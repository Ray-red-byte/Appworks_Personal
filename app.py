from page_routes import main_page, routine_page, house_type_page, house_detail_page, line_page, line_register_page, user_profile, save_house_page, user_information
from socketio_routes import handle_online, handle_offline, on_join, on_leave, handle_message
from chat_routes import chat_user_data, cancel, save_messages, chat_history, save_messages, get_messages, get_matches, allocate_chat_room, chat
from info_insert_routes import user_info_insert, user_routine_insert, user_filter_insert
from initial_routes import login, logout, register, register_validate, login_token
from house_routes import remove_house, get_user_save_house, get_user_house, get_user_recommend_house, save_house, search_hot, search, ai_recommend
from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
import requests
import os
import re
from dotenv import load_dotenv
from datetime import datetime
from celery import Celery
import pymongo
import numpy as np
import time
import logging
import signal
import subprocess
from werkzeug.security import generate_password_hash, check_password_hash
from function import get_user_id, check_exist_user, validate_email, create_token, authentication, get_user_password, get_user_name, calculate_active_status, get_next_user_id
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from user_model.user_data_process import transform_one_user, transform_all_user, match_user, get_value_from_user_dict
from user_model.house_data_process import transform_one_house, transform_all_house, match_house, get_value_from_house_dict, one_hot_gender

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

# JWT secret key
jwt_secret_key = os.getenv('JWT_SECRET_KEY')

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")


# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)


# LINE notify
LINE_SUBSCRIBE_URL = os.getenv("LINE_SUBSCRIBE_URL")
LINE_CLIENT_ID = os.getenv("LINE_CLIENT_ID")
LINE_CLIENT_SECRET = os.getenv("LINE_CLIENT_SECRET")


app.add_url_rule('/login', 'login', login)
app.add_url_rule('/logout', 'logout', logout, methods=['GET'])
app.add_url_rule('/register', 'register', register)
app.add_url_rule('/user/register_validate', 'register_validate',
                 register_validate, methods=['GET', 'POST'])
app.add_url_rule('/user/login_token', 'login_token',
                 login_token, methods=['POST'])

# -------------------------------------------------------User insert page-------------------------------------------------------
app.add_url_rule('/user/info_insert', 'user_info_insert',
                 user_info_insert, methods=["GET", "POST"])
app.add_url_rule('/user/routine_insert', 'user_routine_insert',
                 user_routine_insert, methods=["GET", "POST"])
app.add_url_rule('/user/filter', 'user_filter_insert',
                 user_filter_insert, methods=["GET", "POST"])
# -------------------------------------------------------User insert page-------------------------------------------------------

# -------------------------------------------------------User house-------------------------------------------------------
app.add_url_rule('/remove_house', 'remove_house',
                 remove_house, methods=['POST'])
app.add_url_rule('/user/house/', 'get_user_save_house',
                 get_user_save_house, methods=['GET'])
app.add_url_rule('/user/house/<int:house_id>',
                 'get_user_house', get_user_house)
app.add_url_rule('/user/house/recommend/<int:house_id>',
                 'get_user_recommend_house', get_user_recommend_house)
app.add_url_rule('/save_house', 'save_house',
                 save_house, methods=["GET", "POST"])
app.add_url_rule('/search/hot', 'search_hot', search_hot)
app.add_url_rule('/search', 'search', search)
app.add_url_rule('/ai_recommend', 'ai_recommend', ai_recommend)

# -------------------------------------------------------User house-------------------------------------------------------


@ app.route('/track/click', methods=['POST'])
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

# ------------------------------------------------------Track user click house------------------------------------------------------

# ------------------------------------------------------house detail page------------------------------------------------------

    # ------------------------------------------------------Get user house------------------------------------------------------


# ------------------------------------- Render template-------------------------------------
app.add_url_rule('/main', 'main_page', main_page)
app.add_url_rule('/routine', 'routine_page', routine_page)
app.add_url_rule('/user/house_detail/<int:houseId>',
                 'house_detail_page', house_detail_page)
app.add_url_rule('/line_page', 'line_page', line_page)
app.add_url_rule('/line_register', 'line_register_page', line_register_page)
app.add_url_rule('/user/profile/<int:chat_user_id>',
                 'user_profile', user_profile)
app.add_url_rule('/user/save_house', 'save_house_page', save_house_page)
app.add_url_rule('/user/information', 'user_information',
                 user_information, methods=['GET', 'POST'])
# ------------------------------------- Render template-------------------------------------


# -----------------------------------------Chat room----------------------------------------
app.add_url_rule('/user/current/<int:chat_user_id>',
                 'chat_user_data', chat_user_data)
app.add_url_rule('/cancel', 'cancel', cancel, methods=['POST'])
app.add_url_rule('/chat_history', 'chat_history',
                 chat_history, methods=['GET', 'POST'])
app.add_url_rule('/save/messages', 'save_messages',
                 save_messages, methods=['POST'])
app.add_url_rule('/get/messages', 'get_messages',
                 get_messages, methods=['POST'])
app.add_url_rule('/matches/<string:match_type>', 'get_matches', get_matches)
app.add_url_rule('/allocate_chat_room', 'allocate_chat_room',
                 allocate_chat_room, methods=['GET', 'POST'])
app.add_url_rule('/chat/<int:user_id>', 'chat', chat)
# ------------------------User Save House------------------------


# --------------------------------------------------------LINE Notify--------------------------------------------------------
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


@ app.route('/line/preference', methods=['POST'])
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


@ app.route('/send', methods=['GET', 'POST'])
def send():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    # Get user access_token from mongoDB
    db = client["personal_project"]
    user_collection = db["user"]
    cur_user = user_collection.find_one({"user_id": user_id})
    access_token = cur_user["access_token"]

    logger.info(f"start to use line notify : {user_id}")

    monitor.delay(user_id, access_token)
    return jsonify("Start to send"), 200


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


@ app.route('/', methods=['POST', 'GET'])
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


# Add URL routes using add_url_rule
socketio.on_event('online', handle_online)
socketio.on_event('offline', handle_offline)
socketio.on_event('join_room', on_join)
socketio.on_event('leave', on_leave)
socketio.on_event('send_message', handle_message)


if __name__ == '__main__':
    socketio.run(app)
