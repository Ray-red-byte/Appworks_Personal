import asyncio
import websockets

async def send_message():
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            message = input("Enter message: ")
            await websocket.send(message)

asyncio.run(send_message())
