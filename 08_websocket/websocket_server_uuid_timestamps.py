import asyncio
import websockets
import uuid
from datetime import datetime

connected_clients = {}
chat_history = []

async def send_to_all(message):
    """
    Broadcasts a message to all connected clients.
    """
    if connected_clients:
        websockets.broadcast(set(connected_clients.keys()), message)

async def send_chat_history(websocket):
    """
    Sends the entire chat history to a newly connected client.
    """
    for message in chat_history:
        await websocket.send(message)

async def send_user_list():
    """
    Broadcasts the list of currently connected users to all clients.
    """
    if connected_clients:
        user_list_message = "USERS:" + "," + ",".join(connected_clients.values())
        websockets.broadcast(set(connected_clients.keys()), user_list_message)

async def chat_server(websocket):
    """
    Handles incoming WebSocket connections and chat messages.
    """
    try:
        await websocket.send("Please enter your username:")
        username = await websocket.recv()

        connected_clients[websocket] = username
        await send_chat_history(websocket)

        join_message = f"{uuid.uuid4()}|System|{datetime.now().isoformat()}|{username} has joined the chat."
        chat_history.append(join_message)
        await send_to_all(join_message)

        await send_user_list()

        async for message in websocket:
            chat_message = f"{uuid.uuid4()}|{username}|{datetime.now().isoformat()}|{message}"
            chat_history.append(chat_message)
            await send_to_all(chat_message)

    except websockets.ConnectionClosed:
        pass

    finally:
        leave_message = f"{uuid.uuid4()}|System|{datetime.now().isoformat()}|{username} has left the chat."
        connected_clients.pop(websocket, None)
        chat_history.append(leave_message)
        await send_to_all(leave_message)

        await send_user_list()

async def main():
    async with websockets.serve(chat_server, '0.0.0.0', 7000):
        await asyncio.Future()  # Keep the server running forever

if __name__ == "__main__":
    asyncio.run(main())

