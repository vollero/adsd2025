import socket
import threading

HOST = '127.0.0.1'
PORT = 65432

clients = []  # Lista dei client connessi

def handle_client(conn, addr):
    print(f"Nuovo client connesso: {addr}")
    clients.append(conn)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            broadcast(data, conn)
    finally:
        print(f"Client disconnesso: {addr}")
        clients.remove(conn)
        conn.close()

def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.sendall(message)
            except:
                clients.remove(client)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print("Server di chat in ascolto...")
    
    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()
