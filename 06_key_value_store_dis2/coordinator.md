# Coordinator con Sharding basato su Consistent Hashing

Questo documento spiega l'implementazione del coordinator con sharding per il key-value store distribuito. Il coordinatore utilizza l'algoritmo di consistent hashing per distribuire le chiavi tra i nodi, supportando un fattore di replica configurabile.

## Consistent Hashing: Panoramica

Il consistent hashing è un algoritmo di distribuzione che minimizza la riorganizzazione dei dati quando si aggiungono o rimuovono nodi da un sistema distribuito. L'idea è la seguente:

1. Immagina un anello (hash ring) con valori da 0 a 2^128-1
2. Ogni nodo viene posizionato in uno o più punti sull'anello (hash(nodo))
3. Ogni chiave viene assegnata al primo nodo che si incontra procedendo in senso orario dalla posizione hash(chiave)

## Caratteristiche Principali

### Nodi Virtuali

Ogni nodo fisico è rappresentato da più nodi virtuali nell'hash ring:

```python
def _build_ring(self):
    """Costruisce l'hash ring con nodi virtuali"""
    self.ring = []
    for node in self.nodes:
        for i in range(self.virtual_nodes):
            key = f"{node}:{i}"
            position = self._hash(key)
            self.ring.append((position, node))
```

I nodi virtuali migliorano il bilanciamento del carico distribuendo ogni nodo fisico in più punti dell'anello. Questo evita gli "hotspot" che potrebbero verificarsi con un singolo hash per nodo.

### Fattore di Replica Configurabile

Il fattore di replica determina su quanti nodi viene replicata ciascuna chiave:

```python
def get_replica_nodes(key: str) -> List[str]:
    """Determina quali nodi dovrebbero contenere una chiave"""
    # Calcola quanti nodi devono avere la replica
    replica_count = max(1, round(len(KVS_NODES) * REPLICATION_FACTOR))
    return hash_ring.get_nodes(key, replica_count)
```

Un fattore di replica di 0.5 su 4 nodi significa che ogni chiave sarà replicata su 2 nodi (50% dei nodi disponibili).

### Ricerca dei Nodi per una Chiave

Per trovare tutti i nodi che dovrebbero contenere una chiave:

```python
def get_nodes(self, key: str, count: int) -> List[str]:
    """Trova 'count' nodi responsabili per una chiave"""
    hash_key = self._hash(key)
    
    # Trova l'indice del primo nodo con posizione >= hash_key
    start_idx = 0
    for i, (position, _) in enumerate(self.ring):
        if position >= hash_key:
            start_idx = i
            break
    
    # Raccoglie i nodi unici, procedendo circolarmente nell'anello
    result_nodes: Set[str] = set()
    current_idx = start_idx
    
    while len(result_nodes) < count:
        result_nodes.add(self.ring[current_idx][1])
        current_idx = (current_idx + 1) % len(self.ring)
```

Il sistema trova il nodo primario e poi continua a percorrere l'anello in senso orario per trovare i nodi di replica richiesti.

## Operazioni Principali

### Operazione di GET

```python
@app.get("/key/{key}")
async def get_value(key: str):
    # Determina quali nodi dovrebbero avere questa chiave
    replica_nodes = get_replica_nodes(key)
    
    # Mischia i nodi replica per distribuire il carico
    nodes = random.sample(replica_nodes, len(replica_nodes))
    
    # Interroga i nodi finché non trova la chiave
    for node in nodes:
        response = await request_node(client, node, "GET", f"/key/{key}")
        if response.success:
            return KeyValueResponse(
                key=key,
                value=response.value["value"],
                replicas=len(replica_nodes),
                responses=[response]
            )
```

La lettura cerca la chiave sui nodi che dovrebbero contenerla secondo l'algoritmo di hashing, fermandosi al primo risultato positivo.

### Operazione di PUT

```python
@app.put("/key/{key}")
async def put_value(key: str, item: KeyValue):
    # Determina quali nodi dovrebbero avere questa chiave
    replica_nodes = get_replica_nodes(key)
    
    # Scrive su tutti i nodi di replica
    tasks = [request_node(client, node, "PUT", f"/key/{key}", json={"value": item.value}) 
             for node in replica_nodes]
    responses = await asyncio.gather(*tasks)
```

Le scritture avvengono in parallelo su tutti i nodi che dovrebbero contenere la chiave secondo l'algoritmo di hashing.

### Ribilanciamento

```python
@app.post("/rebalance")
async def rebalance_shards():
    # Per ogni chiave nel sistema
    for key in all_keys:
        # Determina dove dovrebbe essere la chiave
        target_nodes = get_replica_nodes(key)
        
        # Trova il valore attuale
        for node in KVS_NODES:
            response = await request_node(client, node, "GET", f"/key/{key}")
            if response.success:
                current_value = response.value["value"]
                
                # Rimuovi dalle posizioni non corrette
                if node not in target_nodes:
                    await request_node(client, node, "DELETE", f"/key/{key}")
                
                # Aggiungi alle posizioni corrette
                for target_node in target_nodes:
                    await request_node(client, target_node, "PUT", f"/key/{key}", 
                                      json={"value": current_value})
```

Il ribilanciamento riorganizza le chiavi quando cambia la configurazione dello sharding, assicurando che ogni chiave sia sui nodi corretti.

## Riconfigurazione

L'API supporta la modifica dei parametri di sharding a runtime:

```python
@app.post("/sharding/reconfigure")
async def reconfigure_sharding(config: ShardingConfig):
    global REPLICATION_FACTOR, VIRTUAL_NODES, hash_ring
    
    # Aggiorna la configurazione
    REPLICATION_FACTOR = config.replication_factor
    VIRTUAL_NODES = config.virtual_nodes
    
    # Ricostruisci l'hash ring
    hash_ring = ConsistentHashRing(KVS_NODES, VIRTUAL_NODES)
```

Dopo la riconfigurazione è necessario eseguire un ribilanciamento per allineare i dati alla nuova disposizione.

## Statistiche e Monitoraggio

Il coordinatore fornisce API per monitorare la distribuzione delle chiavi:

```python
@app.get("/sharding/info")
async def get_sharding_info():
    keys_distribution = {node: 0 for node in KVS_NODES}
    
    # Calcola la distribuzione delle chiavi
    for key in all_keys:
        replica_nodes = get_replica_nodes(key)
        for node in replica_nodes:
            keys_distribution[node] += 1
```

Queste statistiche sono fondamentali per verificare che l'algoritmo di sharding funzioni correttamente e che il carico sia ben distribuito.

## Vantaggi di questa Architettura

1. **Bilanciamento del carico**: Le chiavi sono distribuite uniformemente tra i nodi
2. **Minimizzazione della riorganizzazione**: Quando si aggiunge o rimuove un nodo, solo una frazione delle chiavi deve essere riassegnata
3. **Alta disponibilità**: La replicazione permette di tollerare il fallimento di alcuni nodi
4. **Configurabilità**: Il fattore di replica può essere adattato per bilanciare performance e ridondanza
5. **Scalabilità orizzontale**: È possibile aggiungere nuovi nodi con un impatto minimo sul sistema
