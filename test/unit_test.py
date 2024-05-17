import pytest
from unittest.mock import patch, MagicMock
from app import app  # Make sure your Flask app is imported correctly


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    with patch('app.client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_auth():
    with patch('app.authentication') as mock_authentication:
        yield mock_authentication


def test_get_matches_success(client, mock_db, mock_auth):
    mock_auth.return_value = '123'  # Mock authenticated user_id

    # Mock current user data
    mock_db["personal_project"]["user"].find_one.return_value = {
        "user_id": 123,
        "house_preference": {"zone": ["Zone1", "Zone2"]},
        "basic_info": {"gender": "male"}
    }

    # Mock transformed user data
    mock_db["personal_project"]["transform_all_user"].find_one.return_value = {
        "user_id": 123,
        "value": [0.1, 0.2, 0.3]
    }

    # Mock users sharing the same zone
    mock_db["personal_project"]["user"].find.return_value = [
        {"user_id": 234},
        {"user_id": 345}
    ]

    # Mock transformed users sharing the same zone
    mock_db["personal_project"]["transform_all_user"].find.return_value = [
        {"user_id": 234, "value": [0.4, 0.5, 0.6]},
        {"user_id": 345, "value": [0.7, 0.8, 0.9]}
    ]

    # Mock user active statuses
    mock_db["personal_project"]["user"].find.return_value = [
        {"user_id": 234, "active_status": 10},
        {"user_id": 345, "active_status": 20}
    ]

    # Call the endpoint
    response = client.get('/matches/zone')

    # Verify the response
    assert response.status_code == 200
    assert response.json == [
        {'user_id': 234, 'username': 'username234'},
        {'user_id': 345, 'username': 'username345'}
    ]


def test_get_matches_no_match(client, mock_db, mock_auth):
    mock_auth.return_value = '123'  # Mock authenticated user_id

    # Mock current user data
    mock_db["personal_project"]["user"].find_one.return_value = {
        "user_id": 123,
        "house_preference": {"zone": ["Zone1", "Zone2"]},
        "basic_info": {"gender": "male"}
    }

    # Mock transformed user data
    mock_db["personal_project"]["transform_all_user"].find_one.return_value = {
        "user_id": 123,
        "value": [0.1, 0.2, 0.3]
    }

    # Mock no users sharing the same zone
    mock_db["personal_project"]["user"].find.return_value = []

    # Call the endpoint
    response = client.get('/matches/zone')

    # Verify the response
    assert response.status_code == 500
    assert response.json == {'error': 'No match'}


def test_get_matches_invalid_token(client, mock_db, mock_auth):
    mock_auth.side_effect = Exception("Invalid token")  # Mock invalid token

    # Call the endpoint
    response = client.get('/matches/zone')

    # Verify the response
    assert response.status_code == 500
    assert response.json == {'error': 'No match'}
