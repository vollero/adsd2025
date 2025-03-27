# FastAPI e Programmazione Asincrona: Concetti Fondamentali

## FastAPI

[FastAPI](https://fastapi.tiangolo.com/) è un framework web Python ad alte prestazioni, progettato per creare API sugli standard OpenAPI e JSON Schema. 
Le caratteristiche principali di FastAPI sono:

1. **Velocità**: È uno dei framework Python più veloci disponibili, paragonabile a NodeJS e Go, grazie all'utilizzo di [Starlette](https://www.starlette.io/) e [Pydantic](https://docs.pydantic.dev/latest/).

2. **Semplicità e facilità d'uso**: Sintassi intuitiva e riduzione del codice boilerplate permettono di sviluppare API rapidamente.

3. **Validazione automatica**: Attraverso Pydantic, FastAPI fornisce validazione automatica dei dati in entrata, generazione di errori JSON chiari e conversione dei dati.

4. **Documentazione automatica**: Genera automaticamente documentazione interattiva (Swagger UI e ReDoc) basata su OpenAPI.

5. **Programmazione asincrona**: Supporto nativo per operazioni asincrone, fondamentali per applicazioni ad alte prestazioni.

## Programmazione Asincrona in Python

La programmazione asincrona consente l'esecuzione non bloccante del codice, particolarmente utile per operazioni I/O-bound come richieste di rete o operazioni su database. In Python, questo è realizzato principalmente attraverso la libreria `asyncio` e le parole chiave `async`/`await`.

### Concetti chiave:

1. **Coroutine**: Funzioni dichiarate con `async def` che possono essere sospese e riprese durante l'esecuzione.

2. **Event Loop**: Il "motore" che gestisce l'esecuzione delle coroutine, pianificando e coordinando il loro flusso.

3. **await**: Operatore utilizzato all'interno di una coroutine per cedere il controllo all'event loop fino al completamento di un'operazione asincrona.

4. **Concorrenza vs Parallelismo**: 
   - La concorrenza asincrona permette a più attività di progredire apparentemente in parallelo, ma ancora su un singolo thread.
   - Il vero parallelismo richiede thread o processi multipli.

### Async Context Managers

I gestori di contesto asincroni (`async with`) sono strumenti potenti nella programmazione asincrona che consentono l'acquisizione e il rilascio automatico di risorse in un contesto asincrono:

1. **Definizione**: Attraverso `@asynccontextmanager` o implementando i metodi `__aenter__` e `__aexit__`.

2. **Utilizzo**: Con `async with` all'interno di funzioni asincrone.

3. **Applicazioni**: Gestione di connessioni a database, sessioni HTTP, e altri contesti di risorse asincrone.

Nel codice del key-value store, il gestore di contesto asincrono `lifespan` è utilizzato per gestire l'inizializzazione e la pulizia dell'applicazione FastAPI.

## Ciclo di Vita dell'Applicazione in FastAPI

FastAPI utilizza il concetto di "lifespan" per gestire la creazione e la pulizia delle risorse dell'applicazione:

1. **Inizializzazione**: Eseguita all'avvio dell'applicazione, prima di accettare richieste.

2. **Esecuzione**: L'applicazione gestisce le richieste in arrivo.

3. **Finalizzazione**: Eseguita prima dello spegnimento dell'applicazione, dopo aver smesso di accettare richieste.

Il gestore `lifespan` sostituisce i precedenti decoratori `@app.on_event("startup")` e `@app.on_event("shutdown")`, offrendo un approccio più elegante e robusto.

## Task in Background in FastAPI

FastAPI consente di eseguire operazioni asincrone in background attraverso il sistema `BackgroundTasks`:

1. **Definizione**: Le attività di background sono funzioni che vengono eseguite dopo che la risposta è stata inviata al client.

2. **Vantaggi**: Permettono di eseguire operazioni costose senza bloccare la risposta all'utente.

3. **Implementazione**: Utilizzando l'oggetto `BackgroundTasks` come parametro di una rotta e aggiungendovi funzioni con `background_tasks.add_task()`.

Nel key-value store, questo è utilizzato per la sincronizzazione asincrona dei dati con il database.

# Documentazione Key-Value Store

## Panoramica

Questo modulo implementa un key-value store utilizzando FastAPI, con supporto per caching in memoria, persistenza su database SQLite, e batch processing per le operazioni di scrittura. Il sistema fornisce un'API RESTful per operazioni CRUD (Create, Read, Update, Delete) su coppie chiave-valore.

## Componenti principali

### Logger

Il sistema utilizza il modulo `logging` standard di Python per tracciare le operazioni:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='kv_store.log'
)
logger = logging.getLogger("kv_store")
```

### Modelli dati

I modelli dati sono definiti utilizzando Pydantic:

- `KeyValue`: Rappresenta un valore associato a una chiave
- `StatusResponse`: Rappresenta una risposta di stato per le operazioni

### Cache in memoria

Il sistema mantiene una cache in memoria per accesso rapido ai dati:

```python
memory_cache: Dict[str, Any] = {}
cache_lock = threading.RLock()  # Lock per la sincronizzazione della cache
```

La cache utilizza un `RLock` per garantire la thread-safety nelle operazioni di lettura e scrittura.

### Database SQLite

La persistenza dei dati è gestita attraverso SQLite:

- `kv_store`: Tabella principale per memorizzare le coppie chiave-valore
- `kv_store_history`: Tabella per memorizzare la cronologia delle operazioni

La connessione al database viene creata quando necessario tramite la funzione `get_db_connection()`.

### Batch Processing

Il sistema raggruppa le operazioni di scrittura in batch per ottimizzare le performance:

```python
pending_operations: List[Tuple[str, str, str]] = []
batch_lock = threading.RLock()
batch_size_threshold = 10
last_batch_time = time.time()
batch_time_threshold = 60  # secondi
```

Le operazioni di scrittura vengono eseguite in batch quando:
1. Il numero di operazioni pendenti raggiunge la soglia `batch_size_threshold`
2. Il tempo trascorso dall'ultimo batch supera la soglia `batch_time_threshold`

### Lifespan

Il gestore di ciclo di vita dell'applicazione è implementato come un context manager asincrono:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice di inizializzazione
    yield
    # Codice di finalizzazione
```

