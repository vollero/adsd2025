import asyncio
import websockets

connected_clients = set()

async def chat_server(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            websockets.broadcast(connected_clients, message)
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients(websocket)

async def main():
    async with websockets.serve(chat_server, "0.0.0.0", 7000):
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
