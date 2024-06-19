from flask import render_template, request, redirect, url_for, jsonify
from datetime import datetime
from dotenv import load_dotenv
from utils import authentication, get_user_name
from user_model.user_data_process import transform_one_user, transform_all_user, match_user, get_value_from_user_dict
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


def chat_user_data(chat_user_id):
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)
    if isinstance(user_id, int):
        user_collection = client['personal_project']['user']
        chat_user = user_collection.find_one({"user_id": chat_user_id})
        chat_user_data = {
            'username': chat_user['username'],
            'email': chat_user['email'],
            'basic_info': chat_user['basic_info'],
            'routine': chat_user['routine'],
            'house_preference': chat_user['house_preference']
        }
        return jsonify(chat_user_data), 200

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def cancel():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    cancel_room_id = request.json.get('room_id')
    cancel_chat_user_id = request.json.get('chat_user_id')

    room_collection = client['personal_project']['room']
    room_collection.delete_one({"room_id": cancel_room_id})

    # Track user status
    user_collection = client['personal_project']['user']
    cancel_user = user_collection.find_one({"user_id": cancel_chat_user_id})
    cancel_user_cancel_ls = cancel_user.get('be_canceled', [])

    if user_id not in cancel_user_cancel_ls:
        cancel_user_cancel_ls.append(user_id)

    user_collection.update_one(
        {'user_id': cancel_chat_user_id},
        {'$set': {'be_cancel': cancel_user_cancel_ls}},
        upsert=True
    )

    return "Cancel", 200


def chat_history():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)
    username = get_user_name(user_id)

    if isinstance(user_id, int):
        room_collection = client['personal_project']['room']
        user_collection = client['personal_project']["user"]
        all_rooms = room_collection.find({})

        other_user_id = []

        for room in all_rooms:
            seperate_room_id = list(map(int, room["room_id"].split("_")))
            if user_id in seperate_room_id:

                status_messages = "unread"
                if room["last_updated_by"] == user_id:
                    status_messages = "read"
                else:
                    status_messages = "unread"

                other_user_id.append({
                    "message_status": status_messages,
                    "other_user_id": [user for user in seperate_room_id if user != user_id]
                })

        other_user_data = []
        for users in other_user_id:

            temp_user = {"message_status": users["message_status"],
                         "other_user": []}

            for user_id in users["other_user_id"]:
                chat_users = user_collection.find_one({"user_id": user_id})
                temp_user["other_user"].append(
                    {"user_id": chat_users["user_id"], "username": chat_users["username"]})
            other_user_data.append(temp_user)

        return jsonify(other_user_data), 200


def save_messages():
    room_collection = client['personal_project']['room']

    messages = request.json.get('messages')
    room_id = request.json.get('room_id')
    user_id = request.json.get('user_id')
    chat_user_id = request.json.get('chat_user_id')

    # Insert messages into MongoDB
    try:
        timestamp = datetime.now()

        # Track user status
        if int(user_id) < int(chat_user_id):
            room_id = f"{user_id}_{chat_user_id}"
        else:
            room_id = f"{chat_user_id}_{user_id}"

        if room_collection.find_one({"room_id": room_id}) is None:
            user_collection = client['personal_project']['user']
            cur_user = user_collection.find_one({"user_id": user_id})
            cur_user_chat_count = cur_user.get('chat_user', 0)
            cur_user_chat_count += 1
            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'chat_user': cur_user_chat_count}},
                upsert=True
            )

            chat_user = user_collection.find_one({"user_id": chat_user_id})
            chat_user_chat_count = chat_user.get('chat_user', 0)
            chat_user_chat_count += 1
            user_collection.update_one(
                {'user_id': chat_user_id},
                {'$set': {'be_chatted_user': chat_user_chat_count}},
                upsert=True
            )

        room_collection.update_one(
            {'room_id': room_id},
            {'$set': {'last_updated_by': user_id,
                      'messages': messages, 'timestamp': timestamp}},
            upsert=True  # Create a new document if no matching document is found
        )

        return jsonify({'success': True, 'message': 'Messages saved successfully'}), 200
    except Exception as e:
        logger.error("Error insert :", e)
        return jsonify({'success': False, 'message': 'Failed to save messages'}), 500


def get_messages():
    room_id = request.json.get('room_id')
    room_collection = client['personal_project']['room']
    room = room_collection.find_one({"room_id": room_id})

    if room:
        messages = room['messages']
        last_updated_user_id = room['last_updated_by']
        return jsonify({'messages': messages, 'last_updated_by': last_updated_user_id}), 200

    return jsonify({'error': 'Room not found'}), 404


