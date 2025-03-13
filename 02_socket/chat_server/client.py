import socket
import threading

HOST = '127.0.0.1'
PORT = 65432

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if not message:
                break
            print("\nMessaggio ricevuto:", message)
        except:
            break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    
    while True:
        message = input("Tu: ")
        if message.lower() == "exit":
            break
        client_socket.sendall(message.encode())
