import argparse
import time
import json
import random
import sys
from mqc import *

def generate_message(msg_id):
    """Genera un messaggio di test con contenuto casuale."""
    return {
        "id": msg_id,
        "content": f"Messaggio #{msg_id}",
        "timestamp": time.time(),
        "random_value": random.randint(1, 1000)
    }

def run_producer(topic, interval, count, host, port):
    """Esegue un producer che pubblica messaggi sul topic specificato."""
    client = MessageQueueClient(server_host=host, server_port=port)
    
    print(f"Producer avviato - Topic: {topic}, Intervallo: {interval}s, Count: {'infinito' if count == -1 else count}")
    
    msg_id = 0
    try:
        while count == -1 or msg_id < count:
            # Genera e pubblica un messaggio
            message = generate_message(msg_id)
            print(f"[{time.strftime('%H:%M:%S')}] Pubblicazione messaggio #{msg_id} sul topic '{topic}'")
            
            response = client.publish(topic, message)
            if response and response.get('status') == 'success':
                print(f"✓ Messaggio pubblicato con successo")
            else:
                print(f"✗ Errore nella pubblicazione del messaggio: {response}")
            
            msg_id += 1
            
            # Attendi l'intervallo specificato prima del prossimo messaggio
            if count == -1 or msg_id < count:
                time.sleep(interval)
                
    except KeyboardInterrupt:
        print("\nProducer interrotto dall'utente")
    finally:
        client.close()
        print("Producer terminato")

def main():
    parser = argparse.ArgumentParser(description='Message Queue Producer')
    parser.add_argument('--topic', type=str, required=True, help='Nome del topic')
    parser.add_argument('--interval', type=float, default=1.0, help='Intervallo tra i messaggi in secondi (default: 1.0)')
    parser.add_argument('--count', type=int, default=-1, help='Numero di messaggi da inviare (-1 per infinito, default: -1)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host del server MQ (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5555, help='Porta del server MQ (default: 5555)')
    
    args = parser.parse_args()
    
    run_producer(args.topic, args.interval, args.count, args.host, args.port)

if __name__ == "__main__":
    main()
