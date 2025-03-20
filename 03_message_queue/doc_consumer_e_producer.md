# Documentazione degli Script Producer e Consumer Standalone

## Panoramica

Gli script `producer.py` e `consumer.py` implementano un sistema di comunicazione asincrona basato sul pattern producer-consumer, utilizzando il protocollo di message queue UDP. Questi script sono progettati per essere eseguiti come programmi standalone, con configurazione flessibile tramite parametri da riga di comando.

**Caratteristiche principali:**
- Producer che genera e pubblica messaggi su topic specificati
- Consumer che si sottoscrive e legge messaggi dai topic
- Configurazione flessibile tramite argomenti da riga di comando
- Supporto per esecuzione limitata o infinita (loop continuo)
- Intervalli di tempo configurabili tra le operazioni
- Output informativo a console per monitorare l'attività

Questi script consentono di testare, dimostrare e utilizzare il sistema di message queue in scenari reali, con la possibilità di avviare più istanze di producer e consumer su diversi terminali per simulare un sistema distribuito.

## Funzionamento Dettagliato

### Producer (`producer.py`)

#### Componenti Principali

Il producer è composto da tre funzioni principali:

1. **`generate_message(msg_id)`**: Genera messaggi di test con:
   ```python
   def generate_message(msg_id):
       """Genera un messaggio di test con contenuto casuale."""
       return {
           "id": msg_id,
           "content": f"Messaggio #{msg_id}",
           "timestamp": time.time(),
           "random_value": random.randint(1, 1000)
       }
   ```
   
   Questa funzione crea un dizionario con:
   - Un identificativo sequenziale
   - Una stringa di contenuto
   - Un timestamp di creazione
   - Un valore casuale tra 1 e 1000

2. **`run_producer(topic, interval, count, host, port)`**: Funzione principale che:
   ```python
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
   ```

   - Inizializza il client di message queue con l'host e la porta specificati
   - Esegue un ciclo che genera e pubblica messaggi:
     - In modo infinito se `count` è -1
     - Per un numero specifico di volte se `count` è positivo
   - Attende l'intervallo specificato tra pubblicazioni consecutive
   - Gestisce l'interruzione da tastiera (Ctrl+C)
   - Garantisce la chiusura del client anche in caso di errori

3. **`main()`**: Configura e avvia il producer:
   ```python
   def main():
       parser = argparse.ArgumentParser(description='Message Queue Producer')
       parser.add_argument('--topic', type=str, required=True, help='Nome del topic')
       parser.add_argument('--interval', type=float, default=1.0, help='Intervallo tra i messaggi in secondi (default: 1.0)')
       parser.add_argument('--count', type=int, default=-1, help='Numero di messaggi da inviare (-1 per infinito, default: -1)')
       parser.add_argument('--host', type=str, default='127.0.0.1', help='Host del server MQ (default: 127.0.0.1)')
       parser.add_argument('--port', type=int, default=5555, help='Porta del server MQ (default: 5555)')
       
       args = parser.parse_args()
       
       run_producer(args.topic, args.interval, args.count, args.host, args.port)
   ```

   - Definisce e gestisce gli argomenti da riga di comando:
     - `--topic`: Nome del topic su cui pubblicare (obbligatorio)
     - `--interval`: Intervallo in secondi tra i messaggi (default: 1.0)
     - `--count`: Numero di messaggi da inviare (-1 per infinito, default: -1)
     - `--host`: Indirizzo del server (default: 127.0.0.1)
     - `--port`: Porta del server (default: 5555)
   - Avvia il producer con i parametri specificati

#### Flusso di Esecuzione del Producer

1. L'utente avvia lo script con i parametri desiderati
2. Lo script analizza i parametri e inizializza il client
3. Il producer entra in un ciclo che:
   - Genera un nuovo messaggio con ID incrementale
   - Pubblica il messaggio sul topic specificato
   - Mostra l'esito dell'operazione
   - Attende per l'intervallo specificato
   - Continua fino al raggiungimento del conteggio o all'interruzione manuale
4. Al termine (o in caso di interruzione), il producer chiude la connessione

### Consumer (`consumer.py`)

#### Componenti Principali

Il consumer è composto da tre funzioni principali:

1. **`process_message(message)`**: Elabora e formatta i messaggi ricevuti:
   ```python
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
   ```

   - Estrae payload e timestamp dal messaggio
   - Converte il timestamp in un formato leggibile
   - Formatta i dati in una stringa per la visualizzazione
   - Gestisce payload di diversi formati

2. **`run_consumer(topic, interval, count, host, port)`**: Funzione principale che:
   ```python
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
   ```

   - Inizializza il client di message queue
   - Si sottoscrive al topic specificato
   - Esegue un ciclo che legge e processa i messaggi:
     - In modo infinito se `count` è -1
     - Per un numero specifico di letture se `count` è positivo
   - Attende l'intervallo specificato tra letture consecutive
   - Gestisce l'interruzione da tastiera
   - Garantisce la chiusura del client anche in caso di errori