Questo sostituisce i vecchi gestori `on_event` e gestisce:
- All'avvio: inizializzazione del database e caricamento dei dati in cache
- All'arresto: sincronizzazione forzata delle operazioni pendenti

## API Endpoints

### Informazioni di base

```
GET /
```

Restituisce un messaggio di base sull'applicazione.

**Risposta**:
```json
{
  "message": "Key-Value Store Distribuito"
}
```

### Ottenere tutte le chiavi

```
GET /keys
```

Restituisce un elenco di tutte le chiavi attualmente presenti nel key-value store.

**Risposta**:
```json
{
  "keys": ["chiave1", "chiave2", "chiave3"]
}
```

### Ottenere un valore

```
GET /key/{key}
```

Restituisce il valore associato alla chiave specificata.

**Parametri**:
- `key`: La chiave di cui si vuole ottenere il valore

**Risposta (successo)**:
```json
{
  "key": "example_key",
  "value": "example_value"
}
```

**Risposta (errore)**:
```json
{
  "detail": "Key 'example_key' not found"
}
```

### Inserire o aggiornare un valore

```
PUT /key/{key}
```

Inserisce o aggiorna il valore associato alla chiave specificata.

**Parametri**:
- `key`: La chiave da inserire o aggiornare

**Corpo della richiesta**:
```json
{
  "value": "nuovo_valore"
}
```

**Risposta**:
```json
{
  "key": "example_key",
  "value": "nuovo_valore"
}
```

### Eliminare una chiave

```
DELETE /key/{key}
```

Elimina una chiave e il suo valore associato.

**Parametri**:
- `key`: La chiave da eliminare

**Risposta (successo)**:
```json
{
  "status": "success",
  "message": "Key 'example_key' deleted"
}
```

**Risposta (errore)**:
```json
{
  "detail": "Key 'example_key' not found"
}
```

### Forzare la sincronizzazione

```
POST /force-sync
```

Forza la sincronizzazione del batch di operazioni con il database.

**Risposta**:
```json
{
  "status": "success",
  "message": "Batch synchronization initiated"
}
```

### Ottenere statistiche

```
GET /stats
```

Ottiene statistiche sul key-value store.

**Risposta**:
```json
{
  "cache_size": 42,
  "db_size": 50,
  "history_count": 120,
  "pending_operations": 5
}
```

## Funzioni principali

### Gestione del database

- `get_db_connection()`: Crea una connessione al database SQLite
- `init_db()`: Inizializza il database creando le tabelle necessarie se non esistono

### Gestione del batch

- `add_to_batch(key, value, operation)`: Aggiunge un'operazione al batch per la sincronizzazione
- `sync_batch_to_db(background_tasks)`: Sincronizza il batch di operazioni con il database in background
- `_sync_batch()`: Funzione di sincronizzazione eseguita in background

### Ciclo di vita dell'applicazione

- Funzione `lifespan`: Gestisce l'inizializzazione e la finalizzazione dell'applicazione

## Gestione della concorrenza

Il sistema utilizza diversi meccanismi per gestire la concorrenza:

1. **RLock per la cache**: Protegge l'accesso concorrente alla cache in memoria
2. **RLock per il batch**: Protegge l'accesso concorrente alle operazioni pendenti
3. **Operazioni asincrone**: Le route sono definite come `async def` per sfruttare la concorrenza di FastAPI
4. **Task in background**: La sincronizzazione con il database viene eseguita in background per non bloccare le risposte API

## Flusso di esecuzione

1. All'avvio, il sistema inizializza il database e carica i dati esistenti nella cache in memoria
2. Le richieste di lettura (GET) cercano prima il valore nella cache, poi nel database se non trovato
3. Le richieste di scrittura (PUT/DELETE) aggiornano la cache immediatamente e aggiungono l'operazione al batch
4. Le operazioni nel batch vengono sincronizzate con il database quando:
   - Il numero di operazioni pendenti raggiunge la soglia configurata
   - Il tempo dall'ultima sincronizzazione supera la soglia configurata
   - Viene richiesta esplicitamente la sincronizzazione
5. All'arresto, il sistema forza la sincronizzazione di tutte le operazioni pendenti

## Esecuzione dell'applicazione

Per avviare l'applicazione, eseguire:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
```

Questo avvierà il server FastAPI sulla porta 8050 e accetterà connessioni da qualsiasi indirizzo IP.

## Vantaggi dell'approccio asincrono in questo contesto

1. **Alta concorrenza**: Può gestire molte richieste contemporaneamente senza bloccare il thread principale
2. **Efficienza I/O**: Le operazioni di database non bloccano l'elaborazione di altre richieste
3. **Risposta reattiva**: Le risposte API vengono restituite rapidamente, con operazioni costose eseguite in background
4. **Scalabilità**: Può gestire un numero elevato di connessioni con risorse limitate

L'uso combinato di operazioni asincrone, cache in memoria e batch processing rende questo key-value store efficiente e scalabile pur mantenendo una buona persistenza dei dati.
