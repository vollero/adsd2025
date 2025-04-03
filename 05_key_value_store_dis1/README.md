# Key-Value Store Distribuito con Cache Limitata

Questo progetto implementa un sistema distribuito di key-value store con un meccanismo di replicazione full e lettura a quorum. Il sistema è composto da un coordinatore e da un numero configurabile di nodi di key-value store.

## Architettura

Il sistema è composto da:

1. **Coordinatore**: Si occupa di gestire le richieste dei client e di coordinarle verso i nodi KV store. Implementa:
   - Replicazione completa per le scritture (scrive su tutti i nodi)
   - Letture con quorum (legge da una maggioranza di nodi)
   - Bilanciamento del carico distribuendo le richieste tra i nodi

2. **Nodi KV Store**: Memorizzano i dati e implementano:
   - Cache LRU (Least Recently Used) con limite di dimensione e numero di elementi
   - Persistenza su database SQLite
   - Batch di operazioni per ottimizzare le scritture sul database

3. **Rete Privata**: I nodi KV store sono accessibili solo dal coordinatore attraverso una rete Docker interna.

4. **Rete Pubblica**: Solo il coordinatore è esposto all'esterno della rete Docker.

## Caratteristiche principali

- **Alta disponibilità**: Il sistema rimane operativo anche in caso di guasto di una parte dei nodi (fino a N-quorum)
- **Cache con politica LRU**: Per ottimizzare le prestazioni
- **Persistenza dei dati**: Ogni nodo mantiene una copia persistente dei dati su SQLite
- **Logging**: Registrazione di tutte le operazioni per diagnostica e debugging
- **Sincronizzazione asincrona**: Le scritture sul database avvengono in batch per ottimizzare le prestazioni
- **Scalabilità orizzontale**: Possibilità di aggiungere ulteriori nodi al sistema

## Requisiti

- Docker
- Docker Compose
- Bash (per lo script di setup)

## Installazione e configurazione

1. Accedi alla cartella:

```bash
cd kvstore-distributed
```

2. Esegui lo script di setup per generare i file necessari:

```bash
chmod +x setup.sh
./setup.sh
```

Durante l'esecuzione, lo script ti chiederà:
- Il numero di nodi KV store da istanziare (default: 3)
- La dimensione del quorum per le letture (default: numero_nodi/2 + 1)
- La porta su cui esporre il coordinatore (default: 8000)

3. Avvia il sistema:

```bash
docker-compose up -d
```

## Utilizzo

### API REST del coordinatore

Il coordinatore espone le seguenti API REST:

- `GET /key/{key}`: Ottiene il valore associato a una chiave con quorum
- `PUT /key/{key}`: Inserisce o aggiorna il valore di una chiave (replica completa)
- `DELETE /key/{key}`: Elimina una chiave (replica completa)
- `GET /keys`: Ottiene tutte le chiavi presenti nel sistema
- `GET /stats`: Ottiene le statistiche del sistema
- `POST /force-sync`: Forza la sincronizzazione di tutte le operazioni in batch

### Client di test

È incluso un client Python per testare il sistema:

```bash
chmod +x test_client.py
./test_client.py --help
```

#### Esempi di utilizzo del client:

```bash
# Inserire una chiave
./test_client.py put chiave1 "valore di test"

# Ottenere il valore associato a una chiave
./test_client.py get chiave1

# Eliminare una chiave
./test_client.py delete chiave1

# Elencare tutte le chiavi
./test_client.py keys

# Ottenere le statistiche
./test_client.py stats

# Eseguire un test di carico
./test_client.py test --count 1000
```

## Monitoraggio

Per visualizzare i log del coordinatore:

```bash
docker-compose logs -f coordinator
```

Per visualizzare i log di un nodo specifico:

```bash
docker-compose logs -f kvstore1
```

## Configurazione avanzata

È possibile modificare diverse configurazioni attraverso variabili d'ambiente:

### Coordinatore:
- `KVS_NODES`: Elenco dei nodi KV store separati da virgola
- `QUORUM_SIZE`: Dimensione del quorum per le letture
- `REQUEST_TIMEOUT`: Timeout per le richieste ai nodi (secondi)

### Nodi KV Store:
- `MAX_CACHE_ITEMS`: Numero massimo di elementi in cache
- `MAX_CACHE_SIZE_BYTES`: Dimensione massima della cache in bytes
- `DB_FILE`: Percorso del file database SQLite
- `LOG_FILE`: Percorso del file di log

Queste variabili possono essere modificate nel file `docker-compose.yml`.
