from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import datetime
import pymongo
import time
import json
import random
import logging
import boto3
from botocore.exceptions import NoCredentialsError
import os
import unicodedata
from good_info_mgdb import get_all_mgdb_good_info, get_next_house_id, insert_good_info_to_mgdb


dotenv_path = './.env'

# Load environment variables from the specified .env file
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
s3_good_url_path = os.getenv("S3_GOOD_URL_PATH")
s3_good_info_path = os.getenv("S3_GOOD_INFO_PATH")
s3_uncrawler_url_path = os.getenv("S3_GOOD_UNCRAWLER_URL_PATH")

log_filename = os.getenv("LOG_FILE_NAME")
log_file_path = os.getenv("LOG_FILE_GOOD_PATH")
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


def crawl_each_url(website_url, driver, rent_info):

    try:

        time.sleep(2)
        driver.get(website_url)
        time.sleep(3)  # Adjust sleep time as needed for the page to load

        simulate_human_interaction(driver)

        info_dict = {}
        xpaths = {
            "house_code": "/html/body/form/div[2]/div[2]/section/div[1]/div[2]/h2",
            "price": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[1]/span[2]/span",
            "address": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[4]/address",
            "size": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[5]/span[2]",
            "other_fees": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[7]/span[2]",
            "floor": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[8]/span[2]",
            "layout": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[9]/span[2]",
            "type": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[10]/span[2]",
            "move_date": "/html/body/form/div[2]/div[2]/section/div[2]/div[2]/ul/li[2]/ul/li[11]/span[2]",
            "min_stay": "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody/tr[1]/td[4]"
        }

        for key, xpath in xpaths.items():
            try:
                element = driver.find_element(
                    By.XPATH, xpath)
                text = element.text

                info_dict.update({key: text})

            except Exception as e:
                print("element cannot found", website_url)
                continue

        # img url
        img_url = driver.find_element(
            By.XPATH, "/html/body/form/div[2]/div[2]/section/div[2]/div[3]/ul/li[1]/figure/img").get_attribute("src")
        info_dict.update({"img_url": img_url})

        # Check if info have been extracted
        '''
        if website_url in rent_info:
            print("Already exists", website_url)
            return True, rent_info, "already exists"
        '''

        tbody_element = driver.find_element(
            By.XPATH, "/html/body/form/div[2]/div[2]/section/div[6]/div[2]/table/tbody")
        rows = tbody_element.find_elements(By.TAG_NAME, "tr")
        for id, row in enumerate(rows):

            # Extract the title and value cells (td) in each row
            title_cells = row.find_elements(By.CLASS_NAME, "title")
            value_cells = row.find_elements(By.CLASS_NAME, "value")

            if id == 6 or id == 7:
                value_cells = row.find_elements(By.CLASS_NAME, "values")

                for title_cell, value_cell in zip(title_cells, value_cells):
                    title = unicodedata.normalize(
                        "NFKC", title_cell.text.strip()).replace(' ', '')
                    span_value = value_cell.find_elements(By.TAG_NAME, "span")
                    value_list = []
                    for i in span_value:
                        if "nohas" not in i.get_attribute("class"):
                            value_list.append(i.text)

                info_dict[title] = value_list
                continue

            # Extract and store each key-value pair from the row
            for title_cell, value_cell in zip(title_cells, value_cells):
                title = unicodedata.normalize(
                    "NFKC", title_cell.text.strip()).replace(' ', '')
                value = unicodedata.normalize("NFKC", value_cell.text.strip())

                if title == "最短租期":
                    values_cells = row.find_elements(By.CLASS_NAME, "values")

                    for value_cell in values_cells:
                        value = unicodedata.normalize(
                            "NFKC", value_cell.text.strip())
                        break

                info_dict[title] = value

        # Update rent_info
        new_rent_info = {website_url: info_dict}
        try:
            insert_good_info_to_mgdb(website_url, info_dict)
        except Exception as e:
            print("Cannot insert to mongoDB", website_url)
            return False, rent_info, "cannot insert"

        new_rent_info.update(rent_info)
        rent_info = new_rent_info

        # Success !
        print("Success", website_url)
        print("--------------------------------------------------------------------------")
        return False, rent_info, "success"

    except Exception as e:
        print("Cannot crawl the website", website_url)
        upload_to_s3(website_url, aws_bucket, s3_uncrawler_url_path)
        return False, rent_info, "cannot crawl"


def handler(event=None, context=None):

    print("Received event:", json.dumps(event))

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    print(bucket_name, object_key)

    if object_key != s3_good_url_path:
        return {
            'statusCode': 200,
            'body': json.dumps('Not a good_url file')
        }

    # download good_url from S3
    try:
        rent_good_urls = download_from_s3(bucket_name, object_key)
    except Exception as e:
        print("No url file on S3")
        exit()

    # download good_info from S3
    try:
        rent_good_info = download_from_s3(aws_bucket, s3_good_info_path)
    except Exception as e:
        print("No info file on S3")
        exit()

    try:
        rent_uncrawler_urls = download_from_s3(
            aws_bucket, s3_uncrawler_url_path)
    except Exception as e:
        print("No info file on S3")
        exit()

    # Load from mongo
    all_g_url = get_all_mgdb_good_info()

    all_g_url = [doc["url"] for doc in all_g_url]

    logger.info(f"Previous number : {len(rent_good_info)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"-------------Start Crawler {timestamp_start_stf}-------------")

    # Create and start threads
    count = 1
    server_error = 0
    for rent_good_url, title in rent_good_urls.items():

        if server_error > 5:
            print("Server error more than 5 times, stop crawling. Sorry")
            break

        if rent_good_url in all_g_url:
            print(f"Already exists {rent_good_url} in DB. Skip.")
            break

        driver = webdriver.Chrome(options=options, service=service)
        stop, rent_good_info, response = crawl_each_url(
            rent_good_url, driver, rent_good_info)
        driver.quit()

        if response == "cannot crawl":
            server_error += 1
            continue

        if stop:
            print("Stop crawling, already exists.", title)
            break

        server_error = 0

    print("Crawling finished.")

    logger.info(f"Total number : {len(rent_good_info)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")

    # Upload the updated file to S3
    upload_to_s3(rent_good_info, aws_bucket, s3_good_info_path)

    return {"statusCode": 200, "body": "Crawling finished."}
