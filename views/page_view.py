from flask import render_template, request, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv
from utils import authentication, get_user_name
import os
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


def main_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('main.html', username=username, user_id=user_id)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def routine_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('routine.html', username=username)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def house_type_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('house_type.html', username=username)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def house_detail_page(houseId):
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)
    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('house_detail.html', username=username, houseId=houseId)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def line_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('line.html')

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def line_register_page():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('line_register.html', username=username)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def user_profile(chat_user_id):
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)
    if isinstance(user_id, int):
        chat_username = get_user_name(chat_user_id)
        return render_template('user_profile.html', chat_user_id=chat_user_id, username=chat_username)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def save_house_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)
    if isinstance(user_id, int):
        return render_template('save_house.html', user_id=user_id)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def user_information():
    # Retrieve the parameters from the query string
    token = request.cookies.get('token')

    logger.info(f"-----------------User information page-----------------")

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('user_information.html', username=username, user_id=user_id)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")

    return redirect(url_for('login'))
