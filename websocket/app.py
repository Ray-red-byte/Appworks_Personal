from flask import Flask, render_template
import asyncio
import threading
import websockets

app = Flask(__name__)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    # Implement your house search functionality here
    return "Search results will be displayed here"


# WebSocket server communication
connected = set()

async def chat_server(websockets, path):
    # Register new client
    connected.add(websockets)
    try:
        # Notify all clients about new connection
        for client in connected:
            await client.send("A new user has joined the chat")

        # Handle messages from client
        async for message in websockets:
            # Broadcast message to all clients
            for client in connected:
                await client.send(message)
    finally:
        # Unregister client when connection is closed
        connected.remove(websockets)


def start_websocket_server():
    start_server = websockets.serve(chat_server, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


# Start WebSocket server
start_server = websockets.serve(chat_server, "localhost", 8765)

if __name__ == '__main__':

    # Start WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.daemon = True
    websocket_thread.start()

    # Start Flask server
    app.run(port=5000)
