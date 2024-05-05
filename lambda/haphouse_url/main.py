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


dotenv_path = './.env'

# Load environment variables from the specified .env file
load_dotenv(dotenv_path)


# S3 setting
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_path = os.getenv("S3_HAP_URL_PATH")

# logger setting
log_filename = os.getenv("LOG_FILE_NAME")
log_file_path = os.getenv("LOG_FILE_HAP_PATH")
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path, level=logging.INFO)


# Initialize variables
begin = False

# Chromedriver setting
options = Options()
service = webdriver.ChromeService("/opt/chromedriver")

options.binary_location = '/opt/chrome/chrome'
options.add_argument("--headless=new")
options.add_argument('--no-sandbox')
options.add_argument("--disable-gpu")
options.add_argument("--single-process")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-dev-tools")
options.add_argument("--no-zygote")
options.add_argument("--remote-debugging-port=9222")


def simulate_human_interaction(driver):
    # Introduce random delays between requests
    time.sleep(random.uniform(1, 5))

    # Simulate mouse movements using ActionChains
    actions = ActionChains(driver)
    actions.move_by_offset(random.uniform(
        1, 2), random.uniform(1, 2)).perform()

    # Introduce another random delay
    time.sleep(random.uniform(1, 2))


def upload_to_s3(data, bucket_name, s3_path):
    s3 = boto3.client('s3')
    try:
        json_data = json.dumps(data, ensure_ascii=False)
        s3.put_object(Body=json_data,
                      Bucket=bucket_name, Key=s3_path)
        print("Upload Successful")
        return True
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return False


def download_from_s3(bucket_name, s3_path):
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_path)
        data = response['Body'].read()
        print("Download Successful")
        downloaded_dict = json.loads(data.decode('utf-8'))
        return downloaded_dict
    except NoCredentialsError:
        print("Credentials not available")
        return None
    except Exception as e:
        print(f"Error downloading file from S3: {e}")
        return None


def crawl_and_store_data(website_url, driver, first, urls, begin, page):
    '''
        1. Get in 樂屋網 website
        2. Get total pages to limit the loop
        3. Iterate each page to get the urls, use for loop cause I know the page rules
        4. if urls exist in json file ,         break and stop the whole program
        5. Change page
        6. if no more pages available ,         break and stop the whole program
        6. if encounter problem ,               break and stop the whole program
    '''

    try:

        time.sleep(random.uniform(1, 5))
        driver.get(website_url)
        # Adjust sleep time as needed for the page to load
        time.sleep(random.uniform(1, 5))
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
                try:
                    xpath = f'/html/body/div[8]/div/div[1]/div[4]/div[2]/div[{count}]/div[2]/div/h6/a'
                    rent_href = driver.find_element(
                        By.XPATH, xpath).get_attribute('href')
                    rent_title = driver.find_element(By.XPATH, xpath).text
                except:
                    xpath = f"/html/body/div[8]/div/div[1]/div[4]/div/div[{count}]/div[2]/div/h6/a"
                    rent_href = driver.find_element(
                        By.XPATH, xpath).get_attribute('href')
                    rent_title = driver.find_element(By.XPATH, xpath).text

                count += 1
                total += 1

                if rent_href not in urls:
                    new_urls.update({rent_href: rent_title})
                    print("Success", rent_href, rent_title)
                else:
                    if len(urls) == 0:
                        urls = new_urls
                    elif begin:
                        urls = {**urls, **new_urls}
                    else:
                        urls = {**new_urls, **urls}

                    print("Already exists", rent_href, rent_title)
                    return True, urls

            except Exception as e:

                print("No element found")
                count += 1
                continue

        logger.info(f"Next page : {page}")
        if len(urls) == 0:
            urls = new_urls
        elif begin:
            urls = {**urls, **new_urls}
        else:
            urls = {**new_urls, **urls}

        return True, urls

    except Exception as e:
        print(f"Error retrieving data: {type(e).__name__} - {e}")
        return True, urls

    finally:
        # Close the Chrome driver
        driver.quit()


def get_total_page(driver, url):

    time.sleep(1)
    driver.get(url)
    time.sleep(1)

    total_page = driver.find_element(
        By.XPATH, f" /html/body/div[8]/div/div[1]/nav/p").text
    match = re.search(r'(\d+) 頁', total_page)

    if match:
        page_number = int(match.group(1))
        print(page_number)  # Output: 167
    else:
        print("Page number not found.")

    driver.quit()
    return page_number


def handler(event=None, context=None):

    # 樂屋網
    # First download the file from S3
    try:
        rent_hap_urls = download_from_s3(aws_bucket, s3_path)
        print(rent_hap_urls)
    except Exception as e:
        print(e)
        print("No file on S3")

    region_url = ["https://www.rakuya.com.tw/search/rent_search/index?display=list&con=eJyrVkrOLKlUsopWMlCK1VFKySwuyEkE8pVyMotLlHSU8pOyMvNSQPJBIPni1MSi5AwQF6wNKFJanJqcn5IKEjIHqrcAYksgNgQaVwsAQwcbJg&tab=def&sort=21&ds=&",
                  "https://www.rakuya.com.tw/search/rent_search/index?display=list&con=eJyrVkrOLKlUsopWMlKK1VFKySwuyEkE8pVyMotLlHSU8pOyMvNSQPJBIPni1MSi5AwQF6wNKFJanJqcn5IKEjIHqrcAYksgNjRQiq0FAEOtGyg&tab=def&sort=21&ds=&"]

    logger.info(f"Previous number : {len(rent_hap_urls)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"-------------Start Crawler {timestamp_start_stf}-------------")

    for region in region_url:
        driver = webdriver.Chrome(options=options, service=service)
        page_number = get_total_page(driver, region_url[0] + "page=1")

        for i in range(1, page_number+1):
            driver = webdriver.Chrome(options=options, service=service)
            rent_url = region + f"page={i}"

            first = i == 1

            stop, rent_hap_urls = crawl_and_store_data(
                rent_url, driver, first, rent_hap_urls, begin, i)

            driver.quit()

            if stop:
                print("Stop crawling")
                break

    logger.info(f"Total number : {len(rent_hap_urls)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")

    # Upload the updated file to S3
    upload_to_s3(rent_hap_urls, aws_bucket, s3_path)

    return {"statusCode": 200, "body": "Success"}
