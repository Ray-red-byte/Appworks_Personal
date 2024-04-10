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

    simulate_human_interaction(driver)

    with threading.Lock():
        try:

            time.sleep(5)
            driver.get(website_url)
            time.sleep(5)  # Adjust sleep time as needed for the page to load


            count = 1
            next_page = 1
            total = 0
            json_file = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_url.json"
            urls = load_urls_from_json(json_file)
            logger.info(f"Previous number : {len(urls)}")
            timestamp_start = datetime.datetime.now()
            timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"-------------Start Crawler {timestamp_start_stf}-------------")
            new_urls = {}
            condition = True

            while condition:

                try:
                    rent_href = driver.find_element(
                        By.XPATH, f'//*[@id="rent-list-app"]/div/div[3]/div[1]/section[3]/div/section[{count}]/a').get_attribute('href')

                    rent_title = driver.find_element(
                        By.XPATH, f'//*[@id="rent-list-app"]/div/div[3]/div[1]/section[3]/div/section[{count}]/a/div[2]/div[1]/span').text
                    if rent_title is None:
                        rent_title = driver.find_element(
                            By.XPATH, f'//*[@id="rent-list-app"]/div/div[3]/div[1]/section[3]/div/section[{count}]/a/div[2]/div[1]/span[1]').text

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
                        for i in range(6, 16):
                            try:
                                next = driver.find_element(
                                    By.XPATH, f'//*[@id="rent-list-app"]/div/div[3]/div[1]/section[4]/div/a[{i}]')
                                if next.text == "下一頁":

                                    # Verify if the class attribute contains "last"
                                    if "last" in next.get_attribute("class").split():
                                        print("No more pages available. Exiting loop.")
                                        condition = False
                                        break
                                    else:
                                        print("Next page")

                                    next.click()

                                    # Wait for the page to refresh
                                    WebDriverWait(driver, 10).until(EC.staleness_of(next))
                                    print("Page refreshed.")
                                    break

                            except Exception as e:
                                continue

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

# Function to create and start threads
def start_threads(num_threads, driver):
    threads = []

    rent_url = "https://rent.591.com.tw/?region=1&order=posttime&orderType=desc"

    # Create and start threads
    for _ in range(num_threads):
        thread = threading.Thread(target=crawl_and_store_data, args=(rent_url, driver))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


def main():

    # Testing
    

    driver = webdriver.Chrome(options=options)
    rent_url = "https://rent.591.com.tw/?region=1&order=posttime&orderType=desc"
    
    crawl_and_store_data(rent_url, driver)


if __name__ == "__main__":
    main()
