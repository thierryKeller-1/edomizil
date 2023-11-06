from playwright.sync_api import sync_playwright
from random import randint
from nested_lookup import nested_lookup
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
import time
import json
import os


load_dotenv()


class EdomizilInitScraper(object):

    def __init__(self, filename:str) -> None:
        print('==> initializing scraper ...')
        self.filename = filename
        self.list_urls = []
        self.details_urls = []
        self.base_url_path = []
        self.base_urls = []
        self.scrool_count = 0
        self.response_count = 0
        self.scrap_finished = False
        self.current_date = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%d_%m_%Y")

        self.base_log = os.getenv("LOG_FOLDER_PATH")
        self.base_static = os.getenv('STATIC_FOLDER_PATH')
        self.base_output = os.getenv("OUTPUT_FOLDER_PATH")
        self.base_config = os.getenv("CONFIG_FOLDER_PATH")
        self.base_dests = os.getenv("DESTS_FOLDER_PATH")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, args=['--start-maximized'])
        self.context = self.browser.new_context(no_viewport=True)
        self.page = self.context.new_page()

    def load_configs(self) -> None:
        print('  ==> loading config files')
        df = pd.read_csv(f'{self.base_config}/destination_ids.csv')
        self.dest_ids = df.to_dict(orient='records')

    def create_logs(self) -> None:
        print(' ==> creating log file')
        log = {'last_index': 0}
        self.logfile_path = f'{self.base_log}/edomizil/{self.current_date}/init/{self.filename}.json'
        if not Path(self.logfile_path).exists():
            os.makedirs(os.path.dirname(self.logfile_path), exist_ok=True)
            with open(self.logfile_path, 'w+') as openfile:
                openfile.write(json.dumps(log, indent=4))

    def create_url(self) -> None:
        print('  ==> creating urls')
        for dest_id in self.dest_ids:
            self.list_urls.append(f"https://www.e-domizil.ch/search/{dest_id['id']}?c=EUR&hl=fr_CH")

    def save_base_url(self) -> None:
        print('  ==> saving base_url')
        self.base_url_path = f"{self.base_static}/edomizil/{self.current_date}/init/{self.filename}.json"
        if not Path(self.base_url_path).exists():
            os.makedirs(os.path.dirname(self.base_url_path), exist_ok=True)
            with open(self.base_url_path, 'w') as openfile:
                openfile.write(json.dumps(self.list_urls, indent=4))

    def load_base_url(self) -> None:
        with open(self.base_url_path, 'r') as openfile:
            self.base_urls = json.loads(openfile.read())
            print(f"{len(self.base_urls)} urls loaded")

    def load_history(self) -> None:
        with open(self.logfile_path, 'r') as openfile:
            self.history = json.loads(openfile.read())

    def get_log(self, key:str) -> object | None:
        try:
            return self.history[key]
        except KeyError:
            return
        
    def set_log(self, key:str, value:object) -> None:
        try:
            self.history[key] = value
            with open(self.logfile_path, 'w') as openfile:
                openfile.write(json.dumps(self.history, indent=4))
        except Exception as e:
            print(f'error => {e}')

    def setup(self) -> None:
        print('  ==> initializing ')
        self.load_configs()
        self.create_url()
        self.save_base_url()
        self.create_logs()
        self.load_history()


    def goto_page(self, url:str) -> None:
        print(f' ==> {url}')
        self.page.on('response', self.intercept_response)
        try:
            self.page.goto(url, timeout=100000)
            self.page.wait_for_timeout(10000)
        except TimeoutError:
            self.page.evaluate("window.location.reload();")
            self.page.wait_for_timeout(10000)

    def close_modal(self):
        try:
            self.page.locator("//button=[@data-test='accept-button']").click()
        except:
            pass

    def get_result_number(self) -> int:
        numbers = int(''.join(filter(str.isdigit, self.page.locator("div.vam.dib.c-gray-dark.w100p").text_content())))
        print(f'  ==> {numbers} results count')
        return numbers


    def load_results(self) -> None:
        self.close_modal()
        results_count = self.get_result_number()
        for i in range(results_count):
            print(f'scroll {i} times')
            self.scrool_count += 1
            self.page.mouse.wheel(0,500)
            if self.scrool_count > 3 and self.response_count == 0:
                time.sleep(5)
                self.page.wait_for_timeout(5000)
                self.scrool_count = 0
            else:
                if self.response_count > 0:
                    self.response_count = 0
                time.sleep(2)
                self.page.wait_for_timeout(2000)

            if self.page.locator("//*[@id='page-search']/div[2]/section/div[2]/div[2]/button").is_visible():
                print('button is visible')
                self.page.click("//*[@id='page-search']/div[2]/section/div[2]/div[2]/button")
            if self.page.locator("//div[@class='text-large']", has_text="Il n'y a plus d'offres disponibles pour cette destination").is_visible():
                time.sleep(1)
                print('page loaded')
                break

    def format_urls(self, response_data:list) -> list:
        base_url = "https://www.e-domizil.ch"
        self.list_urls.clear()
        offers = nested_lookup(key='offers', document=response_data)
        links = []

        for offer in offers:
            links.append(nested_lookup(key='first', document=offer))
        link_cleaned = list(set(nested_lookup(key='link', document=links)))

        for url in link_cleaned:
            self.list_urls.append(base_url+url)

        return self.list_urls

    def intercept_response(self, response) -> None:
        """capture all background requests and save them"""
        response_type = response.request.resource_type
        if response_type == "fetch":
            if 'SearchDetailsFields' in response.url:
                self.response_count += 1
                response_list = []
                response_list.append(response.json())
                dest = self.format_urls(response_list)
                print(f'dests {len(dest)}')
                self.save_reponse(dest)
                
    def save_reponse(self, data:object) -> None:
        print('saving ...')
        response = []
        self.response_path = f"{self.base_dests}/{self.filename}.json"
        if not Path(self.response_path).exists():
            os.makedirs(os.path.dirname(self.response_path), exist_ok=True)
            with open(self.response_path, 'w') as openfile:
                pass

        with open(self.response_path, 'a+') as openfile:
            for item in data:
                openfile.write(f'"{item}",\n')

    def initialize(self) -> None:
        self.setup()
        self.load_base_url()
        for i in range(self.history['last_index'], len(self.base_urls)):
            print(f"{i + 1} / {len(self.base_urls)}")
            self.goto_page(self.base_urls[i])
            self.load_results()
            new_index = self.history['last_index'] + 1
            if i+1 <= len(self.base_urls):
                self.set_log('last_index',new_index)
                self.scrap_finished = True
            else:
                self.save()
                
        if not self.scrap_finished:
            print('something went wrong')

