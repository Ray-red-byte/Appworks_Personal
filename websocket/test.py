import asyncio
import websockets

# Store connected clients
connected = set()

async def chat_server(websocket, path):
    # Register new client
    connected.add(websocket)
    try:
        async for message in websocket:
            # Broadcast message to all clients
            for client in connected:
                if client != websocket:  # Don't send the message back to the sender
                    await client.send(message)
            print("Received:", message)
            
    finally:
        # Unregister client when connection is closed
        connected.remove(websocket)

async def main():
    async with websockets.serve(chat_server, "localhost", 8765):
        await asyncio.Future()  # Keep the server running indefinitely

asyncio.run(main())
