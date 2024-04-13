from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import datetime
import time
import json
import random
import threading
import logging
import boto3
from botocore.exceptions import NoCredentialsError
import os
from bs4 import BeautifulSoup


# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")

log_filename = 'log_file.log'
log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file.log'
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


def crawl_and_store_data(website_url, driver):

    

    try:

        time.sleep(5)
        driver.get(website_url)
        time.sleep(5)  # Adjust sleep time as needed for the page to load
        simulate_human_interaction(driver)
        print(driver.current_url)

        
        
        #//*[@id="vue-container"]/section/ul[1]/li[2]/div[2]/h3/a
        rent_href = driver.find_element(
                        By.XPATH, f'/html/body/div[1]/div/div/div[1]/div[4]/div[2]/div[1]/div[1]/div[1]/div[2]/a')
        print(rent_href)

    except Exception as e:
        print(f"Error retrieving data: {type(e).__name__} - {e}")
    finally:
        # Close the Chrome driver
        driver.quit()




def main():

    # Testing
    

    driver = webdriver.Chrome(options=options)
    rent_url = "https://www.dd-room.com/search?category=house&city=%E8%87%BA%E5%8C%97%E5%B8%82&order=recommend&sort=desc&page=1&per_page=20"
    
    crawl_and_store_data(rent_url, driver)


if __name__ == "__main__":
    main()
