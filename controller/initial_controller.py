from flask import render_template, request, redirect, url_for, jsonify, make_response
from datetime import datetime
from dotenv import load_dotenv
from utils import authentication, get_user_name
import os
import pymongo
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from utils import validate_email, get_user_id, get_user_password, create_token, calculate_active_status, get_next_user_id

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


def login():
    return render_template('login.html')


def logout():
    try:
        user_collection = client['personal_project']['user']
        user_id = authentication(request.cookies.get('token'), jwt_secret_key)
        user = user_collection.find_one({"user_id": user_id})

        save_house_count = len(user.get('saved_house', []))
        click_house_count = len(user.get('click_house', []))
        be_cancel_count = len(user.get('be_cancel', []))
        be_chatted_user_count = user.get('be_chatted_user', 0)
        chat_user_count = user.get('chat_user', 0)

        active_status_percent = calculate_active_status(be_cancel_count, be_chatted_user_count,
                                                        chat_user_count, save_house_count, click_house_count)

        user_collection.update_one(
            {'user_id': user_id},
            {'$set': {'active_status': active_status_percent}},
            upsert=True
        )

        response = make_response(redirect(url_for('login')))
        response.set_cookie('token', '', expires=0)
        return response

    except Exception as e:
        cur_time = datetime.now()
        logger.error(f"{cur_time} Logout error : {e}")


def login_token():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')

        if content_type != 'application/json':
            cur_time = datetime.now()
            logger.error(f"{cur_time} Login error : Invalid Content-Type")
            return jsonify({'error': 'wrong Content-type'}, 400)

        form_data = request.get_json()
        user_name = form_data["username"]
        user_login_password = form_data["password"]
        user_email = form_data["email"]

        if not validate_email(user_email):
            cur_time = datetime.now()
            logger.error(f"{cur_time} Login error : Invalid email")
            response_data = {"Error": 'Invalid email'}
            return response_data, 400

        # Get user_id then get password from MongoDB
        user_id = get_user_id(user_name, user_email)
        if user_id:
            user_password = get_user_password(user_id)
        else:
            cur_time = datetime.now()
            logger.error(f"{cur_time} Login error : Invalid User Name")
            response_data = {"Error": 'Invalid username or email'}
            return response_data, 400

        # Check if password is correct
        if not check_password_hash(user_password, user_login_password):
            cur_time = datetime.now()
            logger.error(f"{cur_time} Login error : Invalid password")
            response_data = {"Error": 'Invalid password'}
            return response_data, 400

        token = create_token(user_id, jwt_secret_key)

        # Create a response object
        response = make_response()

        # Set the token in the response header
        response.headers["Authorization"] = f"Bearer {token}"
        return response, 200

    else:
        cur_time = datetime.now()
        logger.error(f"{cur_time} Login error : Invalid Content-Type")
        response_data = {"Error": "Invalid Content-Type"}
        return response_data, 400


def register():
    return render_template('register.html')


def register_validate():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')

        if content_type != 'application/json':
            return jsonify({'error': 'wrong Content-type'}, 400)

        form_data = request.get_json()
        user_name = form_data["username"]
        user_email = form_data["email"]
        user_login_password = form_data["password"]

        if not validate_email(user_email):
            response_data = {"Error": 'Invalid email'}
            return response_data

        # Get user_id then get password from MongoDB
        user_id = get_user_id(user_name, user_email)
        if user_id:
            response_data = {'Alresdy exist user'}
            return response_data

        # Hash the password
        hashed_password = generate_password_hash(user_login_password)

        # Generate the user ID
        user_id = get_next_user_id()

        timestamp = datetime.now()

        # Isnert into mongoDB
        user_info = {
            "user_id": user_id,
            "username": user_name,
            "email": user_email,
            "password": hashed_password,
            "active_status": 0,
            'timestamp': timestamp
        }
        user_collection = client['personal_project']['user']

        user_collection.insert_one(user_info)

        return jsonify({'message': 'Register is valid'}), 200

    else:
        cur_time = datetime.now()
        logger.error(f"{cur_time} Register error : Invalid Content-Type")
        response_data = {"Error": "Invalid Content-Type"}
        return response_data, 400
