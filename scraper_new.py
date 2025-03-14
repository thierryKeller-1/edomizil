from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

from botasaurus.browser import Driver

from dotenv import load_dotenv
import pandas as pd
import json
import os
import sys
import time
import csv

load_dotenv()




class EdomizilScraper(object):

    # def __init__(self,filename:str, dest_name:str, date_start, date_end) -> None:
    def __init__(self,filename:str, dest_name:str, weekscrap:str) -> None:
        
        self.data = []
        self.filename = filename
        self.dest_name = dest_name
        # self.date_start = datetime.strptime(date_start, '%d/%m/%Y').strftime('%Y-%m-%d')
        # self.date_end = datetime.strptime(date_end, '%d/%m/%Y').strftime('%Y-%m-%d')
        self.week_scrap = datetime.strptime(weekscrap, "%d/%m/%Y").strftime("%d_%m_%Y")
        self.cycle_count = 0
        self.max_cycle = 30

        self.base_log = os.environ.get("LOG_FOLDER_PATH")
        self.base_static = os.environ.get('STATIC_FOLDER_PATH')
        self.base_output = os.environ.get("OUTPUT_FOLDER_PATH")
        self.base_config = os.environ.get("CONFIG_FOLDER_PATH")
        self.base_dests = os.environ.get("DESTS_FOLDER_PATH")

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-search-engine-choice-screen')
        self.chrome_options.add_argument('--incognito')
        # self.chrome_options.add_extension(f"{os.environ.get('EXTENSION_PATH')}")
        # self.chrome_options.add_argument('--headless')

        self.firefox_options = webdriver.FirefoxOptions()
        self.firefox_options.add_argument('--disable-gpu')
        self.firefox_options.add_argument('--incognito')
        # self.chrome_options.add_argument('--headless')

        self.use_new_driver()

    def normalize_url(self, url:str, date:str) -> str:
        url_params = list(parse_qs(urlparse(url).query).keys())
        if 'c' in url_params and 'hl' in url_params:
            return url 
        else:
            if 'c' not in url_params:
                url += '&c=EUR'
            if 'hl' not in url_params:
                url += '&hl=fr_CH'
            return url + f"&arrival={date}"

    def get_file_content(self, filepath:str) -> object:
        with open(filepath, 'r') as openfile:
            return json.loads(openfile.read())
        
    def create_files(self) -> None:
        print("  ==> creating logs")
        default_log = {'last_dest': 0}

        self.logfile_path = f"{self.base_log}/edomizil/{self.week_scrap}/start/{self.filename}.json"
        self.dest_path = f"{self.base_dests}/{self.dest_name}.json"
        self.output_path = f"{self.base_output}/edomizil/{self.week_scrap}/results/{self.filename}.csv"

        if not Path(self.output_path).exists():
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            pd.DataFrame(columns=[
                'date_scrap',
                'date_debut',
                'date_fin',
                'price',
                'identifiant',
                'typologie',
                'nom'
            ]).to_csv(self.output_path, index=False)

        if not Path(self.logfile_path).exists():
            os.makedirs(os.path.dirname(self.logfile_path), exist_ok=True)
            with open(self.logfile_path, 'w') as openfile:
                openfile.write(json.dumps(default_log, indent=4))
            
        if not Path(self.dest_path).exists():
            print('destination files not found')
            sys.exit()
            
        
    def load_configs(self) -> None:
        print(' ==> load config files')
        self.history = self.get_file_content(self.logfile_path)
        print(f'history = {self.history}')
        self.destinations = self.get_file_content(self.dest_path)
        print(f'{len(self.destinations)} destinations loaded')

    def set_history(self, key:str, value:object) -> None:
        self.history[key] = value
        with open(self.logfile_path, 'w') as openfile:
            openfile.write(json.dumps(self.history, indent=4))

    def use_new_driver(self) -> None:
        try:
            self.driver.close()
            self.driver = Driver(
                block_images=True,
                arguments=['--start-maximized'])
        except Exception:
            self.driver = Driver(
                block_images=True,
                arguments=['--start-maximized'])
            # self.driver = webdriver.Firefox(options=self.firefox_options)
        
        # self.driver.maximize_window()

    def goto_page(self, url:str) -> str:
        if self.cycle_count >= self.max_cycle:
            print('   ==> max cycle reached')
            self.use_new_driver()
            self.cycle_count = 0
        try:
            # normalized_url = self.normalize_url(url, date)
            # print(f"    => {normalized_url}")
            # test_url = "https://www.e-domizil.ch/rental/c2b595ce31e3499a1d576fdce31290ed?location=5460aeabb3b30&pricetype=totalPrice&duration=7&timestamp=2025-02-10T09%3A52%3A13%2B01%3A00&id=c2b595ce31e3499a1d576fdce31290ed&searchId=1adbef2678a920c0&screen=search&isHotel=0&clickId=VY6G7DWP4N0L7X3S&sT=dateless&prodName=JM&prodSource=Search&c=EUR&hl=fr_CH&arrival=2025-02-22"
            self.driver.get(url)
            #check if the link is unavailable 21 02 2025
            time.sleep(0.5)
            try:
                if self.driver.select('//*[text()="404 Seite nicht gefunden"]'):
                    print("                     ")
                    print("erreur 404, quit the function for the next url")
                    print("                     ")
                    return "next url"
            except:
                pass

            # WebDriverWait(self.driver, 3).until(EC.element_to_be_selected((By.XPATH,'//*[@id="jager-app"]/div/div[5]/div/div[2]/div[2]/button[2]/span/span/span')))
            # self.driver.find_element(By.XPATH,'//*[@id="jager-app"]/div/div[5]/div/div[2]/div[2]/button[2]/span/span/span').click()

            # WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//div[@data-test='rental-sidebar']")))
            self.driver.wait_for_element("div[data-test='rental-sidebar']", wait=30)
            waiting_count = 0
            while "disponibilité en cours de vérification" in self.driver.select("div[data-test='rental-sidebar']").text.lower().strip():
                print("    =>  waiting for data to be loaded")
                if waiting_count >= 5:
                    waiting_count = 0
                    self.use_new_driver()
                    self.goto_page(url)
                time.sleep(1)
                waiting_count += 1
        except Exception as e:
            print(f' erreur ==> {e} ')
            self.driver.close()
            self.use_new_driver()
            self.goto_page(url)
        self.cycle_count += 1
        

    def soupify(self, element:str) -> object:
        return BeautifulSoup(element, 'lxml')

    def page_info_is_valid(self) -> bool:
        print('    =>  verifying page')
        info_container = self.driver.select("div[data-test='rental-sidebar']").html()
        info_cleaned = self.soupify(info_container)
        info_displayed = info_cleaned.find('div', {'data-test':"available-badge"}) and 'bg-success-super-light' in info_cleaned.find('div', {'data-test':"available-badge"})['class']
        if info_displayed: 
            print('    =>  data displayed and available')
        else:
            print('    =>  data not displayed or not available')
        return info_displayed

    def extract_data(self) -> None:
        print('    =>  extracting data')
        time.sleep(3)
        soupe = self.soupify(self.driver.page_source)
        info_container = soupe.find("div", {"data-test":'rental-sidebar'})
        identifiant = ""
        typologie = ""
        try:
            identifiant = info_container.find('div', {'class':"bdtlrsm bdtrrsm bgc-gray-extra-light c-gray-dark pv4 tac text-small"}).find_all('span')[-1].text.strip()
        except:
            identifiant = soupe.find("div", "c-gray-extra-dark fwb").text.strip()
        try:
            typologie = info_container.find('div', {'class':"text-overflow text-small txt-strong"}).text.strip()
        except:
            typologie = soupe.find('span', {'class':"text-medium fwb db cols>m4"}).text.strip()
        # input('pause')
        #selecteur ancien affichage de nom:
        try:
            nom = soupe.find('div', {'data-test':"rental-sidebar"}).find_all('div', {'class':'text-overflow'})[1].text.strip().replace(',', ' -')
            print("anienne affichage")
            # input("pause")
        except:
            try:
                nom = soupe.find('article', {'class':"df db-print"}).find('span', {'class':'c-gray-dark text-medium'}).text.strip().replace(',', ' -')
                print("nouvelle afichage")
                # nom = soupe.find('article', {'class':"df db-print"}).find('h1', {'role':'button'}).text.strip().replace(',', ' -')
            except:
                print("pas de bon selecteur nom")
                input("pause")
                # nom = soupe.find('article', {'class':"df db-print"}).find('h1', {'class':'subheading-medium mv0'}).text.strip().replace(',', ' -')
        # input("price")
        price = info_container.find('div', {'data-test':"total-price"}).find('span', {'class':'wsnw'}).text.replace('\u202f', '').replace(' ', '')
        if price[0] == "€":
            price = price.replace('€', '').replace(',', '')
        else:
            price = price.replace('€', '').replace('.', '').replace(',', '.')
        arrival_date = datetime.strptime(parse_qs(urlparse(self.driver.current_url).query)['arrival'][0], "%Y-%m-%d").strftime("%d/%m/%Y")
        data = {
            'date_scrap': datetime.now().strftime("%d/%m/%Y"),
            'date_debut': arrival_date,
            'date_fin': (datetime.strptime(arrival_date, "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y"),
            'price': price,
            'identifiant': identifiant,
            'typologie': typologie,
            'nom': nom
        }

        print(data)
        self.data.append(data)

    def save_data(self) -> None:
        print('    =>  saving data')
        field_names = [
            'date_scrap',
            'date_debut',
            'date_fin',
            'price',
            'identifiant',
            'typologie',
            'nom'
        ]
        with open(self.output_path, 'a', newline='', encoding='utf-8') as f_object:
            dictwriter_object = csv.DictWriter(f_object, fieldnames=field_names)
            dictwriter_object.writerows(self.data)
        self.data.clear()

    def start(self) -> None:
        self.create_files()
        self.load_configs()
        for k in range(self.history['last_dest'], len(self.destinations)):
            print(f" ==> {k + 1} / {len(self.destinations)} destinations")
            # dates = pd.bdate_range(
            #                         start=self.date_start, 
            #                         end=self.date_end, 
            #                         freq='C', 
            #                         weekmask='Sat'
            #                     ).strftime('%Y-%m-%d').to_list()
            # for j in range(len(dates)):
            #     print(f'    => week {j + 1} / {len(dates)} : {datetime.strptime(dates[j], "%Y-%m-%d").strftime("%d-%m-%Y")} => {(datetime.strptime(dates[j], "%Y-%m-%d") + timedelta(days=7)).strftime("%d-%m-%Y")}')
            continue_or_break = self.goto_page(self.destinations[k])
            #break this boucle for next_url 21 02 2025
            if continue_or_break == "next url":
            # input(f"{continue_or_break}")
                print("         ")
                print("next url now")
                print("         ")
                time.sleep(2.5)
                continue
            if self.page_info_is_valid():
                self.extract_data()
                self.save_data()
            if k <= len(self.destinations):
                new_index = k + 1 
                self.set_history('last_dest', new_index)
            print('scrap finished !')
