import socket

HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
    message = b'Hello, UDP Server!'
    client_socket.sendto(message, (HOST, PORT))
    data, server = client_socket.recvfrom(1024)

print(f"Risposta dal server: {data.decode()}")
