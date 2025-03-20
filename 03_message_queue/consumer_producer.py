# esempio_utilizzo.py
import time
from mqc import *

def producer():
    """Funzione di esempio per un producer."""
    client = MessageQueueClient()
    
    for i in range(5):
        message = {
            "id": i,
            "content": f"Messaggio di test #{i}",
            "timestamp": time.time()
        }
        
        print(f"Pubblicazione messaggio: {message}")
        response = client.publish("esempi", message)
        print(f"Risposta: {response}")
        
        time.sleep(1)
    
    client.close()

def consumer():
    """Funzione di esempio per un consumer."""
    client = MessageQueueClient()
    
    # Sottoscrivi al topic
    client.subscribe("esempi")
    
    # Leggi messaggi periodicamente
    for _ in range(10):
        messages = client.get_messages("esempi")
        if messages:
            print(f"Ricevuti {len(messages)} messaggi:")
            for msg in messages:
                print(f" - {msg}")
        else:
            print("Nessun messaggio disponibile")
        
        time.sleep(2)
    
    client.close()

if __name__ == "__main__":
    import threading
    
    # Avvia producer e consumer in thread separati
    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)
    
    producer_thread.start()
    time.sleep(1)  # Piccolo ritardo per assicurarsi che il producer inizi prima
    consumer_thread.start()
    
    producer_thread.join()
    consumer_thread.join()
