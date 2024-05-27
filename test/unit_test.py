import pytest
import os
import numpy as np
from dotenv import load_dotenv
import warnings
from app import app
from utils import calculate_house_metrics, calculate_active_status
from user_model.house_data_process import transform_one_house

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


def test_calculate_house_metrics():
    # Prepare test data
    user_house_transform_dict = {
        'save': [
            [100, 10, 50],
            [200, 20, 60],
            [150, 15, 55]
        ],
        'click': [
            [300, 30, 70],
            [250, 25, 65],
            [350, 35, 75]
        ]
    }

    # Expected results
    expected_lowest_price = (100 * 2 + 250) / 3
    expected_highest_price = (200 * 2 + 350) / 3
    expected_lowest_age = (10 * 2 + 25) / 3
    expected_highest_age = (20 * 2 + 35) / 3
    expected_lowest_size = (50 * 2 + 65) / 3
    expected_highest_size = (60 * 2 + 75) / 3

    # Call the function
    lowest_price, highest_price, lowest_age, highest_age, lowest_size, highest_size = calculate_house_metrics(
        user_house_transform_dict)

    # Assertions
    assert np.isclose(
        lowest_price, expected_lowest_price), f"Expected {expected_lowest_price}, got {lowest_price}"
    assert np.isclose(
        highest_price, expected_highest_price), f"Expected {expected_highest_price}, got {highest_price}"
    assert np.isclose(
        lowest_age, expected_lowest_age), f"Expected {expected_lowest_age}, got {lowest_age}"
    assert np.isclose(
        highest_age, expected_highest_age), f"Expected {expected_highest_age}, got {highest_age}"
    assert np.isclose(
        lowest_size, expected_lowest_size), f"Expected {expected_lowest_size}, got {lowest_size}"
    assert np.isclose(
        highest_size, expected_highest_size), f"Expected {expected_highest_size}, got {highest_size}"


def test_calculate_active_status():
    # Test cases with different input values

    # Test case 1: All activities are zero
    assert calculate_active_status(0, 0, 0, 0, 0) == 0

    # Test case 2: Only one activity has a value
    assert calculate_active_status(1, 0, 0, 0, 0) == 0
    assert calculate_active_status(0, 1, 0, 0, 0) == 0.5
    assert calculate_active_status(0, 0, 1, 0, 0) == 0.2
    assert calculate_active_status(0, 0, 0, 1, 0) == 0.24
    assert calculate_active_status(0, 0, 0, 0, 1) == 0.05

    # Test case 3: All activities have equal values
    assert calculate_active_status(1, 1, 1, 1, 1) == 0.98

    # Test case 4: Random values for activities
    assert calculate_active_status(2, 5, 3, 4, 1) == 4.090000000000001


def test_transform_one_house():
    # Sample house data
    house_data = {
        "_id": {"$oid": "662253af2b1b2f13455e2ff8"},
        "id": 2,
        "title": "近捷運三房美寓(房屋編號：035215)",
        "price": 32800.0,
        "age": 43,
        "size": 28.0,
        "cook": True,
        "pet": "不可",
        "stay_landlord": True,
        "park": False,
        "gender": "男女皆可"
    }

    # Expected transformed data
    expected_row = [32800.0, 43, 28.0, 1, 0, 1, 0, 1, 0, 0]
    expected_house_dict = {"house_id": 2, "value": expected_row}

    # Call the function to transform the house data
    actual_row, actual_house_dict = transform_one_house(house_data)

    # Verify if the transformation is correct
    assert actual_row == expected_row
    assert actual_house_dict == expected_house_dict
