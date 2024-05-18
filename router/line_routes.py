from flask import render_template, request, redirect, url_for, jsonify
from datetime import datetime
from dotenv import load_dotenv
from function import authentication, get_user_name
import os
import pymongo
import logging
from function import getNotifyToken, authentication

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


def line_house_preference():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        price = request.form.get('price')
        house_age = request.form.get('houseAge')
        zone = request.form.getlist('zone')
        stay_with_landlord = request.form.get('stayWithLandlord')
        park_nearby = request.form.get('park')

        db = client["personal_project"]
        user_collection = db["user"]
        user_collection.update_one(
            {"user_id": user_id},
            {"$set": {'line_preference': {'price': price, 'house_age': house_age, 'zone': zone,
                                          'stay_with_landlord': stay_with_landlord, 'park_nearby': park_nearby}}}
        )
    return jsonify("Line preference saved successfully"), 200


def line_register():
    # Get user id from cookies
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    try:
        authorizeCode = request.args.get('code')
        token = getNotifyToken(authorizeCode, user_id)
    except Exception as e:
        cur_time = datetime.now()
        logger.error(f"{cur_time} Error in getting token {e}")

    # Save in mongo DB
    db = client["personal_project"]
    user_collection = db["user"]
    user_collection.update_one(
        {"user_id": int(user_id)},
        {"$set": {'access_token': token}},
        upsert=True)

    return redirect(url_for('line_page'))
