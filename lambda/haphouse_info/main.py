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
import logging
import boto3
from botocore.exceptions import NoCredentialsError
import os
import pymongo
from hap_info_mgdb import get_all_mgdb_info, get_next_house_id, insert_hap_info_to_mgdb


dotenv_path = './.env'
load_dotenv(dotenv_path)

# Mongo Setting
# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)

# Select a database and collection
db = client["personal_project"]
collection = db["house"]

# S3 setting
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_hap_info_path = os.getenv("S3_HAP_INFO_PATH")
s3_hap_url_path = os.getenv("S3_HAP_URL_PATH")
s3_uncrawler_url_path = os.getenv("S3_HAP_UNCRAWLER_URL_PATH")

log_filename = os.getenv("LOG_FILE_NAME")
log_file_path = os.getenv("LOG_FILE_HAP_PATH")
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path, level=logging.INFO)


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
    time.sleep(random.uniform(1, 5))


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


def crawl_each_url(website_url, title, rent_info, driver, uncrawler_hap_url_dict):

    try:

        time.sleep(random.uniform(1, 5))
        driver.get(website_url)
        # Adjust sleep time as needed for the page to load
        time.sleep(random.uniform(1, 5))

        simulate_human_interaction(driver)

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

        # img url
        img_url = driver.find_element(
            By.XPATH, "/html/body/div[8]/div[2]/div[1]/div[1]/div/div[1]/div/div/div[1]/img").get_attribute("src")
        info_dict.update({"img_url": img_url})

        # Check if info have been extracted
        '''
        if website_url in rent_info:
            print("Already exists", website_url)
            return True, rent_info, "success"
        '''

        parent_element = driver.find_element(By.CLASS_NAME, "block__info-sub")

        # Iterate through each section (div) containing sub-information
        sub_info_divs = parent_element.find_elements(
            By.CLASS_NAME, "list__info-sub")
        for sub_info_div in sub_info_divs:

            # Extract the list items (li) within the section
            list_items = sub_info_div.find_elements(By.TAG_NAME, "li")

            # Extract and store each key-value pair within the section
            for list_item in list_items:
                label_element = list_item.find_element(
                    By.CLASS_NAME, "list__label")
                label_text = label_element.text.strip()

                content_element = list_item.find_element(
                    By.CLASS_NAME, "list__content")
                content_text = content_element.text.strip()

                # Handle cases where the content contains multiple items (e.g., equipment)
                if content_element.find_elements(By.TAG_NAME, "b"):
                    content_items = [
                        b.text.strip() for b in content_element.find_elements(By.TAG_NAME, "b")]
                    info_dict[label_text] = content_items
                else:
                    if label_text:
                        info_dict[label_text] = content_text
                    else:
                        info_dict["坪數"] = content_text

        # Update rent_info
        new_rent_info = {website_url: info_dict}
        try:
            insert_hap_info_to_mgdb(website_url, info_dict)
        except Exception as e:
            print("Cannot insert to mongoDB", website_url)
            return False, rent_info, uncrawler_hap_url_dict, "cannot insert"

        new_rent_info.update(rent_info)
        rent_info = new_rent_info

        print("--------------------------------------------------------------------------")
        return False, rent_info, uncrawler_hap_url_dict, "success"

    except Exception as e:
        print("Cannot crawl the website", website_url)
        uncrawler_hap_url_dict.update({website_url: title})
        return False, rent_info, uncrawler_hap_url_dict, "cannot crawl"


def handler(event=None, context=None):

    # ----------------------------------------------------------------樂屋網----------------------------------------------------------------
    print("Received event:", json.dumps(event))

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    print(bucket_name, object_key)

    if object_key != s3_hap_url_path:
        return {
            'statusCode': 200,
            'body': json.dumps('Not a hap_url file')
        }

    try:
        rent_hap_urls = download_from_s3(
            aws_bucket, s3_hap_url_path)
    except Exception as e:
        print(e)
        print("No url file on S3")

    try:
        rent_hap_info = download_from_s3(aws_bucket, s3_hap_info_path)
    except Exception as e:
        print(e)
        print("No info file on S3")

    try:
        uncrawler_hap_url_dict = download_from_s3(
            aws_bucket, s3_uncrawler_url_path)
    except Exception as e:
        uncrawler_hap_url_dict = {}
        print("No info file on S3")

    # Load from mongo
    all_h_url = get_all_mgdb_info()
    all_h_url = [doc["url"] for doc in all_h_url]

    # Log start time
    logger.info(f"Previous number : {len(all_h_url)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"---------- ---Start Crawler {timestamp_start_stf}-------------")

    # Create and start threads
    server_error = 0
    for rent_hap_url, title in rent_hap_urls.items():

        if server_error > 5:
            print("Server error more than 5 times, stop crawling. Sorry")
            break

        if rent_hap_url in all_h_url:
            print("Already exists in DB. Skip.")
            break

        driver = webdriver.Chrome(service=service, options=options)
        stop, rent_hap_info, uncrawler_hap_url_dict, response = crawl_each_url(
            rent_hap_url, title, rent_hap_info, driver, uncrawler_hap_url_dict)
        driver.quit()

        if stop:
            print("Stop crawling, already exists.", title)
            break

        if response == "cannot crawl":
            server_error += 1
            continue

    # Log end time
    logger.info(f"Total number : {len(rent_hap_info)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")

    # Upload the updated file to S3
    upload_to_s3(rent_hap_info, aws_bucket, s3_hap_info_path)
    upload_to_s3(uncrawler_hap_url_dict, aws_bucket, s3_uncrawler_url_path)

    return {"status": "success"}
