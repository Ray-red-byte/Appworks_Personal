import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import os
from flask import jsonify
import pymongo


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)

# Select a database and collection
db = client["personal_project"]
user_collection = db["user"]
house_collection = db["house"]


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

    expiration_time = datetime.now() + timedelta(seconds=60)
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
