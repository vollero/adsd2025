import asyncio
import websockets

connected_clients = {}

async def chat_server(websocket):
    await websocket.send("Please enter your username:")
    username = await websocket.recv()
    connected_clients[websocket] = username
    await broadcast_message(f"System: {username} has joined the chat.")

    try:
        async for message in websocket:
            await broadcast_message(f"{username}: {message}")
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.pop(websocket, None)
        await broadcast_message(f"System: {username} has left the chat.")

async def broadcast_message(message):
    if connected_clients:
        websockets.broadcast(set(connected_clients.keys()), message)

async def main():
    async with websockets.serve(chat_server, '0.0.0.0', 7000):
        await asyncio.Future()  # Keeps server running

if __name__ == "__main__":
    asyncio.run(main())

