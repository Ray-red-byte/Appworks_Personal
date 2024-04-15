from flask import Flask, render_template, request, jsonify, make_response
import os
from dotenv import load_dotenv
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
from function import get_user_id, check_exist_user, validate_email, create_token, authentication, get_user_password, get_user_name
from flask_cors import CORS
from flask_socketio import SocketIO


app = Flask(__name__)
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
            return response_data

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

        return jsonify({'message': 'Register is valid'})

    else:
        response_data = {"Error": "Invalid Content-Type"}
        return response_data


# User information page
@ app.route('/user/information', methods=["GET", "POST"])
def user_information():
    # Retrieve the parameters from the query string
    token = request.headers.get("Authorization")

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    username = get_user_name(user_id)

    # Create a response object
    response = make_response()

    # Set the token in the response header
    response.headers["Authorization"] = f"Bearer {token}"
    return render_template('user_information.html', username=username), response


@ app.route('/main')
def main_page():
    # Retrieve the parameters from the query st ring
    token = request.headers.get("Authorization")

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)
    return render_template('main.html', username=user_id)


@socketio.on('message')
def handle_message(message):
    print('Received message: ' + message)
    # Broadcast the message to all connected clients
    socketio.send(message)


@ app.route('/search')
def search():
    # Implement your house search functionality here
    return "Search results will be displayed here"


if __name__ == '__main__':

    socketio.run(app)
    # start_websocket_server()
