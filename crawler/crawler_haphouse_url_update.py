from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import datetime
import time
import json
import random
import threading
import logging
import boto3
from botocore.exceptions import NoCredentialsError
import os
import re


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'

# Load environment variables from the specified .env file
load_dotenv(dotenv_path)


# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_path = 'personal_project/urls/happy_urls/rent_hap_url.json'
local_happy_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_url.json'


# logger setting
log_filename = 'log_file.log'
log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file_hap_url.log'
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path, level=logging.INFO)


# Initialize variables
begin = False

# Chromedriver setting
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

        os.remove(local_file)
        print(f"Local file '{local_file}' deleted successfully")
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


def store_url(urls, json_file):

    with open(json_file, 'w') as f:
        json.dump(urls, f, ensure_ascii=False)
    print(f"URL stored successfully.")


def crawl_and_store_data(website_url, driver, first, urls, begin, page):

    

    try:

        time.sleep(2)
        driver.get(website_url)
        time.sleep(3)  # Adjust sleep time as needed for the page to load
        simulate_human_interaction(driver)

        count = 1
        next_page = 1
        total = 0
        
        new_urls = {}

        while True:
            
            # Next page
            if first:
                if count > 11:
                    break
            else:
                if count > 12:
                    break

            try:    
                xpath = f"/html/body/div[8]/div/div[1]/div[4]/div/div[{count}]/div[2]/div/h6/a"
                if first:
                    xpath = f'/html/body/div[8]/div/div[1]/div[4]/div[2]/div[{count}]/div[2]/div/h6/a'
                
                rent_href = driver.find_element(By.XPATH, xpath).get_attribute('href')

                rent_title = driver.find_element(By.XPATH, xpath).text
                
                count += 1
                total += 1

                if rent_href not in urls:
                    new_urls.update({rent_href: rent_title})
                    print("Success", rent_href, rent_title)
                else:
                    print("Already exists", rent_href, rent_title)
                    break

            except Exception as e:
                print("No element found")
                count += 1
                continue

        if len(urls) == 0:
            urls = new_urls
        elif begin:
            urls = {**urls, **new_urls}
        else:
            urls = {**new_urls, **urls}

        logger.info(f"Next page : {page}")
        store_url(urls, "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_url.json")
        return urls

    except Exception as e:
        print(f"Error retrieving data: {type(e).__name__} - {e}")
    finally:
        # Close the Chrome driver
        driver.quit()

def get_total_page(driver, url):

    time.sleep(1)
    driver.get(url)
    time.sleep(1)

    total_page = driver.find_element(By.XPATH,f" /html/body/div[8]/div/div[1]/nav/p").text
    match = re.search(r'(\d+) 頁', total_page)

    if match:
        page_number = int(match.group(1))
        print(page_number)  # Output: 167
    else:
        print("Page number not found.")

    driver.quit()
    return page_number


def main():

    # 樂屋網
    # First download the file from S3
    try:
        download_from_s3(aws_bucket, s3_path, local_happy_url_file)
    except Exception as e:
        print("No file on S3")

    urls = load_urls_from_json("/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_url.json")

    region_url = ["https://www.rakuya.com.tw/search/rent_search/index?display=list&con=eJyrVkrOLKlUsopWMlCK1VFKySwuyEkE8pVyMotLlHSU8pOyMvNSQPJBIPni1MSi5AwQF6wNKFJanJqcn5IKEjIHqrcAYksgNgQaVwsAQwcbJg&tab=def&sort=21&ds=&",
                  "https://www.rakuya.com.tw/search/rent_search/index?display=list&con=eJyrVkrOLKlUsopWMlKK1VFKySwuyEkE8pVyMotLlHSU8pOyMvNSQPJBIPni1MSi5AwQF6wNKFJanJqcn5IKEjIHqrcAYksgNjRQiq0FAEOtGyg&tab=def&sort=21&ds=&"]
    

    logger.info(f"Previous number : {len(urls)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"-------------Start Crawler {timestamp_start_stf}-------------")

    
    
    for region in region_url:
        driver = webdriver.Chrome(options=options)
        page_number = get_total_page(driver, region_url[0] + "page=1")

        for i in range(1, page_number+1):
            driver = webdriver.Chrome(options=options)
            rent_url = region + f"page={i}"

            first = i == 1

            urls = crawl_and_store_data(rent_url, driver, first, urls, begin, i)
            driver.quit()

        


    logger.info(f"Total number : {len(urls)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")
    


    # Upload the updated file to S3
    wait_input = input("Do you want to upload the updated file and delete local to S3? (y/n): ")
    if wait_input == 'y':
        upload_to_s3(local_happy_url_file, aws_bucket, s3_path)

if __name__ == "__main__":
    main()
