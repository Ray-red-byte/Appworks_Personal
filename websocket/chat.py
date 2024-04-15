import asyncio
import websockets


# WebSocket server communication
connected = set()


async def chat_server(websocket, path):

    # Receive user identifier from client
    user_identifier_data = await websocket.recv()
    user_identifier = user_identifier_data.split(': ')[1].split(')')[0]
    print(user_identifier)

    # Register new client with user identifier
    connected.add((websocket, user_identifier))
    try:
        # Notify all clients about new connection
        for client, _ in connected:
            if client != websocket:  # Don't send the message to the new user
                await client.send(f"User {user_identifier} has joined the chat")

        # Handle messages from client
        async for message in websocket:

            for client, _ in connected:
                if client != websocket:  # Don't send the message back to the sender
                    await client.send(f"{user_identifier}: {message}")
    finally:
        # Unregister client when connection is closed
        connected.remove((websocket, user_identifier))


async def main():
    async with websockets.serve(chat_server, "localhost", 8765):
        await asyncio.Future()  # Keep the server running indefinitely

asyncio.run(main())
