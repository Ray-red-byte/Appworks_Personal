from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    print(room)
    join_room(room)
    emit('message', f'{username} has joined the room.', room=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('message', f'{username} has left the room.', room=room)


@socketio.on('send_message')
def handle_message(data):
    username = data['username']
    room = data['room']
    message = data['message']
    emit('message', {'username': username, 'message': message}, room=room)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app)
