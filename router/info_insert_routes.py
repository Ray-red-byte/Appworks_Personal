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


def user_info_insert():

    if request.method == 'POST':

        token = request.cookies.get('token')

        # Call the authentication function to verify the token
        user_id = authentication(token, jwt_secret_key)

        if isinstance(user_id, int):
            username = get_user_name(user_id)
            user_collection = client['personal_project']['user']

            # Extract form data
            gender = request.form['gender']
            identity = request.form['identity']
            partner = request.form['partner']
            introduction = request.form['introduction']

            # Prepare basic information data
            basic_info_data = {
                'gender': gender,
                'identity': identity,
                'partner': partner,
                'introduction': introduction
            }

            # Update user's routine information in MongoDB
            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'basic_info': basic_info_data}}
            )

            return redirect(url_for('routine_page'))

        cur_time = datetime.now()
        logger.warning(f"{cur_time} Login timeout")

        return redirect(url_for('login'))


def user_routine_insert():

    if request.method == 'POST':
        # Retrieve the parameters from the query string
        token = request.cookies.get('token')

        # Call the authentication function to verify the token
        user_id = authentication(token, jwt_secret_key)

        if isinstance(user_id, int):

            # Extract form data
            sleep_time = request.form['sleepTime']
            wake_up_time = request.form['wakeUpTime']
            hygiene_tolerance = int(request.form['hygieneTolerance'])
            noise_tolerance = int(request.form['noiseTolerance'])
            cook_options = request.form['cookOptions']
            pet_options = request.form['petOptions']
            smoke_options = request.form['smokeOptions']
            additional_notes = request.form['additionalNotes']

            username = get_user_name(user_id)
            user_collection = client['personal_project']['user']

            # Prepare routine data
            routine_data = {
                'sleepTime': sleep_time,
                'wakeUpTime': wake_up_time,
                'hygieneTolerance': hygiene_tolerance,
                'noiseTolerance': noise_tolerance,
                'cookOptions': cook_options,
                'petOptions': pet_options,
                'smokeOptions': smoke_options,
                'additionalNotes': additional_notes
            }

            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'routine': routine_data}}
            )

            return redirect(url_for('main_page'))

        cur_time = datetime.now()
        logger.warning(f"{cur_time} Login timeout")

        return redirect(url_for('login'))


def user_filter_insert():
    if request.method == 'POST':

        # Retrieve the parameters from the query string
        token = request.cookies.get('token')

        # Call the authentication function to verify the token
        user_id = authentication(token, jwt_secret_key)

        if isinstance(user_id, int):

            # Retrieve form data
            price = request.form.get('price')
            house_age = request.form.get('houseAge')
            zone = request.form.getlist('zone')
            stay_with_landlord = request.form.get('stayWithLandlord')
            park_nearby = request.form.get('park')

            username = get_user_name(user_id)
            user_collection = client['personal_project']['user']

            # Create a dictionary to represent the document to be inserted
            house_preference = {
                'price': price,
                'house_age': house_age,
                'zone': zone,
                'stay_with_landlord': stay_with_landlord,
                'park_nearby': park_nearby
            }

            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'house_preference': house_preference}}
            )

            return "House preference saved successfully", 200

        cur_time = datetime.now()
        logger.warning(f"{cur_time} Login timeout")

        return redirect(url_for('login'))

    else:
        cur_time = datetime.now()
        logger.error(
            f"{cur_time} User filter insert error : Invalid Content-Type")
        return jsonify({'error': 'Invalid Content-Type'}, 400)
