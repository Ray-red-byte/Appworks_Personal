from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.edge.service import Service
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


dotenv_path = './.env'

# Load environment variables from the specified .env file
load_dotenv(dotenv_path)


# S3 setting
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_path = 'personal_project/urls/good_urls/rent_good_url.json'

log_filename = 'log_file.log'
log_file_path = './log/log_file_good_url.log'
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
        1, 5), random.uniform(1, 5)).perform()

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


def crawl_and_store_data(website_url, driver, all_g_url):
    '''
        1. Get in 好房網 website
        2. Click on the "By Post" option, to get the latest post
        3. if urls exist in json file , break and stop the whole program
        4. if urls not exist in json file , store the urls in json file
        5. Change page
        6. if no more pages available , break and stop
    '''

    try:

        time.sleep(random.uniform(1, 5))
        driver.get(website_url)
        time.sleep(random.uniform(1, 5))

        simulate_human_interaction(driver)

        # Click on the "By Post" option
        click_by_post(driver)

        count = 1
        next_page = 1
        total = 0
        # urls = load_urls_from_json(json_file)

        # click_all(driver)
        timestamp_start = datetime.datetime.now()
        timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(
            f"-------------Start Crawler {timestamp_start_stf}-------------")
        logger.info(f"Previous number : {len(all_g_url)}")
        new_urls = {}

        while True:

            try:
                rent_href = driver.find_element(
                    By.XPATH, f'//*[@id="SearchContent"]/article[{count}]/div[1]/h3/a').get_attribute('href')

                rent_title = driver.find_element(
                    By.XPATH, f'//*[@id="SearchContent"]/article[{count}]/div[1]/h3/a').text

                count += 1
                total += 1

                if rent_href not in all_g_url:
                    new_urls.update({rent_href: rent_title})
                    print("Success", rent_href, rent_title)
                else:
                    print("Already exists", rent_href, rent_title)
                    break

            except Exception as e:

                logger.info(f"Next page : {next_page}")

                next_page += 1

                try:

                    next = driver.find_element(
                        By.XPATH, f'/html/body/form/div[2]/div[1]/div[2]/div[2]/div/div[3]/div[2]/ul/li[13]/a')
                    driver.execute_script(
                        "arguments[0].scrollIntoView();", next)
                    next.click()

                    # Wait for the page to refresh
                    WebDriverWait(driver, 10).until(EC.staleness_of(next))
                    print("Page refreshed.")

                    time.sleep(1)
                except Exception as e:
                    print(e)
                    print("No more pages available. Exiting loop.")
                    break

                count = 1

        if len(all_g_url) == 0:
            updated_urls = new_urls
        else:
            updated_urls = {**new_urls, **all_g_url}

        logger.info(f"Total number : {len(updated_urls)}")
        timestamp_end = datetime.datetime.now()
        timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(
            f"-------------Time consume {timestamp_end - timestamp_start}-------------")
        logger.info(
            f"-------------End Crawler {timestamp_end_stf}-------------")

        return updated_urls

    except Exception as e:
        print(f"Error retrieving data: {type(e).__name__} - {e}")
    finally:
        # Close the Chrome driver
        driver.quit()


def click_by_post(driver):
    try:
        select_element = driver.find_element(
            By.XPATH, f"/html/body/form/div[2]/div[1]/div[2]/div[2]/div/div[2]/div[2]/select")
        select_element.click()

        # Initialize Select object
        select = Select(select_element)

        # Choose the desired option by value
        option_value = "ByPost"
        select.select_by_value(option_value)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "/html/body/form/div[2]/div[1]/div[2]/div[2]/div/div[3]/div[1]/article[1]/div[1]/h3/a")))

        print("Click on the 'By Post' option.")
    except Exception as e:
        print(
            f"Error clicking on the 'By Post' option: {type(e).__name__} - {e}")


def handler(event=None, context=None):

    # 好房網
    # First download the file from S3
    try:
        all_g_url = download_from_s3(aws_bucket, s3_path)
    except Exception as e:
        print(e)
        print("No file on S3")

    print(all_g_url)

    driver = webdriver.Chrome(options=options, service=service)
    rent_url = "https://rent.housefun.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82/?cid=0000&purpid=1,2,3,4"

    update_urls = crawl_and_store_data(rent_url, driver, all_g_url)
    upload_to_s3(update_urls, aws_bucket, s3_path)

    return {"success": True}
