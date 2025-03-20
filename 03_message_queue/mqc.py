import socket
import json
import time
import uuid

class MessageQueueClient:
    def __init__(self, server_host='127.0.0.1', server_port=5555, timeout=5):
        self.server_address = (server_host, server_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.client_id = str(uuid.uuid4())
    
    def publish(self, topic, payload):
        """Pubblica un messaggio su un topic."""
        message = {
            'action': 'publish',
            'topic': topic,
            'payload': payload,
            'client_id': self.client_id
        }
        
        return self._send_and_receive(message)
    
    def subscribe(self, topic):
        """Sottoscrive il client a un topic."""
        message = {
            'action': 'subscribe',
            'topic': topic,
            'client_id': self.client_id
        }
        
        return self._send_and_receive(message)
    
    def get_messages(self, topic):
        """Ottiene i messaggi da un topic."""
        message = {
            'action': 'get',
            'topic': topic,
            'client_id': self.client_id
        }
        
        response = self._send_and_receive(message)
        if response and response.get('status') == 'success':
            return response.get('messages', [])
        return []
    
    def _send_and_receive(self, message):
        """Invia un messaggio al server e riceve la risposta."""
        try:
            serialized_message = json.dumps(message).encode('utf-8')
            self.socket.sendto(serialized_message, self.server_address)
            
            data, _ = self.socket.recvfrom(4096)
            return json.loads(data.decode('utf-8'))
        except socket.timeout:
            print("Timeout di connessione al server")
            return None
        except (ConnectionRefusedError, ConnectionResetError):
            print("Impossibile connettersi al server")
            return None
        except json.JSONDecodeError:
            print("Ricevuta risposta non valida dal server")
            return None
    
    def close(self):
        """Chiude la connessione."""
        self.socket.close()


# Esempio di utilizzo del client
if __name__ == "__main__":
    client = MessageQueueClient()
    
    # Pubblica un messaggio
    print("pubblico un messaggio")
    client.publish("test-topic", {"message": "Ciao mondo!"})
    

    print("mi sottoscrivo al topic")
    # Sottoscrivi a un topic
    client.subscribe("test-topic")
    
    print("leggo tutti i messaggi del topic")
    # Leggi messaggi da un topic
    messages = client.get_messages("test-topic")
    for msg in messages:
        print(f"Messaggio ricevuto: {msg}")
    
    client.close()
