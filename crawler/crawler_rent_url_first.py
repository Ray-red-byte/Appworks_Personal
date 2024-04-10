from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import base64
import time
import json
import random
import requests
import threading
import logging
from bs4 import BeautifulSoup

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


def load_urls_from_json(json_file):
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}


def store_url(urls, json_file):

    with open(json_file, 'a') as f:
        json.dump(urls, f, ensure_ascii=False)
    print(f"URL stored successfully.")


def next_page_click(driver):
    try:

        # Try each span to be clicked
        for i in range(6, 16):
            try:
                next = driver.find_element(
                    By.XPATH, f'//*[@id="rent-list-app"]/div/div[3]/div[1]/section[4]/div/a[{i}]')
                if next.text == "下一頁":

                    # Verify if the class attribute contains "last"
                    if "last" in next.get_attribute("class").split():
                        print("No more pages available. Exiting loop.")
                        return False
                    else:
                        print("The class of the <a> element is not 'last'")

                    next.click()
                    break

            except Exception as e:
                continue

        time.sleep(1)

        return True

    except Exception as e:
        print(e)
        print("No more pages available. Exiting loop.")
        return False


def crawl_and_store_data(website_url, driver):

    simulate_human_interaction(driver)

    try:

        time.sleep(5)
        driver.get(website_url)
        time.sleep(5)  # Adjust sleep time as needed for the page to load

        # --------------Rent----------------
        count = 1
        next_page = 1
        total = 0
        json_file = "./rent_url.json"
        previous_urls = {}
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

                # Data correction
                if rent_href not in previous_urls:
                    new_urls.update({rent_href: rent_title})
                    print("Success", rent_href, rent_title)
                else:
                    next_page_click(driver)
                    count = 1

            except Exception as e:
                logger.info("-------------Next page-------------")
                logger.info(f"{next_page}")

                next_page += 1
                condition = next_page_click(driver)
                count = 1

                # Update urls
                if next_page % 3 == 0:
                    store_url(new_urls, json_file)
                    print(next_page, "success")
                    previous_urls = new_urls
                    new_urls = {}

        print(total)
        # ----------------------------------

    except Exception as e:
        print(f"Error retrieving data: {type(e).__name__} - {e}")
    finally:
        # Close the Chrome driver
        driver.quit()


def main():

    # Testing
    rent_url = "https://rent.591.com.tw/?order=posttime&orderType=desc"

    driver = webdriver.Chrome(options=options)
    crawl_and_store_data(rent_url, driver)

    # Create a list to hold thread objects
    threads = []
    '''
    for i in range(1, 100):
        for j in range(1, 5):
            driver = webdriver.Chrome(options=options)
            thread = threading.Thread(
                target=crawl_and_store_data, args=(website_url, driver, i, j))
            thread.start()
            time.sleep(10)
            threads.append(thread)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
    '''


if __name__ == "__main__":
    main()
