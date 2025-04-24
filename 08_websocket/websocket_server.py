import asyncio
import websockets

connected_clients = set()

async def chat_server(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            await asyncio.wait([client.send(message) for client in connected_clients])
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

start_server = websockets.serve(chat_server, '0.0.0.0', 7000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