3. **`main()`**: Configura e avvia il consumer:
   ```python
   def main():
       parser = argparse.ArgumentParser(description='Message Queue Consumer')
       parser.add_argument('--topic', type=str, required=True, help='Nome del topic')
       parser.add_argument('--interval', type=float, default=2.0, help='Intervallo tra le letture in secondi (default: 2.0)')
       parser.add_argument('--count', type=int, default=-1, help='Numero di letture da effettuare (-1 per infinito, default: -1)')
       parser.add_argument('--host', type=str, default='127.0.0.1', help='Host del server MQ (default: 127.0.0.1)')
       parser.add_argument('--port', type=int, default=5555, help='Porta del server MQ (default: 5555)')
       
       args = parser.parse_args()
       
       run_consumer(args.topic, args.interval, args.count, args.host, args.port)
   ```

   - Definisce e gestisce gli argomenti da riga di comando:
     - `--topic`: Nome del topic da cui leggere (obbligatorio)
     - `--interval`: Intervallo in secondi tra le letture (default: 2.0)
     - `--count`: Numero di cicli di lettura da effettuare (-1 per infinito, default: -1)
     - `--host`: Indirizzo del server (default: 127.0.0.1)
     - `--port`: Porta del server (default: 5555)
   - Avvia il consumer con i parametri specificati

#### Flusso di Esecuzione del Consumer

1. L'utente avvia lo script con i parametri desiderati
2. Lo script analizza i parametri e inizializza il client
3. Il consumer si sottoscrive al topic specificato
4. Il consumer entra in un ciclo che:
   - Richiede i messaggi disponibili sul topic
   - Processa e visualizza i messaggi ricevuti
   - Attende per l'intervallo specificato
   - Continua fino al raggiungimento del conteggio o all'interruzione manuale
5. Al termine (o in caso di interruzione), il consumer chiude la connessione

## Parametri da Riga di Comando

Entrambi gli script accettano parametri simili che permettono una configurazione flessibile:

| Parametro | Descrizione | Default | Producer | Consumer |
|-----------|-------------|---------|----------|----------|
| `--topic` | Nome del topic | (Obbligatorio) | ✓ | ✓ |
| `--interval` | Intervallo in secondi | 1.0 (Producer)<br>2.0 (Consumer) | ✓ | ✓ |
| `--count` | Numero di operazioni | -1 (infinito) | ✓ | ✓ |
| `--host` | Indirizzo del server | 127.0.0.1 | ✓ | ✓ |
| `--port` | Porta del server | 5555 | ✓ | ✓ |

## Gestione degli Errori e Robustezza

Gli script includono diverse misure per garantire robustezza:

1. **Gestione delle interruzioni**: Entrambi gli script gestiscono `KeyboardInterrupt` per terminare in modo pulito quando l'utente preme Ctrl+C
2. **Blocchi `try/finally`**: Garantiscono che il client venga chiuso correttamente anche in caso di errori
3. **Verifica delle risposte**: Controllano lo stato delle risposte del server per rilevare errori
4. **Valori predefiniti ragionevoli**: Forniscono default sensati per i parametri opzionali
5. **Messaggi informativi**: Mostrano informazioni utili sullo stato dell'esecuzione

## Considerazioni di Design

### Vantaggi dell'Implementazione

1. **Autonomia**: Gli script possono essere eseguiti indipendentemente, facilitando test e distribuzione
2. **Configurabilità**: I parametri da riga di comando offrono grande flessibilità senza modificare il codice
3. **Feedback visivo**: L'output a console fornisce informazioni utili sull'attività degli script
4. **Esecuzione controllata**: La possibilità di specificare un conteggio limitato è utile per test e demo
5. **Esecuzione continua**: L'opzione per loop infinito è ideale per scenari di produzione reali

### Pattern di Comunicazione

Il pattern implementato rappresenta il classico modello producer-consumer con alcune caratteristiche specifiche:

1. **Disaccoppiamento**: Producer e consumer non hanno conoscenza diretta l'uno dell'altro
2. **Comunicazione asincrona**: I messaggi vengono pubblicati e letti in momenti diversi
3. **Persistenza temporanea**: I messaggi rimangono disponibili per un certo periodo sul server
4. **Polling**: Il consumer richiede attivamente i messaggi invece di riceverli in modo automatico
5. **Unicast**: Ogni messaggio pubblicato può essere letto da qualsiasi consumer sottoscritto

## Esempi di Utilizzo

### Avvio del Producer

```bash
# Pubblicazione di 10 messaggi sul topic 'news' con intervallo di 0.5 secondi
python producer.py --topic news --interval 0.5 --count 10

# Pubblicazione infinita sul topic 'logs' con intervallo di 2 secondi
python producer.py --topic logs --interval 2

# Pubblicazione su un server remoto
python producer.py --topic events --host 192.168.1.100 --port 5555
```

### Avvio del Consumer

```bash
# Lettura dal topic 'news' ogni secondo per 5 cicli
python consumer.py --topic news --interval 1 --count 5

# Lettura continua dal topic 'logs' ogni 3 secondi
python consumer.py --topic logs --interval 3

# Connessione a un server remoto
python consumer.py --topic events --host 192.168.1.100 --port 5555
```

### Scenari di Test

1. **Un producer, un consumer**: Avviare un producer e un consumer sullo stesso topic per verificare la comunicazione base
2. **Un producer, più consumer**: Avviare un producer e diversi consumer sullo stesso topic per verificare la distribuzione dei messaggi
3. **Più producer, un consumer**: Avviare più producer sullo stesso topic e un consumer per verificare l'aggregazione
4. **Diversi topic**: Avviare producer e consumer su topic diversi per verificare l'isolamento
