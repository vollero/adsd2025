import socket

SOCKET_FILE = "/tmp/uds_socket"

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_socket:
    client_socket.connect(SOCKET_FILE)
    client_socket.sendall(b'Hello, UDS Server!')
    data = client_socket.recv(1024)

print(f"Risposta dal server: {data.decode()}")
