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
            print("\n", message)
        except:
            break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    client_id = client_socket.recv(1024).decode()
    print(client_id)
    
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    
    while True:
        command = input("(ID Messaggio / LIST per elenco utenti): ")
        client_socket.sendall(command.encode())
        if command.lower() == "exit":
            break
