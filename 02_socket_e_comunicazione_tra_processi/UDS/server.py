import socket
import os

SOCKET_FILE = "/tmp/uds_socket"

# Rimuove il file socket precedente se esiste
if os.path.exists(SOCKET_FILE):
    os.remove(SOCKET_FILE)

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
    server_socket.bind(SOCKET_FILE)  # Associa la socket a un file
    server_socket.listen()
    print("Server UDS in ascolto...")
    conn, _ = server_socket.accept()
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)  # Echo
