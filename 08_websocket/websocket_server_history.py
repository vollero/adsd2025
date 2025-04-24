import asyncio
import websockets

connected_clients = {}

chat_history = []

async def broadcast_message(message):
    """
    Broadcasts a message to all connected clients.
    """
    if connected_clients:
        await asyncio.wait([client.send(message) for client in connected_clients])

async def send_chat_history(websocket):
    """
    Sends the entire chat history to a newly connected client.
    """
    for message in chat_history:
        await websocket.send(message)

async def chat_server(websocket, path):
    """
    Handles incoming WebSocket connections and chat messages.
    """
    try:
        await websocket.send("Please enter your username:")
        username = await websocket.recv()
        
        connected_clients[websocket] = username
        await send_chat_history(websocket)
        join_message = f"System: {username} has joined the chat."
        await broadcast_message(join_message)
        chat_history.append(join_message)

        async for message in websocket:
            b_message = f"{username}: {message}"
            chat_history.append(b_message)
            await broadcast_message(b_message)

    except websockets.ConnectionClosed:
        pass

    finally:
        leave_message = f"System: {username} has left the chat."
        connected_clients.pop(websocket, None)
        await broadcast_message(leave_message)
        chat_history.append(leave_message)

start_server = websockets.serve(chat_server, '0.0.0.0', 7000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
