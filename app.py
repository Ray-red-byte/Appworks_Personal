from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
import os
import re
from dotenv import load_dotenv
from datetime import datetime
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
from function import get_user_id, check_exist_user, validate_email, create_token, authentication, get_user_password, get_user_name
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from user_model.user_data_process import transform_one_user, transform_all_user, match_ten_user, get_value_from_dict


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET')
CORS(app)

socketio = SocketIO(app)

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

# JWT secret key
jwt_secret_key = os.getenv('JWT_SECRET_KEY')


# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('token', '', expires=0)
    return response


@app.route('/user/login_token', methods=['POST'])
def login_token():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')

        if content_type != 'application/json':
            return jsonify({'error': 'wrong Content-type'}, 400)

        form_data = request.get_json()
        user_name = form_data["username"]
        user_login_password = form_data["password"]
        user_email = form_data["email"]

        if not validate_email(user_email):
            response_data = {"Error": 'Invalid email'}
            return response_data, 400

        # Get user_id then get password from MongoDB
        user_id = get_user_id(user_name, user_email)
        if user_id:
            user_password = get_user_password(user_id)
        else:
            response_data = {"Error": 'Invalid username or email'}
            return response_data, 400

        # Check if password is correct
        if not check_password_hash(user_password, user_login_password):
            response_data = {"Error": 'Invalid password'}
            return response_data, 400

        token = create_token(user_id, jwt_secret_key)

        # Create a response object
        response = make_response()

        # Set the token in the response header
        response.headers["Authorization"] = f"Bearer {token}"
        return response, 200

    else:

        response_data = {"Error": "Invalid Content-Type"}
        return response_data, 400


@app.route('/register')
def register():
    return render_template('register.html')


def get_next_user_id():
    # Find and update the user_id counter
    counter_doc = client['personal_project']['user'].counters.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,  # Create the counter if it doesn't exist
        return_document=True
    )
    return counter_doc["seq"]


@app.route("/user/register_validate", methods=['GET', 'POST'])
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

        # Isnert into mongoDB
        user_info = {
            "user_id": user_id,
            "username": user_name,
            "email": user_email,
            "password": hashed_password
        }
        user_collection = client['personal_project']['user']

        user_collection.insert_one(user_info)

        return jsonify({'message': 'Register is valid'}), 200

    else:
        response_data = {"Error": "Invalid Content-Type"}
        return response_data, 400


# -------------------------------------------------------User information page-------------------------------------------------------
@ app.route('/user/information', methods=["GET", "POST"])
def user_information():
    # Retrieve the parameters from the query string
    token = request.cookies.get('token')

    print("-----------------User information page-----------------")

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('user_information.html', username=username)

    return redirect(url_for('login'))


@ app.route('/user/info_insert', methods=["GET", "POST"])
def user_info_insert():

    if request.method == 'POST':
        # Retrieve the parameters from the query string
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

        return redirect(url_for('login'))
# -------------------------------------------------------User information page-------------------------------------------------------


# -------------------------------------------------------User routine page-------------------------------------------------------
@ app.route('/user/routine_insert', methods=["GET", "POST"])
def user_routine_insert():

    if request.method == 'POST':
        # Retrieve the parameters from the query string
        token = request.cookies.get('token')

        # Call the authentication function to verify the token
        user_id = authentication(token, jwt_secret_key)

        if isinstance(user_id, int):
            print(user_id)

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
            print(routine_data)

            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'routine': routine_data}}
            )

            return redirect(url_for('house_type_page'))

        return redirect(url_for('login'))

# -------------------------------------------------------User routine page-------------------------------------------------------


# -------------------------------------------------------User house type page-------------------------------------------------------
@app.route('/user/furniture_insert', methods=["GET", "POST"])
def furniture_insert():
    # Retrieve the parameters from the query string
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        equipment = request.form.getlist('equip')
        furniture = request.form.getlist('furniture')

        user_collection = client['personal_project']['user']

        furniture_preference = {
            'equipment': equipment,
            'furniture': furniture
        }

        user_collection.update_one(
            {'user_id': user_id},
            {'$set': {'furniture_preference': furniture_preference}}
        )
        print("house type saved successfully")
        return redirect(url_for('main_page'))

    return redirect(url_for('login'))


