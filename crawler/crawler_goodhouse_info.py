from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor
import datetime
import base64
import time
import json
import random
import requests
import threading
import logging
from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import NoCredentialsError
import os


# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")

log_filename = 'log_file.log'
log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file_good_info.log'
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path, level=logging.INFO)



options = Options()
options.add_argument('--headless')  # run in headless mode.
options.add_argument('--disable-gpu')
options.add_argument('start-maximized')
options.add_argument('disable-infobars')
options.add_argument('--disable-extensions')


def simulate_human_interaction(driver):
    # Introduce random delays between requests
    time.sleep(random.uniform(1, 5))

    # Simulate mouse movements using ActionChains
    actions = ActionChains(driver)
    actions.move_by_offset(random.uniform(
        1, 5), random.uniform(1, 5)).perform()

    # Introduce another random delay
    time.sleep(random.uniform(1, 5))

def upload_to_s3(local_file, bucket_name, s3_path):
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key)
    try:
        s3.upload_file(local_file, bucket_name, s3_path)
        print("Upload Successful")
        return True

    except FileNotFoundError:
        print("The file was not found")
        return False

    except NoCredentialsError:
        print("Credentials not available")
        return False


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def load_urls_from_json(json_file):
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(e)
        return {}


def store_url(urls, json_file):

    with open(json_file, 'w') as f:
        json.dump(urls, f, ensure_ascii=False)
    print(f"URL stored successfully.")


def crawl_each_url(website_url, driver):

    simulate_human_interaction(driver)

    try:

        time.sleep(5)
        driver.get(website_url)
        time.sleep(5)  # Adjust sleep time as needed for the page to load

        # 房屋編號 ：/html/body/form/div[2]/div[2]/section/div[1]/div[2]/h2
        # 租金：/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[1]/span[2]/span
        # 地址：/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[4]/address/text()
        # 評數：/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[5]/span[2]
        # 其他費用：/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[7]/span[2]
        # 樓層 ：/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[8]/span[2]
        # 格局 ：/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[9]/span[2]
        # 型太 : /html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[10]/span[2]
        # 嵌入日期 ：/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[11]/span[2]
        # 屋齡 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[1]/td[2]
        # 最短租期 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[1]/td[4]
        # 性別 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[2]/td[4]
        # 與房東同住 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[2]/td[6]
        # 開火 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[3]/td[2]
        # 寵物 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[3]/td[4]
        # 車位 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[4]/td[6]
        # 頂樓加蓋 ：/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[5]/td[2]

        # Define XPath expressions
        xpaths = {
            "house_code": "/html/body/form/div[2]/div[2]/section/div[1]/div[2]/h2",
            "rent": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[1]/span[2]/span",
            "address": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[4]/address",
            "size": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[5]/span[2]",
            "other_fees": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[7]/span[2]",
            "floor": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[8]/span[2]",
            "layout": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[9]/span[2]",
            "type": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[10]/span[2]",
            "move_date": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[11]/span[2]",
            "house_age": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[1]/td[2]",
            "min_stay": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[1]/td[4]",
            "gender": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[2]/td[4]",
            "live_with_landlord": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[2]/td[6]",
            "cook": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[3]/td[2]",
            "pet": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[3]/td[4]",
            "park": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[4]/td[6]",
            "roof_top": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[5]/td[2]"
        }

        # Extract text for each XPath expression
        for key, xpath in xpaths.items():
            element = driver.find_element(
                    By.XPATH, xpath)
            text = element.text
            print(f"{key}: {text}")
        print("--------------------------------------------------------------------------")

    except Exception as e:
        print(e)


def main():

    # Testing
    json_file = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good.json"
    rent_urls = load_urls_from_json(json_file)
    driver = webdriver.Chrome(options=options)

    #crawl_each_url("https://rent.housefun.com.tw/rent/house/1347823/", driver)

    threads = []
    
    # Create and start threads
    for rent_url, title in rent_urls.items():
        driver = webdriver.Chrome(options=options)
        crawl_each_url(rent_url, driver)
    
    




if __name__ == "__main__":
    main()
