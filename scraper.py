from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import json
import os
import sys
import time
import csv

load_dotenv()

class EdomizilScraper(object):

    def __init__(self,filename:str, dest_name:str, date_start:str, date_end:str) -> None:
        
        self.data = []
        self.filename = filename
        self.dest_name = dest_name
        self.date_start = datetime.strptime(date_start, '%d/%m/%Y').strftime('%Y-%m-%d')
        self.date_end = datetime.strptime(date_end, '%d/%m/%Y').strftime('%Y-%m-%d')
        self.week_scrap = datetime.strptime(date_start, "%d/%m/%Y").strftime("%d_%m_%Y")
        self.cycle_count = 0
        self.max_cycle = 30

        self.base_log = os.getenv("LOG_FOLDER_PATH")
        self.base_static = os.getenv('STATIC_FOLDER_PATH')
        self.base_output = os.getenv("OUTPUT_FOLDER_PATH")
        self.base_config = os.getenv("CONFIG_FOLDER_PATH")
        self.base_dests = os.getenv("DESTS_FOLDER_PATH")

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--incognito')
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
        self.dest_path = f"{self.base_dests}/{self.dest_name}"
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
            self.driver.quit()
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.maximize_window()
        except Exception:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.maximize_window()

    def goto_page(self, url:str, date:str) -> None:
        print(f"    => {url}")
        if self.cycle_count >= self.max_cycle:
            print('   ==> max cycle reached')
            self.use_new_driver()
            self.cycle_count = 0
        try:
            normalized_url = self.normalize_url(url, date)
            self.driver.get(normalized_url)
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//div[@data-test='rental-sidebar']")))
            while "disponibilité en cours de vérification" in self.driver.find_element(By.XPATH, "//div[@data-test='rental-sidebar']").text.lower().strip():
                print("    =>  waiting for data to be loaded")
                time.sleep(1)
        except TimeoutException:
            print('     ===> TimeoutException')
            self.use_new_driver()
            self.goto_page(url, date)
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//div[@data-test='rental-sidebar']")))
        self.cycle_count += 1
        

    def soupify(self, element:str) -> object:
        return BeautifulSoup(element, 'lxml')

    def page_info_is_valid(self) -> bool:
        print('    =>  verifying page')
        info_container = self.driver.find_element(By.XPATH, "//div[@data-test='rental-sidebar']").get_attribute('innerHTML')
        info_cleaned = self.soupify(info_container)
        info_displayed = info_cleaned.find('div', {'data-test':"available-badge"}) and 'bg-success-super-light' in info_cleaned.find('div', {'data-test':"available-badge"})['class']
        if info_displayed: 
            print('    =>  data displayed and available')
        else:
            print('    =>  data not displayed or not available')
        return info_displayed

    def extract_data(self) -> None:
        print('    =>  extracting data')
        info_container = self.driver.find_element(By.XPATH, "//div[@data-test='rental-sidebar']").get_attribute('innerHTML')
        info_cleaned = self.soupify(info_container)
        identifiant = info_cleaned.find('div', {'class':"bdtlrsm bdtrrsm bgc-gray-extra-light c-gray-dark pv4 tac text-small"}).find_all('span')[-1].text.strip()
        typologie = info_cleaned.find('div', {'class':"text-overflow text-small txt-strong"}).text.strip()
        nom = info_cleaned.find('div', {'class':"rows>m4"}).text.strip().split('personnes')[-1].replace(',', ' -')
        price = int(''.join(filter(str.isdigit, info_cleaned.find('div', {'class':"heading-medium"}).text.replace(',', '').strip()[1:])))
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
            dates = pd.bdate_range(
                                    start=self.date_start, 
                                    end=self.date_end, 
                                    freq='C', 
                                    weekmask='Sat'
                                ).strftime('%Y-%m-%d').to_list()
            for j in range(len(dates)):
                print(f'    => week {j + 1} / {len(dates)} : {datetime.strptime(dates[j], "%Y-%m-%d").strftime("%d-%m-%Y")} => {(datetime.strptime(dates[j], "%Y-%m-%d") + timedelta(days=7)).strftime("%d-%m-%Y")}')
                self.goto_page(self.destinations[k], dates[j])
                if self.page_info_is_valid():
                    self.extract_data()
                    self.save_data()
            if k <= len(self.destinations):
                new_index = k + 1 
                self.set_history('last_dest', new_index)
        print('scrap finished !')