@ app.route('/user/filter', methods=["GET", "POST"])
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

        return redirect(url_for('login'))


@app.route('/save_house', methods=["GET", "POST"])
def save_hosue():
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if request.method == 'POST':
        data = request.get_json()
        house_id = data.get('save_house')

        print('house_id', house_id)

        if house_id is None:
            return jsonify({'error': 'House ID not provided'}), 400

        save_house_ls = []
        if isinstance(user_id, int):
            user_collection = client['personal_project']['user']
            cur_user = user_collection.find_one({"user_id": user_id})
            cur_user_save_house_ls = cur_user.get('saved_house', [])

            if house_id not in cur_user_save_house_ls:
                save_house_ls.append(house_id)

            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'saved_house': save_house_ls}},
                upsert=True
            )
            print("-------------------------------", cur_user_save_house_ls)
            return "House saved successfully", 200


translations = {
    "basic_info": "基本資訊",
    "house_preference": "房屋偏好",
    "price": "價格",
    "house_age": "房屋年齡",
    "zone": "區域",
    "stay_with_landlord": "與房東同住",
    "park_nearby": "附近有公園",
    "equipment": "設備",
    "Internet": "網路",
    "cableTV": "有線電視",
    "washingMachine": "洗衣機",
    "dryer": "烘乾機",
    "dryingMachine": "乾衣機",
    "waterDispenser": "飲水機",
    "waterFilter": "淨水器",
    "lcdTV": "電視",
    "refrigerator": "冰箱",
    "microwave": "微波爐",
    "gasStove": "瓦斯爐",
    "naturalGas": "天然瓦斯",
    "inductionCooker": "電磁爐",
    "electricFan": "電風扇",
    "oven": "烤箱",
    "furniture": "家具",
    "wardrobe": "衣櫃",
    "diningTable": "餐桌",
    "diningChair": "餐椅",
    "singleBed": "單人床",
    "doubleBed": "雙人床",
    "desk": "桌子",
    "chair": "椅子",
    "sofa": "沙發",
    "routine": "例行公事",
    "petOptions": "寵物選項"
}


@app.route('/search/hot', methods=['GET'])
def search_hot():

    # First get user's house preference
    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    if not user_id:
        return redirect(url_for('login'))

    house_collection = client['personal_project']['house']
    top_houses = list(house_collection.find().sort([('click', -1)]).limit(10))
    top_houses_json = [
        {**house, '_id': str(house['_id'])}  # Convert ObjectId to string
        for house in top_houses
    ]

    print(top_houses_json)

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


# Change method to POST since you're sending data
@app.route('/search', methods=['GET'])
def search():
    # Retrieve the parameters from the query string
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        print("user", user_id)
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
        print(search_houses_json)

        # You may want to process the matching houses list further or send it directly to the frontend

        return jsonify(search_houses_json), 200

# -------------------------------------------------------User house type page-------------------------------------------------------

# ------------------------------------------------------Track user click house------------------------------------------------------


@ app.route('/track/hot/click', methods=['POST'])
def track_hot_click():
    house_id = request.json.get('house_id')

    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)
    print("click", house_id)
    # Insert into MongoDB
    house_collection = client['personal_project']['house']
    print(type(house_id))
    house_collection.update_one(
        {'id': int(house_id)},
        {'$inc': {'click': 1}},
        upsert=True
    )

    return "Click tracked", 200


@ app.route('/track/search/click', methods=['POST'])
def track_search_click():
    house_id = request.json.get('house_id')

    token = request.cookies.get('token')
    user_id = authentication(token, jwt_secret_key)

    # Insert into MongoDB
    house_collection = client['personal_project']['house']
    house_collection.update_one(
        {'id': int(house_id)},
        {'$inc': {'click': 1}},
        upsert=True
    )

    return "Click tracked", 200
