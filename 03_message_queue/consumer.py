import argparse
import time
import json
import sys
from mqc import *

def process_message(message):
    """Elabora un messaggio ricevuto (esempio)."""
    payload = message.get('payload', {})
    timestamp = message.get('timestamp', 0)
    
    msg_time = time.strftime('%H:%M:%S', time.localtime(timestamp))
    
    if isinstance(payload, dict):
        msg_id = payload.get('id', 'unknown')
        content = payload.get('content', 'empty')
        random_value = payload.get('random_value', 'N/A')
        return f"ID: {msg_id}, Content: {content}, Random: {random_value}, Time: {msg_time}"
    else:
        return f"Payload: {payload}, Time: {msg_time}"

def run_consumer(topic, interval, count, host, port):
    """Esegue un consumer che legge messaggi dal topic specificato."""
    client = MessageQueueClient(server_host=host, server_port=port)
    
    # Sottoscrivi al topic
    response = client.subscribe(topic)
    if response and response.get('status') == 'success':
        print(f"Sottoscrizione al topic '{topic}' avvenuta con successo")
    else:
        print(f"Errore nella sottoscrizione al topic '{topic}': {response}")
        client.close()
        return
    
    print(f"Consumer avviato - Topic: {topic}, Intervallo: {interval}s, Count: {'infinito' if count == -1 else count}")
    
    iterations = 0
    try:
        while count == -1 or iterations < count:
            print(f"\n[{time.strftime('%H:%M:%S')}] Lettura messaggi dal topic '{topic}'...")
            
            # Leggi messaggi dal topic
            messages = client.get_messages(topic)
            
            if messages:
                print(f"Ricevuti {len(messages)} messaggi:")
                for idx, msg in enumerate(messages):
                    print(f" #{idx+1}: {process_message(msg)}")
            else:
                print("Nessun messaggio disponibile")
            
            iterations += 1
            
            # Attendi l'intervallo specificato prima della prossima lettura
            if count == -1 or iterations < count:
                time.sleep(interval)
                
    except KeyboardInterrupt:
        print("\nConsumer interrotto dall'utente")
    finally:
        client.close()
        print("Consumer terminato")

def main():
    parser = argparse.ArgumentParser(description='Message Queue Consumer')
    parser.add_argument('--topic', type=str, required=True, help='Nome del topic')
    parser.add_argument('--interval', type=float, default=2.0, help='Intervallo tra le letture in secondi (default: 2.0)')
    parser.add_argument('--count', type=int, default=-1, help='Numero di letture da effettuare (-1 per infinito, default: -1)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host del server MQ (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5555, help='Porta del server MQ (default: 5555)')
    
    args = parser.parse_args()
    
    run_consumer(args.topic, args.interval, args.count, args.host, args.port)

if __name__ == "__main__":
    main()
