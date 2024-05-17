import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import numpy as np
import os
from flask import jsonify
import logging
import requests
import pymongo

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

log_filename = os.getenv("APP_LOG_FILE_NAME")
log_file_path = os.getenv("APP_LOG_FILE_PATH")
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path,
                    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)

# Select a database and collection
db = client["personal_project"]
user_collection = db["user"]
house_collection = db["house"]


def calculate_house_metrics(user_house_transform_dict):
    np_save = np.array(user_house_transform_dict['save'])
    np_click = np.array(user_house_transform_dict['click'])

    highest_save_price = np_save[:, 0].max()
    lowest_save_price = np_save[:, 0].min()
    highest_click_price = np_click[:, 0].max()
    lowest_click_price = np_click[:, 0].min()

    highest_save_age = np_save[:, 1].max()
    lowest_save_age = np_save[:, 1].min()
    highest_click_age = np_click[:, 1].max()
    lowest_click_age = np_click[:, 1].min()

    highest_save_size = np_save[:, 2].max()
    lowest_save_size = np_save[:, 2].min()
    highest_click_size = np_click[:, 2].max()
    lowest_click_size = np_click[:, 2].min()

    lowest_price = (lowest_save_price * 2 + lowest_click_price) / 3
    highest_price = (highest_save_price * 2 + highest_click_price) / 3
    lowest_age = (lowest_save_age * 2 + lowest_click_age) / 3
    highest_age = (highest_save_age * 2 + highest_click_age) / 3
    lowest_size = (lowest_save_size * 2 + lowest_click_size) / 3
    highest_size = (highest_save_size * 2 + highest_click_size) / 3

    return lowest_price, highest_price, lowest_age, highest_age, lowest_size, highest_size


def get_next_user_id():
    # Find and update the user_id counter
    counter_doc = client['personal_project']['user'].counters.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,  # Create the counter if it doesn't exist
        return_document=True
    )
    return counter_doc["seq"]


def calculate_active_status(be_cancel, be_chatted_user, chat_user, saved_house, click_house):
    # Define weights for each activity
    weights = {
        'be_cancel': 0.01,
        'be_chatted_user': 0.5,
        'chat_user': 0.2,
        'saved_house': 0.24,
        'click_house': 0.05
    }

    # Calculate total activity score
    total_score = (
        weights['be_chatted_user'] * be_chatted_user +
        weights['chat_user'] * chat_user +
        weights['saved_house'] * saved_house +
        weights['click_house'] * click_house -
        weights['be_cancel'] * be_cancel
    )

    # Normalize the total score to a percentage (assuming maximum score is 100)
    max_score = sum(weights.values()) * 100
    active_status_percent = min(
        (total_score / max_score) * 100, 100) if total_score > 0 else 0

    return active_status_percent


def get_user_id(username, email):
    db = client["personal_project"]
    user_collection = db["user"]
    user = user_collection.find_one({"username": username, "email": email})
    try:
        if user:
            return user["user_id"]
        return None
    except Exception as e:
        print(e)
        return None


def get_user_password(user_id):
    db = client["personal_project"]
    user_collection = db["user"]
    try:
        user = user_collection.find_one({"user_id": user_id})
        if user:
            return user["password"]
        else:
            print("User not found")
            return None
    except Exception as e:
        print("Error:", e)
        return None


def get_user_name(user_id):
    db = client["personal_project"]
    user_collection = db["user"]
    try:
        user = user_collection.find_one({"user_id": user_id})
        if user:
            return user["username"]
        else:
            print("User not found")
            return None
    except Exception as e:
        print("Error:", e)
        return None


def check_exist_user(user_id):
    if user_id:
        user = user_collection.find_one({"user_id": user_id})
        if user:
            return True
    return False


def validate_email(email):
    email_pattern = re.compile(
        r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    if email_pattern.match(email):
        return True
    return False


# Custom function to create JWT toke
def create_token(user_id, jwt_secret_key):
    # Token expiresuser_id in 1 minutes

    expiration_time = datetime.now() + timedelta(seconds=600)
    payload = {'user_id': user_id, 'exp': expiration_time}
    token = jwt.encode(payload, str(jwt_secret_key), algorithm='HS256')
    return token


def authentication(token, jwt_secret_key):
    # Retrieve user profile from DB
    if not token:
        return jsonify({'message': 'Token is missing'}), 401

    try:
        # Extract the token value (remove 'Bearer ' if present)
        token = token.split(' ')[1] if token.startswith('Bearer ') else token
        # Verify and decode the token
        decoded_token = jwt.decode(
            token, jwt_secret_key, algorithms=['HS256'])
        # Retrieve the user ID from the decoded token
        user_id = decoded_token.get('user_id')
        return user_id
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 500


def getNotifyToken(AuthorizeCode, user_id):
    body = {
        "grant_type": "authorization_code",
        "code": AuthorizeCode,
        "redirect_uri": f'https://rentright.info',
        "client_id": 'bvtTFwMkqG5LiWFJIq3aXb',
        "client_secret": 'saHb9IQBraM3Rm76iNMModraELZAjx7YJUiibpfEfUh'
    }
    r = requests.post("https://notify-bot.line.me/oauth/token", data=body)
    return r.json()["access_token"]


def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify",
                      headers=headers, data=payload)
    return r.status_code
