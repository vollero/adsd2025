# Implementazione della Cache con Limite di Memoria

Nel file python è implementata una cache con limite di memoria sostituendo la semplice struttura dati `Dict` con una classe `LRUCache` più sofisticata. 

## 1. Classe LRUCache

LRUCache è una classe dedicata che implementa una cache LRU (Least Recently Used) basata su `OrderedDict`. Questa struttura dati mantiene l'ordine di inserimento/accesso e permette di rimuovere facilmente gli elementi meno recentemente utilizzati quando la cache raggiunge i suoi limiti.

La classe `LRUCache` offre diverse funzionalità:

- **Limite di elementi**: Configurato tramite `max_items` (default: 1000)
- **Limite di dimensione**: Configurato tramite `max_size_bytes` (default: 10 MB)
- **Politica LRU**: Gli elementi meno recentemente utilizzati vengono rimossi automaticamente
- **Stima della dimensione**: Calcolo approssimativo dello spazio utilizzato da ogni elemento
- **Thread-safety**: Utilizzo di lock per garantire la sicurezza in ambienti multi-thread

## 2. Gestione della Memoria

La classe tiene traccia della dimensione approssimativa in memoria di ogni elemento usando `sys.getsizeof()`. Quando viene raggiunto il limite configurato, gli elementi meno recentemente usati vengono automaticamente rimossi.

### Vantaggi:
- **Prevenzione out-of-memory**: La memoria utilizzata non crescerà oltre il limite configurato
- **Auto-regolazione**: La cache si adatta automaticamente rimuovendo gli elementi meno utili
- **Protezione da attacchi DoS**: Grandi valori non possono saturare la memoria del server

## 3. API Avanzate

E' stata aggiunta una nuova rotta `/clear-cache` per svuotare completamente la cache e la rotta `/stats` ora fornisce informazioni dettagliate sull'utilizzo della cache.

Le statistiche includono:
- Numero di elementi nella cache
- Numero massimo di elementi
- Dimensione attuale in bytes
- Dimensione massima consentita
- Percentuale di utilizzo

## 4. Gestione dei Valori Troppo Grandi

E' stato aggiunto un controllo per i valori troppo grandi per la cache. Se un valore supera il limite massimo di dimensione consentito, viene memorizzato solo nel database, con un avviso nei log.

## Modifiche alle Route Esistenti

Tutte le route sono state aggiornate per utilizzare i nuovi metodi della classe `LRUCache` invece di accedere direttamente al dizionario. In particolare:

- `get_all_keys`: Utilizza `memory_cache.keys()`
- `get_value`: Utilizza `memory_cache.get(key)`
- `put_value`: Utilizza `memory_cache.put(key, value)`
- `delete_value`: Utilizza `memory_cache.delete(key)`

## Configurazione

I limiti della cache possono essere modificati aggiornando le costanti all'inizio del file:

```python
MAX_CACHE_ITEMS = 1000  # Numero massimo di elementi in cache
MAX_CACHE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB in bytes
```

Si possono regolare questi valori in base alle caratteristiche del proprio sistema e ai requisiti di memoria.
