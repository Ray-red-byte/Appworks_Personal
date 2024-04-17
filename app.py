from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
import os
from dotenv import load_dotenv
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
from function import get_user_id, check_exist_user, validate_email, create_token, authentication, get_user_password, get_user_name
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room


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


@app.route('/logout')
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


# User information page
@ app.route('/user/information', methods=["GET", "POST"])
def user_information():
    # Retrieve the parameters from the query string
    token = request.cookies.get('token')

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

            return render_template('house_type.html', username=username)

        return redirect(url_for('login'))


@ app.route('/user/routine_insert', methods=["GET", "POST"])
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

            return render_template('house_type.html', username=username)

        return redirect(url_for('login'))


@ app.route('/user/house_type_insert', methods=["GET", "POST"])
def user_house_type_insert():
    if request.method == 'POST':
        # Retrieve the parameters from the query string
        token = request.cookies.get('token')

        # Call the authentication function to verify the token
        user_id = authentication(token, jwt_secret_key)

        if isinstance(user_id, int):

            # Retrieve form data
            price = request.form.get('price')
            house_age = request.form.get('houseAge')
            zone = request.form.get('zone')
            stay_with_landlord = request.form.get('stayWithLandlord')
            park_nearby = request.form.get('park')
            equipment = request.form.getlist('equip')
            furniture = request.form.getlist('furniture')

            username = get_user_name(user_id)
            user_collection = client['personal_project']['user']

            # Create a dictionary to represent the document to be inserted
            house_preference = {
                'price': price,
                'house_age': house_age,
                'zone': zone,
                'stay_with_landlord': stay_with_landlord,
                'park_nearby': park_nearby,
                'equipment': equipment,
                'furniture': furniture
            }

            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'house_preference': house_preference}}
            )

            return redirect(url_for('main_page'))

        return redirect(url_for('login'))


@app.route('/matches', methods=['GET'])
def get_matches():
    # Get all users from mongodb
    db = client["personal_project"]
    user_collection = db["user"]

    # Get all users from the user collection
    projection = {'_id': 0, 'user_id': 1, 'username': 1}
    users = user_collection.find({}, projection)

    matches_data = [{'user_id': user['user_id'], 'username': user['username']}
                    for user in users]

    '''
     Think some algorithm to match user
    '''

    return jsonify(matches_data), 200

# Route to enter chat room with a specific user


@app.route('/allocate_chat_room', methods=['POST'])
def allocate_chat_room():

    chat_user_id = request.json.get('user_id')
    print(chat_user_id)
    return {'user_id': chat_user_id}


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


@ app.route('/main')
def main_page():
    token = request.cookies.get('token')

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    if isinstance(user_id, int):
        username = get_user_name(user_id)
        return render_template('main.html', username=username, user_id=user_id)

    return redirect(url_for('login'))


# ------------------------Show online users------------------------
online_users = []


@socketio.on('online')
def handle_online(data):
    user_id = data['user_id']
    online_users.append(user_id)
    print("add", user_id)
    emit('show', online_users, broadcast=True)


@socketio.on('offline')
def handle_offline(data):
    user_id = data['user_id']
    online_users.remove(user_id)
    print("remove", user_id)
    emit('hide', user_id, broadcast=True)

# ------------------------Show online users------------------------

# ----------------------------Testing--------------------------------


room_messages = {}


@socketio.on('join_room')
def on_join(data):
    user_id = data['user_id']
    room_id = data['room_id']
    join_room(room_id)

    previous_messages = room_messages.get(room_id, [])
    print(room_id)
    emit('message', {"message": 'joined the room.',
         "recipientId": None, 'senderId': None}, room=room_id)


@socketio.on('leave')
def on_leave(data):
    username = data['userId1']
    room_id = data['roomId']
    leave_room(room_id)
    print(f'{username} has left the room.')
    emit('message', {"message": 'eft the room.',
         "recipientId": None, 'senderId': None}, room=room_id)


@socketio.on('send_message')
def handle_message(data):
    senderId = data['senderId']
    recipientId = data['recipientId']
    room = data['room']
    message = data['message']
    print(senderId, ':', message)
    room_messages.setdefault(room, []).append(message)
    emit('message', {'senderId': senderId,
         "recipientId": recipientId, 'message': message}, room=room)


# ----------------------------Testing--------------------------------
'''
# Dictionary to store users in each room
rooms = {}


@ socketio.on('join_room')
def handle_join_room(data):

    user_id = data['user_id']
    room_id = data['room_id']

    # Add user to the room
    if room_id not in rooms:
        rooms[room_id] = [user_id]
    else:
        rooms[room_id].append(user_id)


@ socketio.on('new_message')
def handle_message(data):

    sender_id = data['senderId']
    recipient_id = data['recipientId']
    message = data['message']

    print(sender_id, recipient_id, message)

    # Check if both sender and recipient are in the same room

    for room_id, users in rooms.items():
        # if both user in the same room
        if sender_id in users and recipient_id in users:
            # Broadcast the message only to users in the same room
            emit('chat', {'senderId': sender_id,
                 'message': message, 'room_id': room_id}, broadcast=True)


@ socketio.on('leave_room')
def handle_leave_room(data):
    user_id = data['user_id']
    room_id = data['room_id']

    # Remove user from the room
    if room_id in rooms:
        rooms[room_id].remove(user_id)
        if len(rooms[room_id]) == 0:
            del rooms[room_id]
'''


@ app.route('/search')
def search():
    # Implement your house search functionality here
    return "Search results will be displayed here"


if __name__ == '__main__':

    socketio.run(app)
    # start_websocket_server()
