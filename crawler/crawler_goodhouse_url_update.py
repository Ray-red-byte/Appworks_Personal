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
s3_path = 'personal_project/urls/good_urls/rent_good_url.json'
local_good_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_url.json'

log_filename = 'log_file.log'
log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file_good_url.log'
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


def crawl_and_store_data(website_url, driver):

    #simulate_human_interaction(driver)

    # Click on the "By Post" option
    
    

    try:

        time.sleep(5)
        driver.get(website_url)
        time.sleep(5)  # Adjust sleep time as needed for the page to load

        click_by_post(driver)

        count = 1
        next_page = 1
        total = 0
        json_file = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_url.json"
        urls = load_urls_from_json(json_file)
        
        #click_all(driver)
        timestamp_start = datetime.datetime.now()
        timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"-------------Start Crawler {timestamp_start_stf}-------------")
        logger.info(f"Previous number : {len(urls)}")
        new_urls = {}

        # /html/body/form/div[2]/div[1]/div[2]/div[2]/div/div[3]/div[1]/article[1]/div[1]/h3/a
        # /html/body/form/div[2]/div[1]/div[2]/div[2]/div/div[3]/div[1]/article[2]/div[1]/h3/a
        # //*[@id="SearchContent"]/article[1]/div[1]/h3/a
        # //*[@id="SearchContent"]/article[2]/div[1]/h3/a

        while True:


            try:
                rent_href = driver.find_element(
                    By.XPATH, f'//*[@id="SearchContent"]/article[{count}]/div[1]/h3/a').get_attribute('href')
                
                rent_title = driver.find_element(
                    By.XPATH, f'//*[@id="SearchContent"]/article[{count}]/div[1]/h3/a').text
                
                count += 1
                total += 1

                
                if rent_href not in urls:
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
                    driver.execute_script("arguments[0].scrollIntoView();", next)
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


def click_by_post(driver):
    print(driver.current_url)
    try:
        select_element = driver.find_element(
                        By.XPATH, f"/html/body/form/div[2]/div[1]/div[2]/div[2]/div/div[2]/div[2]/select")
        select_element.click()

        # Initialize Select object
        select = Select(select_element)

        # Choose the desired option by value
        option_value = "ByPost"
        select.select_by_value(option_value)
        

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/form/div[2]/div[1]/div[2]/div[2]/div/div[3]/div[1]/article[1]/div[1]/h3/a")))

        print("Click on the 'By Post' option.")
    except Exception as e:
        print(f"Error clicking on the 'By Post' option: {type(e).__name__} - {e}")


def main():

    # 好房網

    # First download the file from S3
    try:
        download_from_s3(aws_bucket, s3_path, local_good_url_file)
    except Exception as e:
        print("No file on S3")
    
    driver = webdriver.Chrome(options=options)
    
    rent_url = "https://rent.housefun.com.tw/region/%E5%8F%B0%E5%8C%97%E5%B8%82/?cid=0000&purpid=1,2,3,4"
    
    crawl_and_store_data(rent_url, driver)
    
    # Upload the updated file to S3
    wait_input = input("Do you want to upload the updated file and delete local to S3? (y/n): ")
    if wait_input == 'y':
        upload_to_s3(local_good_url_file, aws_bucket, s3_path)
    

if __name__ == "__main__":
    main()
