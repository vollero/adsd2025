import asyncio
import websockets
import uuid
import random

BOARD_SIZE = 16

connected_clients = {}

async def send_to_all(message):
    """
    Broadcasts a message to all connected clients.
    """
    if connected_clients:
        await asyncio.wait([client_data['websocket'].send(message) for client_data in connected_clients.values()])

async def send_initial_positions(websocket):
    """
    Sends the positions of all connected users to a newly connected client.
    """
    for client_id, client_data in connected_clients.items():
        await websocket.send(f"POSITION|{client_id}|{client_data['username']}|{client_data['x']}|{client_data['y']}")

async def send_user_list():
    """
    Broadcasts the list of currently connected users to all clients.
    """
    if connected_clients:
        user_list_message = "USERS:" + "," + ",".join(client_data['username'] for client_data in connected_clients.values())
        await asyncio.wait([client_data['websocket'].send(user_list_message) for client_data in connected_clients.values()])

async def chat_server(websocket, path):
    """
    Handles incoming WebSocket connections and movements on the chessboard.
    """
    try:
        await websocket.send("Please enter your username:")
        username = await websocket.recv()

        client_id = str(uuid.uuid4())
        initial_position = {
            "websocket": websocket,
            "username": username,
            "x": random.randint(0, BOARD_SIZE - 1),
            "y": random.randint(0, BOARD_SIZE - 1)
        }
        connected_clients[client_id] = initial_position

        await send_initial_positions(websocket)
        await send_to_all(f"POSITION|{client_id}|{username}|{initial_position['x']}|{initial_position['y']}")

        await send_user_list()

        async for message in websocket:
            if message.startswith("MOVE|"):
                _, direction = message.split("|")
                current_position = connected_clients[client_id]

                if direction == "UP" and current_position['y'] > 0:
                    current_position['y'] -= 1
                elif direction == "DOWN" and current_position['y'] < BOARD_SIZE - 1:
                    current_position['y'] += 1
                elif direction == "LEFT" and current_position['x'] > 0:
                    current_position['x'] -= 1
                elif direction == "RIGHT" and current_position['x'] < BOARD_SIZE - 1:
                    current_position['x'] += 1

                await send_to_all(f"POSITION|{client_id}|{current_position['username']}|{current_position['x']}|{current_position['y']}")

    except websockets.ConnectionClosed:
        pass

    finally:
        leave_message = f"LEAVE|{client_id}|{connected_clients[client_id]['username']}"
        connected_clients.pop(client_id, None)
        await send_to_all(leave_message)

        await send_user_list()

start_server = websockets.serve(chat_server, '0.0.0.0', 7000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
