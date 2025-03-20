# Documentazione del Message Queue Client UDP

## Panoramica del Client

Il codice implementa un client per interagire con un sistema di code di messaggi (Message Queue) basato su UDP. Questo client permette alle applicazioni di comunicare con il server di message queue per pubblicare messaggi, sottoscriversi a topic di interesse e leggere messaggi dai topic sottoscritti.

**Funzionalità principali:**
- Connessione al server di message queue via socket UDP
- Generazione di un ID client univoco per identificazione
- Pubblicazione di messaggi su topic specifici
- Sottoscrizione a topic di interesse
- Lettura di messaggi dai topic sottoscritti
- Gestione degli errori di comunicazione

Il client funge da interfaccia tra le applicazioni (producer o consumer) e il server di message queue, semplificando la comunicazione e gestendo le complessità di rete.

## Funzionamento Dettagliato

### Inizializzazione del Client

```python
def __init__(self, server_host='127.0.0.1', server_port=5555, timeout=5):
    self.server_address = (server_host, server_port)
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.socket.settimeout(timeout)
    self.client_id = str(uuid.uuid4())
```

Durante l'inizializzazione:
1. Viene memorizzato l'indirizzo del server (host e porta)
2. Viene creato un socket UDP
3. Viene impostato un timeout per le operazioni di rete (default 5 secondi)
4. Viene generato un ID client univoco usando UUID v4

L'ID client univoco è importante per identificare il client nelle comunicazioni con il server, specialmente in implementazioni più avanzate dove il server potrebbe tracciare lo stato delle sottoscrizioni per client specifici.

### Pubblicazione di Messaggi

```python
def publish(self, topic, payload):
    """Pubblica un messaggio su un topic."""
    message = {
        'action': 'publish',
        'topic': topic,
        'payload': payload,
        'client_id': self.client_id
    }
    
    return self._send_and_receive(message)
```

Il metodo `publish()`:
1. Costruisce un messaggio JSON con l'azione 'publish', il topic specificato, il payload (contenuto del messaggio) e l'ID client
2. Invia il messaggio al server e attende una risposta tramite il metodo privato `_send_and_receive()`
3. Restituisce la risposta dal server, che tipicamente contiene un'indicazione di successo o fallimento

Il payload può essere qualsiasi struttura dati serializzabile in JSON, offrendo grande flessibilità nel tipo di dati che possono essere scambiati.

### Sottoscrizione a Topic

```python
def subscribe(self, topic):
    """Sottoscrive il client a un topic."""
    message = {
        'action': 'subscribe',
        'topic': topic,
        'client_id': self.client_id
    }
    
    return self._send_and_receive(message)
```

Il metodo `subscribe()`:
1. Costruisce un messaggio JSON con l'azione 'subscribe', il topic di interesse e l'ID client
2. Invia il messaggio al server e attende una risposta
3. Restituisce la risposta dal server, che conferma la sottoscrizione

La sottoscrizione è un'operazione puramente lato server che associa il client al topic specificato. Nel caso di questo client, l'operazione di sottoscrizione è principalmente una richiesta formale, poiché il client dovrà comunque richiedere esplicitamente i messaggi in un secondo momento.

### Lettura di Messaggi

```python
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
```

Il metodo `get_messages()`:
1. Costruisce un messaggio JSON con l'azione 'get', il topic di interesse e l'ID client
2. Invia il messaggio al server e attende una risposta
3. Se la risposta è valida e ha uno stato di successo, estrae e restituisce la lista di messaggi
4. In caso di errore, restituisce una lista vuota

A differenza di molti sistemi di message queue, questo client deve richiedere esplicitamente i messaggi (polling) invece di riceverli automaticamente quando vengono pubblicati.

### Comunicazione con il Server

```python
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
```

Il metodo privato `_send_and_receive()` gestisce tutte le comunicazioni con il server:
1. Serializza il messaggio in formato JSON e lo codifica in UTF-8
2. Invia il messaggio al server tramite il socket UDP
3. Attende una risposta dal server (con timeout impostato durante l'inizializzazione)
4. Decodifica e deserializza la risposta JSON
5. Gestisce varie eccezioni di rete e parsing:
   - `socket.timeout`: Quando il server non risponde entro il timeout
   - `ConnectionRefusedError`, `ConnectionResetError`: Quando non è possibile stabilire una connessione
   - `json.JSONDecodeError`: Quando la risposta non è in formato JSON valido

### Chiusura della Connessione

```python
def close(self):
    """Chiude la connessione."""
    self.socket.close()
```

Il metodo `close()` rilascia le risorse di rete chiudendo il socket UDP. È importante chiamare questo metodo quando il client non è più necessario per evitare perdite di risorse.

## Formato dei Messaggi

### Messaggi dal Client al Server

I messaggi inviati dal client al server hanno una struttura JSON comune:

```json
{
  "action": "[publish|subscribe|get]",
  "topic": "nome-del-topic",
  "client_id": "uuid-del-client",
  "payload": {...}  // Solo per l'azione 'publish'
}
```

### Risposte dal Server al Client

Le risposte dal server seguono generalmente questa struttura:

Per successo:
```json
{
  "status": "success",
  "action": "[publish|subscribe|get]",
  "topic": "nome-del-topic",
  "messages": [...]  // Solo per l'azione 'get'
}
```

Per errore:
```json
{
  "status": "error",
  "error": "descrizione-errore"
}
```

## Esempio di Utilizzo

```python
client = MessageQueueClient()

# Pubblica un messaggio
client.publish("test-topic", {"message": "Ciao mondo!"})

# Sottoscrivi a un topic
client.subscribe("test-topic")

# Leggi messaggi da un topic
messages = client.get_messages("test-topic")
for msg in messages:
    print(f"Messaggio ricevuto: {msg}")

client.close()
```

Questo esempio dimostra un flusso tipico:
1. Creazione di un'istanza del client
2. Pubblicazione di un messaggio su un topic
3. Sottoscrizione allo stesso topic
4. Lettura dei messaggi dal topic
5. Elaborazione dei messaggi ricevuti
6. Chiusura della connessione

## Considerazioni Architetturali

### Vantaggi dell'Implementazione

1. **Semplicità**: L'API del client è intuitiva e facile da usare
2. **Identificazione univoca**: Ogni client ha un ID univoco generato automaticamente
3. **Gestione degli errori**: Il client gestisce vari scenari di errore di rete
4. **Flessibilità nei payload**: Qualsiasi struttura dati serializzabile in JSON può essere inviata come payload

### Limitazioni

1. **Affidabilità**: Basandosi su UDP, non c'è garanzia di consegna dei messaggi
2. **Polling**: Il client deve richiedere esplicitamente i messaggi invece di riceverli automaticamente
3. **Nessuna gestione dello stato**: Il client non tiene traccia dei messaggi già letti
4. **Timeout fisso**: Il timeout è impostato all'inizializzazione e non può essere modificato per singole operazioni

### Possibili Miglioramenti

1. **Modalità asincrona**: Implementare la possibilità di ricevere messaggi in modo asincrono usando thread o callback
2. **Gestione degli ACK**: Aggiungere conferme di lettura per i messaggi
3. **Tentativi automatici**: Implementare il retry automatico in caso di timeout o errori temporanei
4. **Buffer locale**: Memorizzare temporaneamente i messaggi in caso di problemi di connessione
5. **Compressione**: Aggiungere la compressione dei messaggi per ridurre il traffico di rete
6. **Autenticazione**: Implementare un meccanismo di autenticazione per aumentare la sicurezza
