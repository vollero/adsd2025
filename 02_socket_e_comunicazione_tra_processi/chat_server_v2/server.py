import socket
import threading

HOST = '127.0.0.1'
PORT = 65432
clients = {}  # Dizionario per gestire i client (id: connessione)
id_counter = 1  # Contatore per assegnare ID univoci ai client
lock = threading.Lock()

def handle_client(client_socket, client_id):
    global clients
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            
            if data.strip().upper() == "LIST":
                client_socket.sendall(f"Utenti connessi: {list(clients.keys())}".encode())
                continue
            
            parts = data.split(" ", 1)
            if len(parts) != 2:
                client_socket.sendall(b"Formato messaggio non valido. Usa: <ID> <messaggio>")
                continue
            
            target_id, message = parts
            try:
                target_id = int(target_id)
            except ValueError:
                client_socket.sendall(b"ID destinatario non valido.")
                continue
            
            if target_id == 0:
                broadcast_message(f"{client_id}: {message}", client_id)
            elif target_id in clients:
                send_direct_message(f"[Privato da {client_id}]: {message}", target_id)
            else:
                client_socket.sendall(b"ID destinatario non trovato.")
    finally:
        with lock:
            del clients[client_id]
        print(f"Client {client_id} disconnesso.")
        client_socket.close()

def broadcast_message(message, sender_id):
    with lock:
        for client_id, conn in clients.items():
            if client_id != sender_id:
                try:
                    conn.sendall(message.encode())
                except:
                    del clients[client_id]

def send_direct_message(message, target_id):
    with lock:
        if target_id in clients:
            try:
                clients[target_id].sendall(message.encode())
            except:
                del clients[target_id]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print("Server di chat in ascolto...")
    
    while True:
        conn, addr = server_socket.accept()
        with lock:
            client_id = id_counter
            id_counter += 1
            clients[client_id] = conn
        
        print(f"Nuovo client connesso: {client_id}")
        conn.sendall(f"Il tuo ID è {client_id}".encode())
        threading.Thread(target=handle_client, args=(conn, client_id)).start()
