from flask import render_template, request, redirect, url_for, jsonify
from datetime import datetime
from dotenv import load_dotenv
from utils import authentication, get_user_name, calculate_house_metrics
import os
import re
import pymongo
import numpy as np
import logging
from user_model.house_data_process import transform_one_house, transform_all_house, match_house, get_value_from_house_dict, one_hot_gender


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


def remove_house():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        remove_house_id = request.json.get('remove_house')
        user_collection = client['personal_project']['user']

        cur_user = user_collection.find_one({"user_id": user_id})
        cur_user_save_house_ls = cur_user.get('saved_house', [])

        if int(remove_house_id) in cur_user_save_house_ls:
            cur_user_save_house_ls.remove(int(remove_house_id))

            # Update the saved house list
            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'saved_house': cur_user_save_house_ls}},
                upsert=True
            )

    return redirect(url_for('login'))


def get_user_save_house():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    house_collection = client['personal_project']['house']
    user_collection = client['personal_project']['user']
    cur_user_save_house_list = user_collection.find_one({"user_id": user_id})[
        'saved_house']

    houses = house_collection.find({"id": {"$in": cur_user_save_house_list}})
    houses_json = [
        {**house, '_id': str(house['_id'])}
        for house in houses
    ]
    return jsonify(houses_json), 200


def get_user_house(house_id):
    house_collection = client['personal_project']['house']
    house = house_collection.find_one({"id": house_id})
    if house:
        # Convert ObjectId to string
        search_house_json = {**house, '_id': str(house['_id'])}
        return jsonify(search_house_json), 200

    logger.warning(f"House not found")
    return jsonify({'error': 'House not found'}), 404


def get_user_recommend_house(house_id):
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        db = client['personal_project']
        house_collection = db['house']
        transform_all_house_collection = db['transform_all_house']

        # Get current house
        cur_transform_house = transform_all_house_collection.find_one(
            {"house_id": house_id})
        cur_house = house_collection.find_one({"id": house_id})

        logger.info(f"-----------------Start Search-----------------")
        cur_house_zone = cur_house["address"]
        district = cur_house_zone.split('市')[-1]
        district = district.split('區')[0]

        regex_pattern = re.compile(f'({district})', re.IGNORECASE)
        matching_zone_houses = house_collection.find({
            "address": {"$regex": regex_pattern},
        })
        logger.info(f"matching_zone_houses {matching_zone_houses}")

        house_ids = [matching_zone_house["id"]
                     for matching_zone_house in matching_zone_houses]
        transform_select_house_data_dicts = list(
            transform_all_house_collection.find({"house_id": {"$in": house_ids}}))

        transform_house_id_list, transform_house_value_list = get_value_from_house_dict(
            transform_select_house_data_dicts)

        nearest_neighbors_id_list = match_house(transform_house_id_list, transform_house_value_list,
                                                cur_transform_house["value"], 6)
        try:
            match_houses = house_collection.find(
                {"id": {"$in": nearest_neighbors_id_list}})

            matches_houses_data = [{'house_id': match_house['id'], 'title': match_house['title'], 'price': match_house['price'], 'address': match_house['address'], 'age': match_house['age'], 'size': match_house['size'], 'img_url': match_house['img_url']}
                                   for match_house in match_houses if int(match_house['id']) != int(house_id)]

            logger.info(f"Detail recommend houses: {len(matches_houses_data)}")
        except Exception as e:
            logger.warning("Recommend house not found", e)
            return jsonify({'error': 'No match'}), 500

        return jsonify(matches_houses_data), 200


def save_house():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if request.method == 'POST':
        data = request.get_json()
        house_id = data.get('save_house')

        logger.info(f"{user_id} save house {house_id}")

        if house_id is None:
            return jsonify({'error': 'House ID not provided'}), 400

        save_house_ls = []
        if isinstance(user_id, int):
            user_collection = client['personal_project']['user']
            cur_user = user_collection.find_one({"user_id": user_id})
            cur_user_save_house_ls = cur_user.get('saved_house', [])

            if int(house_id) not in cur_user_save_house_ls:
                save_house_ls.append(int(house_id))

            save_house_ls.extend(cur_user_save_house_ls)

            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'saved_house': save_house_ls}},
                upsert=True
            )

            return "House saved successfully", 200

        cur_time = datetime.now()
        logger.warning(f"{cur_time} Login timeout")
        return redirect(url_for('login'))

    else:
        cur_time = datetime.now()
        logger.error(f"{cur_time} Save house error : Invalid Content-Type")
        return jsonify({'error': 'Invalid Content-Type'}, 400)


