from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
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

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'

# Load environment variables from the specified .env file
load_dotenv(dotenv_path)

# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_hap_info_path = 'personal_project/house_detail/happy_detail/rent_hap_info.json'
s3_hap_url_path = 'personal_project/urls/happy_urls/rent_hap_url.json'
local_hap_info_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_info.json'
local_hap_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_url.json'


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
        1, 2), random.uniform(1, 2)).perform()

    # Introduce another random delay
    time.sleep(random.uniform(1, 2))

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
    
def download_from_s3(bucket_name, s3_path, local_file):
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key)
    try:
        s3.download_file(bucket_name, s3_path, local_file)
        print("Download Successful")
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


def store_url(infos, json_file):

    with open(json_file, 'w') as f:
        json.dump(infos, f, ensure_ascii=False)
    print(f"URL stored successfully.")


def crawl_each_url(website_url, rent_info, driver):

    #simulate_human_interaction(driver)

    try:

        time.sleep(1)
        driver.get(website_url)
        time.sleep(1)  # Adjust sleep time as needed for the page to load

        # 房屋編號 ：/html/body/div[8]/div[1]/div[2]/h2/span[2]
        # 租金：/html/body/div[8]/div[2]/div[2]/div[1]/div/span
        # 地址：/html/body/div[8]/div[1]/div[2]/h1
        # 評數：/html/body/div[8]/div[2]/div[2]/div[1]/ul/li[2]
        # 其他費用：
        # 樓層 ：/html/body/div[8]/div[2]/div[1]/div[2]/div[1]/ul/li[3]/span[2]
        # 格局 ：/html/body/div[8]/div[2]/div[2]/div[1]/ul/li[1]
        # 型太 : /html/body/div[8]/div[2]/div[1]/div[2]/div[1]/ul/li[1]/span[2]
        # 嵌入日期 ：
        # 屋齡 ： /html/body/div[8]/div[2]/div[1]/div[2]/div[1]/ul/li[5]/span[2]
        # 最短租期 ：/html/body/div[8]/div[2]/div[1]/div[2]/div[3]/ul/li[1]/span[2]
        # 性別 ：/html/body/div[8]/div[2]/div[1]/div[2]/div[3]/ul/li[4]/span[2]
        # 與房東同住 ： /html/body/div[8]/div[2]/div[1]/div[2]/div[3]/ul/li[7]/span[2]
        # 開火 ：/html/body/div[8]/div[2]/div[1]/div[2]/div[3]/ul/li[2]/span[2]
        # 寵物 ：/html/body/div[8]/div[2]/div[1]/div[2]/div[3]/ul/li[3]/span[2]
        # 車位 ：/html/body/div[8]/div[2]/div[1]/div[2]/div[4]/ul/li/span[2]
        # 頂樓加蓋 ：
        
        # "roof_top": "No define"
        # "other_fees": "No define",

        # Define XPath expressions
        xpaths = {
            "house_code": "/html/body/div[8]/div[1]/div[2]/h2/span[2]",
            "price": "/html/body/div[8]/div[2]/div[2]/div[1]/div/span",
            "address": "/html/body/div[8]/div[1]/div[2]/h1"
        }

        # Basic information
        info_dict = {}
        for key, xpath in xpaths.items():
            try:
                element = driver.find_element(
                        By.XPATH, xpath)
                text = element.text
                info_dict.update({key: text})

            except Exception as e:
                print("element cannot found")
                continue

        # Check if info have been extracted
        if website_url in rent_info:
            print("Already exists", website_url)
            return True, rent_info

        parent_element = driver.find_element(By.CLASS_NAME, "block__info-sub")
        

        # Iterate through each section (div) containing sub-information
        sub_info_divs = parent_element.find_elements(By.CLASS_NAME, "list__info-sub")
        for sub_info_div in sub_info_divs:
            
            # Extract the list items (li) within the section
            list_items = sub_info_div.find_elements(By.TAG_NAME, "li")
            
            # Extract and store each key-value pair within the section
            for list_item in list_items:
                label_element = list_item.find_element(By.CLASS_NAME, "list__label")
                label_text = label_element.text.strip()
                
                content_element = list_item.find_element(By.CLASS_NAME, "list__content")
                content_text = content_element.text.strip()
                
                # Handle cases where the content contains multiple items (e.g., equipment)
                if content_element.find_elements(By.TAG_NAME, "b"):
                    content_items = [b.text.strip() for b in content_element.find_elements(By.TAG_NAME, "b")]
                    info_dict[label_text] = content_items
                else:
                    if label_text:
                        info_dict[label_text] = content_text
                    else:
                        info_dict["坪數"] = content_text
            
        # Update rent_info
        rent_info.update({website_url: info_dict})
        
        print("--------------------------------------------------------------------------")
        return False, rent_info

    except Exception as e:
        print(e)
        print("Cannot crawl the website", website_url)
        return False, rent_info


def main():

    # 樂屋網
    # download hap_url from S3
    try:
        download_from_s3(aws_bucket, s3_hap_url_path, local_hap_url_file)
    except Exception as e:
        print(e)
        print("No url file on S3")
        exit()


    # download hap_info from S3
    try:
        download_from_s3(aws_bucket, s3_hap_info_path, local_hap_info_file)
    except Exception as e:
        print(e)
        print("No info file on S3")

    # Download the url and info file
    rent_hap_urls = load_urls_from_json(local_hap_url_file)
    rent_hap_info = load_urls_from_json(local_hap_info_file)


    logger.info(f"Previous number : {len(rent_hap_info)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"-------------Start Crawler {timestamp_start_stf}-------------")

    # Create and start threads
    for rent_hap_url, title in rent_hap_urls.items():
        driver = webdriver.Chrome(options=options)
        stop, rent_info = crawl_each_url(rent_hap_url, rent_hap_info, driver)
        driver.quit()

        if stop:
            print("Stop crawling, already exists.")
            break

        store_url(rent_info, local_hap_info_file)

    logger.info(f"Total number : {len(rent_hap_info)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")

    # Upload the updated file to S3
    wait_input = input("Do you want to upload the updated info file and delete local to S3? (y/n): ")
    if wait_input == 'y':
        upload_to_s3(local_hap_info_file, aws_bucket, s3_hap_info_path)

    wait_input = input("Do you want to upload the updated url file and delete local to S3? (y/n): ")
    if wait_input == 'y':
        upload_to_s3(local_hap_url_file, aws_bucket, s3_hap_url_path)

if __name__ == "__main__":
    main()
