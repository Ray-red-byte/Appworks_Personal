import jwt
from datetime import datetime, timedelta
import re
import os
from flask import jsonify
import pymongo


# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)

# Select a database and collection
db = client["personal_project"]
collection = db["user"]


def check_exist_row(table_name, column, search_data):
    try:
        product_id = DB.check_exist_row(
            table_name, column, search_data)[0]["id"]
    except IndexError:
        product_id = ""

    return product_id


def validate_email(email):
    email_pattern = re.compile(
        r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    if email_pattern.match(email):
        return True
    return False


# Custom function to create JWT toke
def create_token(user_id, jwt_secret_key):
    # Token expires in 1 minutes
    expiration_time = datetime.now() + timedelta(seconds=600)
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