import asyncio
import websockets

connected_clients = {}

async def chat_server(websocket, path):
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
        await asyncio.wait([client.send(message) for client in connected_clients])

start_server = websockets.serve(chat_server, '0.0.0.0', 7000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
