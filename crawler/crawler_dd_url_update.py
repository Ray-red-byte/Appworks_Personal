from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
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


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'

# Load environment variables from the specified .env file
load_dotenv(dotenv_path)


# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_path = 'personal_project/urls/dd_urls/rent_dd_url.json'
local_good_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_dd_url.json'

log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file_dd_url.log'
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


def crawl_and_store_data(website_url, page, driver):

    

    try:

        time.sleep(random.uniform(1, 5))
        driver.get(website_url + page)
        time.sleep(random.uniform(1, 5))  # Adjust sleep time as needed for the page to load

        simulate_human_interaction(driver)

        # Click on the "By Post" option
        # click_by_post(driver)

        count = 1
        next_page = 1
        total = 0
        json_file = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_dd_url.json"
        urls = load_urls_from_json(json_file)
        
        #click_all(driver)
        timestamp_start = datetime.datetime.now()
        timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"-------------Start Crawler {timestamp_start_stf}-------------")
        logger.info(f"Previous number : {len(urls)}")
        new_urls = {}

        refresh = 0
        while True:
            
            try:
                rent_href = driver.find_element(
                    By.XPATH, f'//html/body/div[1]/div/div/div[1]/div[4]/div[2]/div[1]/div[1]/div[{count}]/div[2]/a').get_attribute('href')
                
                rent_title = driver.find_element(
                    By.XPATH, f'/html/body/div[1]/div/div/div[1]/div[4]/div[2]/div[1]/div[1]/div[{count}]/div[2]/a').text
                
                count += 1
                total += 1

                
                if rent_href not in urls:
                    new_urls.update({rent_href: rent_title})
                    print("Success", rent_href, rent_title)
                    refresh = 0
                else:
                    print("Already exists", rent_href, rent_title)
                    refresh = 0
                    break

            except Exception as e:
                logger.info(f"Next page : {next_page}")

                next_page += 1
                
                try:
                    if refresh > 5:
                        break

                    time.sleep(random.uniform(1, 5))
                    driver.execute_script(f"window.location='{website_url + str(next_page)}'")
                    print("Page refreshed.")

                    refresh += 1

                    time.sleep(random.uniform(1, 5))
                except Exception as e:
                    print(e)
                    print("No more pages available. Exiting loop.")
                    break

                
                count = 1

        if len(urls) == 0:
            updated_urls = new_urls
        else:
            updated_urls = {**new_urls, **urls}

        logger.info(f"Total number : {len(updated_urls)}")
        timestamp_end = datetime.datetime.now()
        timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"-------------Time consume {timestamp_end - timestamp_start}-------------")
        logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")

        store_url(updated_urls, json_file)


    except Exception as e:
        print(f"Error retrieving data: {type(e).__name__} - {e}")
    finally:
        # Close the Chrome driver
        driver.quit()




def main():

    # 租租網

    # First download the file from S3
    
    try:
        download_from_s3(aws_bucket, s3_path, local_good_url_file)
    except Exception as e:
        print("No file on S3")
    
    driver = webdriver.Chrome(options=options)
    
    # 台北市
    rent_url = "https://www.dd-room.com/search?category=house&order=recommend&sort=desc&page="
    
    first_page = "1"
    crawl_and_store_data(rent_url, first_page, driver)
    
    
    # Upload the updated file to S3
    wait_input = input("Do you want to upload the updated file and delete local to S3? (y/n): ")
    if wait_input == 'y':
        upload_to_s3(local_good_url_file, aws_bucket, s3_path)
    

if __name__ == "__main__":
    main()