# ------------------------------------------------------Track user click house------------------------------------------------------

# ------------------------------------------------------Get user house------------------------------------------------------


@ app.route('/user/house/<int:house_id>', methods=['GET'])
def get_user_house(house_id):
    house_collection = client['personal_project']['house']
    house = house_collection.find_one({"id": house_id})
    if house:
        # Convert ObjectId to string
        search_house_json = {**house, '_id': str(house['_id'])}
        return jsonify(search_house_json), 200
    return jsonify({'error': 'House not found'}), 404
# ------------------------------------------------------Get user house------------------------------------------------------


@ app.route('/matches/<string:match_type>', methods=['GET'])
def get_matches(match_type):

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
        print(e)
        return jsonify({'error': 'No match'}), 500

    # No matter what transform first
    row, transform_cur_user_dat_dict = transform_one_user(cur_user)
    transform_all_user_collection.update_one(
        {"user_id": int(user_id)},
        {"$set": transform_cur_user_dat_dict},
        upsert=True)

    # Get all users from the user collection and share one or more zones with the current user
    transform_cur_user_data = transform_all_user_collection.find_one(
        {"user_id": int(user_id)})

    print("-----------------Start Search-----------------")

    if match_type == 'zone':
        users_share_zone = user_collection.find(
            {"house_preference.zone": {"$in": user_prefer_zone}})

        print('users_share_zone', users_share_zone)

        # Find users who share the same zone with the current user in the transform_all_user_collection
        transform_select_user_data_dicts = []

        for user in users_share_zone:
            user_id = user["user_id"]
            transform_user_data = transform_all_user_collection.find_one(
                {"user_id": int(user_id)})
            if transform_user_data:
                transform_select_user_data_dicts.append(transform_user_data)

        print("Selected users", len(transform_select_user_data_dicts))
        transform_id_list, transform_value_lis = get_value_from_dict(
            transform_select_user_data_dicts)

        nearest_neighbors_id_list = match_ten_user(transform_id_list, transform_value_lis,
                                                   transform_cur_user_data["value"])

    else:
        transform_all_user_dict = transform_all_user_collection.find()

        transform_id_list, transform_value_list = get_value_from_dict(
            transform_all_user_dict)

        nearest_neighbors_id_list = match_ten_user(transform_id_list, transform_value_list,
                                                   transform_cur_user_data["value"])

    try:
        match_users = user_collection.find(
            {"user_id": {"$in": nearest_neighbors_id_list}})
        matches_data = [[{'user_id': user['user_id'], 'username': user['username']}]
                        for user in match_users]

    except Exception as e:
        print(e)
        return jsonify({'error': 'No match'}), 500

    return jsonify(matches_data), 200

# Route to enter chat room with a specific user


@ app.route('/allocate_chat_room', methods=['GET', 'POST'])
def allocate_chat_room():

    chat_user_id = request.json.get('user_id')
    chat_user_name = get_user_name(chat_user_id)

    token = request.cookies.get('token')
    cur_user_id = authentication(token, jwt_secret_key)
    if isinstance(cur_user_id, int):
        cur_username = get_user_name(cur_user_id)

        return jsonify({'cur_user_id': cur_user_id, 'cur_username': cur_username, 'chat_user_id': chat_user_id, 'chat_username': chat_user_name}), 200
    return redirect(url_for('login'))


@ app.route('/chat/<int:user_id>')
def chat(user_id):
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    cur_user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        cur_user = get_user_name(cur_user_id)
        chat_user_name = get_user_name(user_id)
        return render_template('chatroom.html', cur_user=cur_user, cur_user_id=cur_user_id, chat_user_id=user_id, chat_user_name=chat_user_name)

    return redirect(url_for('login'))

# ------------------------------------- Render template-------------------------------------


