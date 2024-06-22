from celery import Celery
from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
import logging
import os
import re
import time
from utils import get_user_id, check_exist_user, validate_email, create_token, authentication, get_user_password, get_user_name, calculate_active_status, get_next_user_id, lineNotifyMessage, getNotifyToken
from dotenv import load_dotenv
import pymongo

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

log_filename = os.getenv("APP_LOG_FILE_NAME")
log_file_path = os.getenv("APP_LOG_FILE_PATH")
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path,
                    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET')
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(
    app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
celery.conf.update(app.config)

# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)


@ celery.task
def monitor(user_id, access_token):
    db = client["personal_project"]

    last_update_at = ''
    count = 0
    while True:
        # Query MongoDB to get the latest houses
        logger.info(f"Start to use line ")

        house_collection = db["house"]
        user_collection = db["user"]
        cur_user = user_collection.find_one({"user_id": user_id})
        cur_user_house_preference = cur_user["line_preference"]

        zones = cur_user_house_preference['zone']
        zone_pattern = '|'.join(zones)
        regex_pattern = re.compile(f'({zone_pattern})', re.IGNORECASE)

        if count == 0:  # At first find the last one
            last_house_list = house_collection.find().sort(
                [("updated_at", -1)]).limit(1)
            for i in last_house_list:
                last_update_at = i['updated_at']
        else:

            try:
                last_house_list = house_collection.find(
                    {"updated_at": {"$gt": last_update_at}})
                last_update_at = house_collection.find().sort(
                    [("updated_at", -1)]).limit(1)[0]['updated_at']

            except Exception as e:
                logger.info(f"No house available {e}")
                # lineNotifyMessage(
                #    access_token, f"No house is available")
                time.sleep(10)
                continue

        # Check if last house match user's preference
        for last_house in last_house_list:
            if float(last_house['price']) <= float(cur_user_house_preference['price']) and int(last_house['age']) <= int(cur_user_house_preference['house_age']) and re.search(regex_pattern, last_house['address']) and last_house['stay_landlord'] == (cur_user_house_preference['stay_with_landlord'] == "yes") and last_house['park'] == (cur_user_house_preference['park_nearby'] == "yes"):
                house_title = last_house["title"]
                house_price = last_house['price']
                house_address = last_house['address']
                house_age = last_house['age']
                house_url = "https://rentright.info/user/house_detail/" + \
                    str(last_house["id"])
                lineNotifyMessage(
                    access_token, "New house ! ! !")
                lineNotifyMessage(
                    access_token,
                    f"{house_title}\n{house_url}"
                )

        time.sleep(10)
        count += 1
