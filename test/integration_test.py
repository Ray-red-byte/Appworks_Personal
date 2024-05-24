import pytest
import requests
import os
from dotenv import load_dotenv
import pymongo
import warnings
import json
from app import app
from utils import authentication, create_token


# Suppress pymongo deprecation warnings
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="pymongo.srv_resolver")


# Mongo atlas
dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
TEST_MONGO_URI = os.getenv("MONGO_ATLAS_USER")


@ pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@ pytest.fixture
def set_test_db():
    # Use the test database for the duration of the test
    app.config['MONGO_URI'] = TEST_MONGO_URI
    yield


def test_get_user_recommend_house(client, set_test_db):
    # Set up a valid token for authentication
    valid_token = create_token(8, JWT_SECRET_KEY)

    # Set a test house_id that exists in your test database
    test_house_id = 1

    # Set a cookie with the valid token
    client.set_cookie('localhost', 'token', valid_token)

    # Make a request to your endpoint

    response = client.get(f'/user/house/recommend/{test_house_id}')

    print("Status Code:", response.status_code)
    print("Response Data:", response.get_data(as_text=True))

    # Verify the response
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)
    assert 'house_id' in data[0]
    assert 'title' in data[0]
    assert 'price' in data[0]


def test_ai_recommend(client, set_test_db):
    # Generate a valid token for authentication
    valid_token = create_token(8, JWT_SECRET_KEY)

    # Set a cookie with the valid token for the request
    client.set_cookie('localhost', 'token', valid_token)

    response = client.get('/ai_recommend')

    # Print the response status and data for debugging
    print("Status Code:", response.status_code)
    print("Response Data:", response.get_data(as_text=True))

    # Verify the response status code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    # Verify the response data
    data = response.get_json()
    print("Parsed JSON Data:", data)  # Debugging the parsed JSON response

    assert isinstance(
        data, list), f"Expected response to be a list, got {type(data)}"
    assert 'id' in data[0], "Expected 'house_id' in response data"
    assert 'address' in data[0], "Expected 'title' in response data"
    assert 'price' in data[0], "Expected 'price' in response data"


def test_get_matches_zone(client, set_test_db):

    # Create a valid token and set it as a cookie
    valid_token = create_token(8, JWT_SECRET_KEY)
    client.set_cookie('localhost', 'token', valid_token)

    response = client.get('/matches/zone')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
