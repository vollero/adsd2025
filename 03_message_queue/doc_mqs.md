# Documentazione del Message Queue Server UDP

## Panoramica del Sistema

Il codice implementa un server per un sistema di code di messaggi (Message Queue) basato su UDP. Questo sistema permette la comunicazione asincrona tra applicazioni distribuite attraverso il meccanismo di pubblicazione e sottoscrizione (publish/subscribe).

**Funzionalità principali:**
- Ricezione e gestione di messaggi via socket UDP
- Pubblicazione di messaggi su topic specifici
- Sottoscrizione di client a topic di interesse
- Lettura di messaggi da topic sottoscritti

Il server funge da intermediario tra i producer (che pubblicano messaggi) e i consumer (che leggono messaggi), disaccoppiando i componenti del sistema e consentendo una comunicazione asincrona ed efficiente.

## Funzionamento Dettagliato

### Inizializzazione e Struttura Dati

Il server utilizza diverse strutture dati chiave:

```python
# Dizionario che mappa topic a code di messaggi
self.topics = defaultdict(deque)

# Dizionario che mappa client (indirizzo) a sottoscrizioni
self.subscriptions = defaultdict(set)
```

- `topics`: Un dizionario che associa ogni nome di topic a una coda (deque) di messaggi. Usando `defaultdict` con `deque`, viene automaticamente creata una nuova coda quando si accede a un topic non ancora esistente.
- `subscriptions`: Un dizionario che tiene traccia delle sottoscrizioni, mappando gli indirizzi dei client ai set di topic a cui sono sottoscritti.

### Ciclo Principale del Server

```python
def start(self):
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
```

Il metodo `start()` contiene il ciclo principale del server, che:
1. Imposta il flag `running` a `True`
2. Entra in un ciclo che continuerà finché `running` rimane vero
3. Attende messaggi dai client tramite `socket.recvfrom()`
4. Passa i messaggi ricevuti al metodo interno `_handle_message()`
5. Gestisce eventuali interruzioni (KeyboardInterrupt) e chiude correttamente il socket alla fine

### Gestione dei Messaggi

```python
def _handle_message(self, data, client_address):
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
```

Il metodo `_handle_message()` analizza il messaggio JSON ricevuto e lo indirizza al gestore appropriato in base all'azione richiesta:
- `publish`: Per pubblicare un messaggio su un topic
- `subscribe`: Per sottoscriversi a un topic
- `get`: Per leggere messaggi da un topic

#### Pubblicazione di Messaggi

```python
def _handle_publish(self, message, client_address):
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
    if len(self.topics[topic]) > 100:
        self.topics[topic].popleft()
    
    # Conferma pubblicazione
    response = {
        'status': 'success',
        'action': 'publish',
        'topic': topic
    }
    self.socket.sendto(json.dumps(response).encode('utf-8'), client_address)
```

Quando viene ricevuta una richiesta di pubblicazione:
1. Vengono verificati i parametri necessari (topic e payload)
2. Viene aggiunto un timestamp al messaggio
3. Il messaggio viene inserito nella coda del topic specificato
4. Se la coda supera una certa dimensione (100 messaggi), vengono rimossi i messaggi più vecchi
5. Viene inviata una conferma al client

#### Sottoscrizione a Topic

```python
def _handle_subscribe(self, message, client_address):
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
```

Quando un client richiede di sottoscriversi a un topic:
1. Viene verificato che il topic sia specificato
2. Il topic viene aggiunto al set di sottoscrizioni del client
3. Viene inviata una conferma al client

#### Lettura di Messaggi

```python
def _handle_get(self, message, client_address):
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
        # Invia tutti i messaggi nel topic
        messages = list(self.topics[topic])
        response = {
            'status': 'success',
            'action': 'get',
            'topic': topic,
            'messages': messages
        }
    
    self.socket.sendto(json.dumps(response).encode('utf-8'), client_address)
```

Quando un client richiede di leggere messaggi da un topic:
1. Viene verificato che il topic sia specificato
2. Se il topic non esiste o è vuoto o il client non è sottoscritto al topic, viene inviata una lista vuota
3. Altrimenti, vengono inviati tutti i messaggi presenti nella coda del topic specificato

### Gestione degli Errori

```python
def _send_error(self, client_address, error_message):
    response = {
        'status': 'error',
        'error': error_message
    }
    self.socket.sendto(json.dumps(response).encode('utf-8'), client_address)
```

Il server gestisce gli errori inviando messaggi di errore formattati come JSON con un campo `status` impostato a "error" e un campo `error` contenente il messaggio di errore specifico.

## Considerazioni Architetturali

### Vantaggi dell'Implementazione

1. **Semplicità**: L'uso di UDP e JSON rende l'implementazione semplice e diretta.
2. **Leggerezza**: Il server ha un overhead minimo e utilizza strutture dati efficienti.
3. **Persistenza temporanea**: I messaggi vengono conservati in memoria finché non vengono eliminati per limiti di spazio.
4. **Disaccoppiamento**: I producer e consumer comunicano in modo asincrono, migliorando la scalabilità.

### Limitazioni

1. **Affidabilità**: UDP non garantisce la consegna dei pacchetti, quindi potrebbero verificarsi perdite di messaggi.
2. **Scalabilità limitata**: Tutte le code sono mantenute in memoria, limitando il numero di messaggi che possono essere gestiti.
3. **Nessuna persistenza permanente**: I messaggi vengono persi in caso di riavvio del server.
4. **Nessun supporto per gruppi di consumatori**: Non esiste il concetto di gruppi di consumer che condividono il carico di elaborazione.

## Possibili Estensioni

1. **Persistenza** su disco per i messaggi
2. **Acknowledgment** per confermare l'elaborazione dei messaggi
3. **Gruppi di consumer** per la distribuzione del carico
4. **Retention policy** configurabili per i messaggi
5. **Sicurezza** con autenticazione e autorizzazione
6. **Metriche e monitoraggio** delle prestazioni
