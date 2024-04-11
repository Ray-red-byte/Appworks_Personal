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


# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")

log_filename = 'log_file.log'
log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file_hap_url.log'
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


def crawl_and_store_data(website_url, driver, first, urls, begin, lock, page):

    simulate_human_interaction(driver)

    try:

        time.sleep(1)
        driver.get(website_url)
        time.sleep(1)  # Adjust sleep time as needed for the page to load


        count = 1
        next_page = 1
        total = 0
        
        new_urls = {}
        print(len(urls))

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
                
                rent_href = driver.find_element(
                    By.XPATH, xpath).get_attribute('href')

                rent_title = driver.find_element(
                    By.XPATH, xpath).text
                
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

        with lock:
            logger.info(f"Next page : {page}")
            store_url(urls, "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_url.json")
            return urls

    except Exception as e:
        print(f"Error retrieving data: {type(e).__name__} - {e}")
    finally:
        # Close the Chrome driver
        driver.quit()


def main():

    # 好房網

    urls = load_urls_from_json("/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_url.json")
    logger.info(f"Previous number : {len(urls)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"-------------Start Crawler {timestamp_start_stf}-------------")

    begin = True

    for i in range(1, 169):
        driver = webdriver.Chrome(options=options)
        rent_url = f"https://www.rakuya.com.tw/search/rent_search/index?display=list&con=eJyrVkrOLKlUsopWMlCK1VFKySwuyEkE8pVyMotLlHSU8pOyMvNSQPJBIPni1MSi5AwQF6wNKFJanJqcn5IKEjIHqrcAYksgNgQaVwsAQwcbJg&tab=def&sort=21&ds=&page={i}"
        
        lock = threading.Lock()

        first = i == 1

        urls = crawl_and_store_data(rent_url, driver, first, urls, begin, lock, i)

        


    logger.info(f"Total number : {len(urls)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")


if __name__ == "__main__":
    main()
