# Key-Value Store Distribuito con Cache Limitata e Sharding

Questo progetto implementa un sistema distribuito di key-value store con cache limitata e una configurazione avanzata di sharding basata su consistent hashing.

## Architettura

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
- `REPLICATION_FACTOR`: Fattore di replica (percentuale di nodi su cui replicare ogni chiave)
- `VIRTUAL_NODES`: Numero di nodi virtuali per nodo fisico
- `REQUEST_TIMEOUT`: Timeout per le richieste ai nodi (secondi)

### Nodi KV Store:
- `MAX_CACHE_ITEMS`: Numero massimo di elementi in cache
- `MAX_CACHE_SIZE_BYTES`: Dimensione massima della cache in bytes
- `DB_FILE`: Percorso del file database SQLite
- `LOG_FILE`: Percorso del file di log

Queste variabili possono essere modificate nel file `docker-compose.yml`.

## Dettagli implementativi

### Consistent Hashing

L'implementazione del consistent hashing utilizza un anello hash in cui:

1. Ogni nodo fisico è rappresentato da più nodi virtuali nell'anello
2. Per ogni nodo virtuale, viene calcolato un hash MD5 della stringa `nodo:indice_virtuale`
3. Questi hash vengono ordinati per formare l'anello
4. Per trovare il nodo responsabile di una chiave:
   - Si calcola l'hash MD5 della chiave
   - Si trova il primo nodo virtuale con posizione >= hash della chiave
   - Si procede in senso orario per trovare i nodi di replica

### Replicazione

Il sistema supporta un fattore di replica configurabile:

1. Se il fattore di replica è 0.5 (50%) su 4 nodi, ogni chiave sarà replicata su 2 nodi
2. Le repliche sono posizionate su nodi fisici distinti quando possibile
3. I nodi di replica sono determinati procedendo in senso orario sull'anello hash

### Ribilanciamento

Il ribilanciamento avviene in questi passaggi:

1. Per ogni chiave presente nel sistema, si determina i nodi su cui dovrebbe essere memorizzata
2. Si confronta questa distribuzione ideale con quella attuale
3. Si aggiungono o rimuovono le repliche dai nodi necessari per allinearsi alla distribuzione ideale
4. Il processo avviene senza interruzione del servizio

## Limitazioni e possibili miglioramenti

- **Tolleranza ai guasti**: Implementare un meccanismo di health check per rilevare nodi non disponibili
- **Replica incrementale**: Implementare una replica incrementale per ridurre il traffico di rete
- **Compressione dei dati**: Aggiungere compressione per ridurre lo spazio di archiviazione
- **Consistenza**: Implementare strategie di consistenza più avanzate (read repair, vector clocks, ecc.)
- **Quorum configurabile**: Permette di specificare quante repliche devono rispondere per considerare una lettura valida
- **Auto-scaling**: Aggiungere o rimuovere nodi automaticamente in base al carico
- **Partizioni multiple**: Supportare più anelli di hash per distribuire il carico su infrastrutture diverse
- **Metriche avanzate**: Migliorare il monitoraggio delle prestazioni e della distribuzione delle chiavi
