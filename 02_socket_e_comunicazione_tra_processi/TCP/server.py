import socket

HOST = '127.0.0.1'  # Indirizzo locale
PORT = 65432        # Porta di ascolto

# Creazione della socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))  # Associa la socket all'indirizzo
    server_socket.listen()            # Mette il server in ascolto
    print("Server in ascolto...")
    conn, addr = server_socket.accept()  # Accetta connessioni
    with conn:
        print(f"Connessione stabilita con {addr}")
        while True:
            data = conn.recv(1024)  # Riceve dati dal client
            if not data:
                break
            conn.sendall(data)  # Invia i dati ricevuti (echo)