def search_hot():

    # First get user's house preference
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if not user_id:
        logger.warning(f"Login timeout")
        return redirect(url_for('login'))

    house_collection = client['personal_project']['house']
    top_houses = list(house_collection.find().sort([('click', -1)]).limit(10))
    top_houses_json = [
        {**house, '_id': str(house['_id'])}  # Convert ObjectId to string
        for house in top_houses
    ]

    logger.info(f"Top houses: {len(top_houses_json)}")

    if top_houses_json:
        return jsonify(top_houses_json), 200
    else:
        # If no clicks, return random houses
        random_houses = list(client['personal_project']['house'].aggregate(
            [{'$sample': {'size': 10}}]))
        random_houses_json = [
            {**house, '_id': str(house['_id'])}  # Convert ObjectId to string
            for house in random_houses
        ]
        return jsonify(random_houses_json), 200


def search():
    # Retrieve the parameters from the query string
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        user_collection = client['personal_project']['user']
        house_collection = client['personal_project']['house']
        user = user_collection.find_one({"user_id": user_id})
        user_house_preference = user['house_preference']

        # Base on this preference to search for house
        zones = user_house_preference['zone']
        zone_pattern = '|'.join(zones)
        regex_pattern = re.compile(f'({zone_pattern})', re.IGNORECASE)

        # Query MongoDB to find matching houses
        matching_houses = house_collection.find({
            # Price less than user's input price
            'price': {'$lte': float(user_house_preference['price'])},
            'age': {'$lte': int(user_house_preference['house_age'])},
            "address": {"$regex": regex_pattern},
            'stay_landlord': user_house_preference['stay_with_landlord'] == "yes",
            'park': user_house_preference['park_nearby'] == "yes",
        })

        # Convert matching houses to a list before returning
        search_houses_json = [
            {**house, '_id': str(house['_id'])}  # Convert ObjectId to string
            for house in matching_houses
        ]

        logger.info(f"Search houses: {len(search_houses_json)}")
        return jsonify(search_houses_json), 200

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def ai_recommend():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        db = client['personal_project']
        user_collection = db['user']
        house_collection = db['house']
        transform_all_house_collection = db['transform_all_house']

        # Get current user
        cur_user = user_collection.find_one({"user_id": user_id})

        # Summarize user save house and click house
        user_house_transform_dict = {'save': [], 'click': []}
        user_house_address_dict = {'address': []}

        user_save_house_ids = cur_user.get('saved_house', [])
        for user_save_house_id in user_save_house_ids:
            user_house_transform_dict['save'].append(transform_all_house_collection.find_one(
                {"house_id": user_save_house_id})['value'])
            user_house_address_dict['address'].append(house_collection.find_one(
                {"id": user_save_house_id})['address'])

        user_click_houses = cur_user.get('click_house', [])
        for user_click_house_id in user_click_houses:
            user_house_transform_dict['click'].append(transform_all_house_collection.find_one(
                {"house_id": user_click_house_id})['value'])
            user_house_address_dict['address'].append(house_collection.find_one(
                {"id": user_click_house_id})['address'])

        logger.info(
            f"------------------Start AI search-------------------------")

        # Get the highest and lowest price, age, and size from user's save and click house
        lowest_price, highest_price, lowest_age, highest_age, lowest_size, highest_size = calculate_house_metrics(
            user_house_transform_dict)

        # Search similar zone
        zones = []
        for address in user_house_address_dict['address']:
            district = address.split('市')[-1]
            district = district.split('區')[0] + '區'
            zones.append(district)

        logger.info(f"{zones}")

        zone_pattern = '|'.join(zones)
        regex_pattern = re.compile(f'({zone_pattern})', re.IGNORECASE)
        zone_id_list = [house['id'] for house in house_collection.find(
            {"address": {"$regex": regex_pattern}})]

        transform_id_list = []
        for matching_house in transform_all_house_collection.find({"house_id": {"$in": zone_id_list}}):
            if (matching_house['value'][0] <= highest_price and matching_house['value'][0] >= lowest_price) and ((matching_house['value'][1] <= highest_age and matching_house['value'][1] >= lowest_age) or (matching_house['value'][2] <= highest_size and matching_house['value'][2] >= lowest_size)):
                transform_id_list.append(matching_house['house_id'])

        nearest_neighbors_id_list = [
            transform_id for transform_id in transform_id_list if transform_id not in cur_user['saved_house'] and transform_id not in cur_user['click_house']][:10]

        try:
            match_houses = house_collection.find(
                {"id": {"$in": nearest_neighbors_id_list}})

            search_houses_json = [
                # Convert ObjectId to string
                {**house, '_id': str(house['_id'])}
                for house in match_houses
            ]

            logger.info(f"AI recommend houses: {len(search_houses_json)}")

        except Exception as e:
            cur_time = datetime.now()
            logger.error(f"{cur_time} AI recommend error : ", e)
            return jsonify({'error': 'No match'}), 500

        return jsonify(search_houses_json), 200
