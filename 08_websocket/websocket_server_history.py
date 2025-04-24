import asyncio
import websockets

connected_clients = {}
chat_history = []

async def broadcast_message(message):
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

async def chat_server(websocket):
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
        leave_message = f"System: {connected_clients.get(websocket, 'A user')} has left the chat."
        connected_clients.pop(websocket, None)
        await broadcast_message(leave_message)
        chat_history.append(leave_message)

async def main():
    async with websockets.serve(chat_server, "0.0.0.0", 7000):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())

