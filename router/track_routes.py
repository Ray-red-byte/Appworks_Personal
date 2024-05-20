from flask import render_template, request, redirect, url_for, jsonify
from datetime import datetime
from dotenv import load_dotenv
from function import authentication, get_user_name
import os
import pymongo
import logging

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

log_filename = os.getenv("APP_LOG_FILE_NAME")
log_file_path = os.getenv("APP_LOG_FILE_PATH")
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path,
                    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


# JWT secret key
jwt_secret_key = os.getenv('JWT_SECRET_KEY')

# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)


def track_click():
    house_id = request.json.get('house_id')

    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    # Save house click
    house_collection = client['personal_project']['house']
    house_collection.update_one(
        {'id': int(house_id)},
        {'$inc': {'click': 1}},
        upsert=True
    )

    # Save user click
    click_house_ls = []
    if isinstance(user_id, int):
        user_collection = client['personal_project']['user']
        cur_user = user_collection.find_one({"user_id": user_id})
        cur_user_click_house_ls = cur_user.get('click_house', [])

        if int(house_id) not in cur_user_click_house_ls:
            click_house_ls.append(int(house_id))

        click_house_ls.extend(cur_user_click_house_ls)

        user_collection.update_one(
            {'user_id': user_id},
            {'$set': {'click_house': click_house_ls}},
            upsert=True
        )

    return "Click tracked", 200
