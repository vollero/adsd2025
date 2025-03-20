import socket
import json
import time
import threading
from collections import defaultdict, deque

class MessageQueueServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        
        # Dizionario che mappa topic a code di messaggi
        self.topics = defaultdict(deque)
        
        # Dizionario che mappa client (indirizzo) a sottoscrizioni
        self.subscriptions = defaultdict(set)
        
        # Flag per controllo esecuzione server
        self.running = False
    
    def start(self):
        """Avvia il server di message queue."""
        self.running = True
        print(f"Server avviato su {self.host}:{self.port}")
        
        try:
            while self.running:
                data, client_address = self.socket.recvfrom(4096)
                self._handle_message(data, client_address)
        except KeyboardInterrupt:
            print("Server interrotto")
        finally:
            self.socket.close()
    
    def stop(self):
        """Arresta il server."""
        self.running = False
    
    def _handle_message(self, data, client_address):
        """Gestisce i messaggi ricevuti dai client."""
        try:
            message = json.loads(data.decode('utf-8'))
            action = message.get('action')
            
            if action == 'publish':
                self._handle_publish(message, client_address)
            elif action == 'subscribe':
                self._handle_subscribe(message, client_address)
            elif action == 'get':
                self._handle_get(message, client_address)
            else:
                self._send_error(client_address, f"Azione non supportata: {action}")
        except json.JSONDecodeError:
            self._send_error(client_address, "Formato messaggio non valido")
    
    def _handle_publish(self, message, client_address):
        """Gestisce la pubblicazione di un messaggio su un topic."""
        topic = message.get('topic')
        payload = message.get('payload')
        
        if not topic:
            return self._send_error(client_address, "Topic mancante")
        
        if payload is None:
            return self._send_error(client_address, "Payload mancante")
        
        # Aggiungi timestamp al messaggio
        message_with_timestamp = {
            'payload': payload,
            'timestamp': time.time()
        }
        
        # Aggiungi messaggio alla coda del topic
        self.topics[topic].append(message_with_timestamp)
        
        # Limita la dimensione della coda (opzionale)
        if len(self.topics[topic]) > 10:
            self.topics[topic].popleft()
        
        # Conferma pubblicazione
        response = {
            'status': 'success',
            'action': 'publish',
            'topic': topic
        }
        self.socket.sendto(json.dumps(response).encode('utf-8'), client_address)
    
    def _handle_subscribe(self, message, client_address):
        """Gestisce la sottoscrizione di un client a un topic."""
        topic = message.get('topic')
        
        if not topic:
            return self._send_error(client_address, "Topic mancante")
        
        # Aggiungi il topic alle sottoscrizioni del client
        self.subscriptions[client_address].add(topic)
        
        # Conferma sottoscrizione
        response = {
            'status': 'success',
            'action': 'subscribe',
            'topic': topic
        }
        self.socket.sendto(json.dumps(response).encode('utf-8'), client_address)
    
    def _handle_get(self, message, client_address):
        """Gestisce la lettura di messaggi da un topic."""
        topic = message.get('topic')
        
        if not topic:
            return self._send_error(client_address, "Topic mancante")
        
        if topic not in self.topics or len(self.topics[topic]) == 0 or topic not in self.subscriptions[client_address]:
            response = {
                'status': 'success',
                'action': 'get',
                'topic': topic,
                'messages': []
            }
        else:
            # Invia tutti i messaggi nel topic (in un'implementazione completa potrebbe essere limitato)
            messages = list(self.topics[topic])
            response = {
                'status': 'success',
                'action': 'get',
                'topic': topic,
                'messages': messages
            }
        
        self.socket.sendto(json.dumps(response).encode('utf-8'), client_address)
    
    def _send_error(self, client_address, error_message):
        """Invia un messaggio di errore al client."""
        response = {
            'status': 'error',
            'error': error_message
        }
        self.socket.sendto(json.dumps(response).encode('utf-8'), client_address)


# Avvio server se eseguito direttamente
if __name__ == "__main__":
    server = MessageQueueServer()
    server.start()
