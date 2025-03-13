import socket

HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
    server_socket.bind((HOST, PORT))
    print("Server UDP in ascolto...")
    while True:
        data, addr = server_socket.recvfrom(1024)  # Riceve dati
        print(f"Messaggio ricevuto da {addr}: {data.decode()}")
        server_socket.sendto(data, addr)  # Echo