def get_matches(match_type):
    # Start time to calculate the time and set in logger
    start_time = datetime.now()

    # Get all users from mongodb
    db = client["personal_project"]
    user_collection = db["user"]
    transform_all_user_collection = db["transform_all_user"]

    # Get current user
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    try:
        cur_user = user_collection.find_one({"user_id": int(user_id)})
        user_prefer_zone = cur_user["house_preference"]["zone"]
    except Exception as e:
        logger.warning(f"User not found", e)
        return jsonify({'error': 'User not found'}), 404

    # No matter what transform first
    row, transform_cur_user_dat_dict = transform_one_user(cur_user)
    transform_all_user_collection.update_one(
        {"user_id": int(user_id)},
        {"$set": transform_cur_user_dat_dict},
        upsert=True)

    # Get all users from the user collection and share one or more zones with the current user
    transform_cur_user_data = transform_all_user_collection.find_one(
        {"user_id": int(user_id)})

    logger.info(f"-----------------Start Search-----------------")

    if match_type == 'zone':

        users_share_zone_id_dict = user_collection.distinct(
            "user_id", {"house_preference.zone": {"$in": user_prefer_zone}})

        transform_users_share_zone_dict = transform_all_user_collection.find(
            {"user_id": {"$in": users_share_zone_id_dict}})

        transform_id_list, transform_value_list = get_value_from_user_dict(
            transform_users_share_zone_dict)

        '''
        mongo sort 
        '''
        user_active_statuses = user_collection.find(
            {"user_id": {"$in": transform_id_list}},
            {"active_status": 1, "user_id": 1}
        )

        user_active_status_list = list(user_active_statuses)
        sorted_user_active_status_list = sorted(
            user_active_status_list, key=lambda x: x['active_status'], reverse=True)[:500]

        sorted_user_ids = [user['user_id']
                           for user in sorted_user_active_status_list]

        transform_id_list, transform_value_list = get_value_from_user_dict(transform_all_user_collection.find(
            {"user_id": {"$in": sorted_user_ids}}))

        nearest_neighbors_id_list = match_user(transform_id_list, transform_value_list,
                                               transform_cur_user_data["value"], 11)

    elif match_type == 'same_gender':
        '''
            pack a function
        '''

        users_share_gender_id_dict = user_collection.distinct("user_id",
                                                              {"basic_info.gender": cur_user["basic_info"]["gender"]})

        transform_users_share_gender_dict = transform_all_user_collection.find(
            {"user_id": {"$in": users_share_gender_id_dict}})

        transform_id_list, transform_value_list = get_value_from_user_dict(
            transform_users_share_gender_dict)

        user_active_statuses = user_collection.find(
            {"user_id": {"$in": transform_id_list}},
            {"active_status": 1, "user_id": 1}
        )

        user_active_status_list = list(user_active_statuses)
        sorted_user_active_status_list = sorted(
            user_active_status_list, key=lambda x: x['active_status'], reverse=True)[:500]

        sorted_user_ids = [user['user_id']
                           for user in sorted_user_active_status_list]

        transform_id_list, transform_value_list = get_value_from_user_dict(transform_all_user_collection.find(
            {"user_id": {"$in": sorted_user_ids}}))

        nearest_neighbors_id_list = match_user(transform_id_list, transform_value_list,
                                               transform_cur_user_data["value"], 11)

    elif match_type == 'All':
        user_collection = client['personal_project']['user']
        transform_all_user_dict = transform_all_user_collection.find()

        transform_id_list, transform_value_list = get_value_from_user_dict(
            transform_all_user_dict)

        user_active_statuses = user_collection.find(
            {"user_id": {"$in": transform_id_list}},
            # Projection to include only active_status field
            {"active_status": 1, "user_id": 1}
        )

        user_active_status_list = list(user_active_statuses)
        sorted_user_active_status_list = sorted(
            user_active_status_list, key=lambda x: x['active_status'], reverse=True)[:500]

        sorted_user_ids = [user['user_id']
                           for user in sorted_user_active_status_list]

        transform_id_list, transform_value_list = get_value_from_user_dict(transform_all_user_collection.find(
            {"user_id": {"$in": sorted_user_ids}}))

        nearest_neighbors_id_list = match_user(transform_id_list, transform_value_list,
                                               transform_cur_user_data["value"], 11)

    try:
        match_users = user_collection.find(
            {"user_id": {"$in": nearest_neighbors_id_list}})
        matches_data = [[{'user_id': user['user_id'], 'username': user['username']}]
                        for user in match_users if int(user['user_id']) != int(user_id)]

        logger.info(f"-----------------End Search-----------------")
        end_time = datetime.now()
        logger.info(f"Time: {end_time - start_time}")

        logger.info(f"{match_type}: {len(matches_data)}")
    except Exception as e:
        logger.warning("No match users", e)

        '''
            error format 
        '''
        return jsonify({'error': 'No match users'}), 404

    return jsonify(matches_data), 200


def allocate_chat_room():

    chat_user_id = request.json.get('user_id')
    chat_user_name = get_user_name(chat_user_id)

    token = request.cookies.get('token')
    cur_user_id = authentication(token, jwt_secret_key)
    if isinstance(cur_user_id, int):
        cur_username = get_user_name(cur_user_id)

        return jsonify({'cur_user_id': cur_user_id, 'cur_username': cur_username, 'chat_user_id': chat_user_id, 'chat_username': chat_user_name}), 200

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))


def chat(user_id):
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    cur_user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        cur_user = get_user_name(cur_user_id)
        chat_user_name = get_user_name(user_id)
        return render_template('chatroom.html', cur_user=cur_user, cur_user_id=cur_user_id, chat_user_id=user_id, chat_user_name=chat_user_name)

    cur_time = datetime.now()
    logger.warning(f"{cur_time} Login timeout")
    return redirect(url_for('login'))