@ app.route('/main')
def main_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('main.html', username=username, user_id=user_id)

    return redirect(url_for('login'))


@ app.route('/routine')
def routine_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('routine.html', username=username)

    return redirect(url_for('login'))


@ app.route('/house_type')
def house_type_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        print("house type page")
        username = get_user_name(user_id)
        return render_template('house_type.html', username=username)

    return redirect(url_for('login'))


@ app.route('/user/house_detail/<int:houseId>')
def house_detail(houseId):
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)
    print("get house detail")
    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('house_detail.html', username=username, houseId=houseId)

    return redirect(url_for('login'))

# ------------------------------------- Render template-------------------------------------


@ app.route('/chat_history', methods=['GET', 'POST'])
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


@ app.route('/save/messages', methods=['POST'])
def save_messages():
    room_collection = client['personal_project']['room']

    messages = request.json.get('messages')
    room_id = request.json.get('room_id')
    user_id = request.json.get('user_id')

    print("only one user save messages", messages)

    # Insert messages into MongoDB
    try:
        timestamp = datetime.now()
        room_collection.update_one(
            {'room_id': room_id},
            {'$set': {'last_updated_by': user_id,
                      'messages': messages, 'timestamp': timestamp}},
            upsert=True  # Create a new document if no matching document is found
        )

        print(room_id, "save messages successfully")
        return jsonify({'success': True, 'message': 'Messages saved successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Failed to save messages'}), 500


@ app.route('/get/messages', methods=['POST'])
def get_messages():
    room_id = request.json.get('room_id')
    room_collection = client['personal_project']['room']
    room = room_collection.find_one({"room_id": room_id})

    print("Get messages from room", room_id)

    if room:
        messages = room['messages']
        print("messages", messages)
        last_updated_user_id = room['last_updated_by']
        return jsonify({'messages': messages, 'last_updated_by': last_updated_user_id}), 200

    return jsonify({'error': 'Room not found'}), 404


# ------------------------Show online users------------------------
online_users = []


@ socketio.on('online')
def handle_online(data):
    user_id = data['user_id']
    online_users.append(user_id)
    print("online", user_id)
    emit('show', online_users, broadcast=True)


@ socketio.on('offline')
def handle_offline(data):
    user_id = data['user_id']
    online_users.remove(user_id)
    print("remove", user_id)
    emit('hide', user_id, broadcast=True)

# ------------------------Show online users------------------------


room_count = {}


@ socketio.on('join_room')
def on_join(data):
    user_id = data['user_id']
    username = get_user_name(int(user_id))
    print("new user", username)
    room_id = data['room_id']
    join_room(room_id)
    room_count.setdefault(room_id, 0)
    room_count[room_id] += 1

    print(f'{username} has join {room_id} the room.')

    emit('message', {'senderId': username,
                     "recipientId": "None",  "message": 'joined the room.', 'room_status': "join room"}, room=room_id)


@ socketio.on('leave')
def on_leave(data):
    user_id = data['userId1']
    username = get_user_name(int(user_id))
    room_id = data['roomId']

    room_count[room_id] -= 1
    user_count = room_count[room_id]

    # if the last one leave the room

    print(f'{username} has left the {room_id} room.')
    if user_count == 0:
        print("last user left the room.")

    emit('message', {'senderId': username,
                     "recipientId": "None",  "message": 'leave  room.', 'room_status': "leave_room"}, room=room_id)
    leave_room(room_id)


@ socketio.on('send_message')
def handle_message(data):
    senderId = data['senderId']
    recipientId = data['recipientId']
    room_id = data['room']
    message = data['message']
    print(senderId, ':', message)

    # Get all users from the room_id
    total_user = len(room_id.split("_"))
    user_count = room_count[room_id]

    emit('message', {'senderId': senderId,
                     'recipientId': recipientId, 'message': message, 'room_status': "save_messages"}, room=room_id)


if __name__ == '__main__':

    socketio.run(app)
