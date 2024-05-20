from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
from utils import get_user_name
import logging
import os


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

log_filename = os.getenv("APP_LOG_FILE_NAME")
log_file_path = os.getenv("APP_LOG_FILE_PATH")
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path,
                    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


# ------------------------Show online users------------------------
online_users = []


def handle_online(data):
    user_id = data['user_id']
    if user_id not in online_users and user_id is not None:
        online_users.append(user_id)
    logger.info(f"{online_users} is online")
    emit('show', online_users, broadcast=True)


def handle_offline(data):
    user_id = data['user_id']
    online_users.remove(user_id)
    logger.info(f"{online_users} is remove")
    emit('hide', user_id, broadcast=True)

# ------------------------Show online users------------------------


room_count = {}


def on_join(data):
    user_id = data['user_id']
    username = get_user_name(int(user_id))
    logger.info(f"new user join room {username}")
    room_id = data['room_id']
    join_room(room_id)
    room_count.setdefault(room_id, 0)
    room_count[room_id] += 1

    logger.info(f'{username} has join {room_id} the room.')

    emit('message', {'senderId': username,
                     "recipientId": "None",  "message": 'joined the room.', 'room_status': "join room"}, room=room_id)


def on_leave(data):
    user_id = data['userId1']
    username = get_user_name(int(user_id))
    room_id = data['roomId']

    room_count[room_id] -= 1
    user_count = room_count[room_id]

    # if the last one leave the room

    logger.info(f'{username} has left the {room_id} room.')
    if user_count == 0:
        logger.info("last user left the room.")

    emit('message', {'senderId': username,
                     "recipientId": "None",  "message": 'leave  room.', 'room_status': "leave_room"}, room=room_id)
    leave_room(room_id)


def handle_message(data):
    senderId = data['senderId']
    recipientId = data['recipientId']
    room_id = data['room']
    message = data['message']

    logger.info(f"{senderId} : {message}")

    # Get all users from the room_id
    total_user = len(room_id.split("_"))
    user_count = room_count[room_id]

    emit('message', {'senderId': senderId,
                     'recipientId': recipientId, 'message': message, 'room_status': "save_messages"}, room=room_id)
