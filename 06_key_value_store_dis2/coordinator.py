import asyncio
import os
import logging
import random
import hashlib
import bisect
from typing import Dict, List, Any, Optional, Tuple, Set
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
import httpx

# Configurazione del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='coordinator.log'
)
logger = logging.getLogger("coordinator")

# Modelli Pydantic
class KeyValue(BaseModel):
    value: Any

class StatusResponse(BaseModel):
    status: str
    message: str

class NodeResponse(BaseModel):
    node: str
    success: bool
    value: Optional[Any] = None
    error: Optional[str] = None

class KeyValueResponse(BaseModel):
    key: str
    value: Any
    replicas: int
    responses: List[NodeResponse]

class ShardingConfig(BaseModel):
    replication_factor: float  # Percentuale di nodi su cui replicare (0.0-1.0)
    virtual_nodes: int  # Numero di nodi virtuali per nodo fisico

class HashRingNode(BaseModel):
    node: str
    position: int

class ShardingInfo(BaseModel):
    total_nodes: int
    replication_factor: float
    virtual_nodes_per_node: int 
    total_virtual_nodes: int
    key_distribution: Dict[str, int]  # nodo -> conteggio chiavi

# Configurazione
KVS_NODES = os.environ.get("KVS_NODES", "").split(",")
# Replication factor è la percentuale di nodi su cui replicare ogni chiave (0.0-1.0)
REPLICATION_FACTOR = float(os.environ.get("REPLICATION_FACTOR", "0.5"))
# Ogni nodo fisico avrà questo numero di nodi virtuali nell'hash ring
VIRTUAL_NODES = int(os.environ.get("VIRTUAL_NODES", "100"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 10))  # secondi

# Validazione della configurazione
if REPLICATION_FACTOR <= 0 or REPLICATION_FACTOR > 1:
    logger.error(f"REPLICATION_FACTOR deve essere tra 0 e 1, ricevuto: {REPLICATION_FACTOR}")
    REPLICATION_FACTOR = max(0.1, min(1.0, REPLICATION_FACTOR))  # Fallback a un valore valido

logger.info(f"Configurato coordinatore con {len(KVS_NODES)} nodi, fattore di replica {REPLICATION_FACTOR}")
logger.info(f"Nodi configurati: {KVS_NODES}")

# Consistent Hashing Ring
class ConsistentHashRing:
    def __init__(self, nodes: List[str], virtual_nodes: int = 100):
        self.ring: List[Tuple[int, str]] = []  # (position, node)
        self.virtual_nodes = virtual_nodes
        self.nodes = set(nodes)
        
        self._build_ring()
    
    def _build_ring(self):
        """Costruisce l'hash ring con nodi virtuali"""
        self.ring = []
        for node in self.nodes:
            for i in range(self.virtual_nodes):
                key = f"{node}:{i}"
                position = self._hash(key)
                self.ring.append((position, node))
        
        # Ordina l'anello per posizione
        self.ring.sort(key=lambda x: x[0])
        logger.info(f"Hash ring costruito con {len(self.ring)} nodi virtuali")
    
    def _hash(self, key: str) -> int:
        """Calcola l'hash di una chiave"""
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)
    
    def get_node(self, key: str) -> str:
        """Trova il nodo responsabile per una chiave"""
        if not self.ring:
            raise ValueError("Hash ring vuoto")
        
        hash_key = self._hash(key)
        
        # Trova il primo nodo con posizione >= hash_key
        for position, node in self.ring:
            if position >= hash_key:
                return node
        
        # Se non trovato, torna al primo nodo (giro circolare)
        return self.ring[0][1]
    
    def get_nodes(self, key: str, count: int) -> List[str]:
        """Trova 'count' nodi responsabili per una chiave, iniziando dal nodo primario"""
        if not self.ring:
            raise ValueError("Hash ring vuoto")
        
        if count > len(self.nodes):
            count = len(self.nodes)
        
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
            
            # Se abbiamo fatto il giro completo senza trovare abbastanza nodi unici
            if current_idx == start_idx:
                break
        
        return list(result_nodes)
    
    def add_node(self, node: str):
        """Aggiunge un nodo all'hash ring"""
        if node in self.nodes:
            return
        
        self.nodes.add(node)
        for i in range(self.virtual_nodes):
            key = f"{node}:{i}"
            position = self._hash(key)
            # Insertion sort per mantenere l'ordine
            index = bisect.bisect_left([pos for pos, _ in self.ring], position)
            self.ring.insert(index, (position, node))
    
    def remove_node(self, node: str):
        """Rimuove un nodo dall'hash ring"""
        if node not in self.nodes:
            return
        
        self.nodes.remove(node)
        self.ring = [(pos, n) for pos, n in self.ring if n != node]
    
    def get_ring(self) -> List[HashRingNode]:
        """Restituisce l'anello come lista di nodi"""
        return [HashRingNode(node=node, position=position) for position, node in self.ring]
    
    def get_node_distribution(self) -> Dict[str, int]:
        """Restituisce la distribuzione dei nodi nell'anello"""
        result = {}
        for _, node in self.ring:
            if node in result:
                result[node] += 1
            else:
                result[node] = 1
        return result

# Inizializzazione dell'hash ring
hash_ring = ConsistentHashRing(KVS_NODES, VIRTUAL_NODES)

# Inizializzazione FastAPI
app = FastAPI(title="KV Store Coordinator con Sharding")

# Funzioni di utilità
async def request_node(client: httpx.AsyncClient, node: str, method: str, endpoint: str, 
                      json: Dict = None) -> NodeResponse:
    """Esegue una richiesta a un nodo specifico del KV store"""
    try:
        if method.upper() == "GET":
            response = await client.get(f"http://{node}{endpoint}", timeout=REQUEST_TIMEOUT)
        elif method.upper() == "PUT":
            response = await client.put(f"http://{node}{endpoint}", json=json, timeout=REQUEST_TIMEOUT)
        elif method.upper() == "DELETE":
            response = await client.delete(f"http://{node}{endpoint}", timeout=REQUEST_TIMEOUT)
        else:
            return NodeResponse(node=node, success=False, error=f"Metodo non supportato: {method}")
        
        if response.status_code >= 200 and response.status_code < 300:
            return NodeResponse(node=node, success=True, value=response.json())
        else:
            return NodeResponse(node=node, success=False, error=f"Errore {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Errore durante la richiesta al nodo {node}: {str(e)}")
        return NodeResponse(node=node, success=False, error=str(e))

def get_replica_nodes(key: str) -> List[str]:
    """Determina quali nodi dovrebbero contenere una chiave in base al consistent hashing"""
    # Calcola quanti nodi devono avere la replica
    replica_count = max(1, round(len(KVS_NODES) * REPLICATION_FACTOR))
    return hash_ring.get_nodes(key, replica_count)

# Routes
@app.get("/")
async def root():
    return {
        "message": "KV Store Coordinator con Sharding",
        "nodes": KVS_NODES, 
        "replication_factor": REPLICATION_FACTOR,
        "virtual_nodes": VIRTUAL_NODES
    }

@app.get("/sharding/info")
async def get_sharding_info():
    """Ottiene informazioni sulla configurazione dello sharding"""
    # Costruisci una mappa di distribuzione delle chiavi
    keys_distribution = {node: 0 for node in KVS_NODES}
    
    # Ottieni tutte le chiavi
    all_keys = set()
    async with httpx.AsyncClient() as client:
        for node in KVS_NODES:
            response = await request_node(client, node, "GET", "/keys")
            if response.success and response.value and "keys" in response.value:
                all_keys.update(response.value["keys"])
    
    # Calcola la distribuzione delle chiavi
    for key in all_keys:
        replica_nodes = get_replica_nodes(key)
        for node in replica_nodes:
            if node in keys_distribution:
                keys_distribution[node] += 1
    
    return ShardingInfo(
        total_nodes=len(KVS_NODES),
        replication_factor=REPLICATION_FACTOR,
        virtual_nodes_per_node=VIRTUAL_NODES,
        total_virtual_nodes=len(hash_ring.get_ring()),
        key_distribution=keys_distribution
    )

@app.get("/keys")
async def get_all_keys():
    """Ottiene tutte le chiavi da tutti i nodi"""
    all_keys = set()
    
    async with httpx.AsyncClient() as client:
        for node in KVS_NODES:
            response = await request_node(client, node, "GET", "/keys")
            if response.success and response.value and "keys" in response.value:
                all_keys.update(response.value["keys"])
    
    return {"keys": list(all_keys)}

@app.get("/key/{key}")
async def get_value(key: str):
    """Ottiene il valore associato a una chiave dai nodi replicati"""
    if not KVS_NODES:
        raise HTTPException(status_code=500, detail="Nessun nodo KV Store configurato")
    
    # Determina quali nodi dovrebbero avere questa chiave
    replica_nodes = get_replica_nodes(key)
    
    if not replica_nodes:
        raise HTTPException(status_code=500, detail="Impossibile determinare i nodi per la chiave")
    
    # Mischia i nodi replica per distribuire il carico
    nodes = random.sample(replica_nodes, len(replica_nodes))
    successful_responses = []
    node_responses = []
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "GET", f"/key/{key}") for node in nodes]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            node_responses.append(response)
            if response.success:
                successful_responses.append(response)
                # Se abbiamo ottenuto almeno una risposta positiva, possiamo interrompere
                break
    
    # Verifica se abbiamo trovato il valore
    if not successful_responses:
        # Se non troviamo la chiave nei nodi in cui dovrebbe essere, proviamo in tutti gli altri
        # Questo può accadere se la configurazione dei nodi è cambiata dopo che la chiave è stata scritta
        other_nodes = [node for node in KVS_NODES if node not in nodes]
        if other_nodes:
            async with httpx.AsyncClient() as client:
                tasks = [request_node(client, node, "GET", f"/key/{key}") for node in other_nodes]
                responses = await asyncio.gather(*tasks)
                
                for response in responses:
                    node_responses.append(response)
                    if response.success:
                        successful_responses.append(response)
                        # Trovata la chiave in un nodo non previsto
                        logger.warning(f"Chiave '{key}' trovata in un nodo non previsto: {response.node}")
                        break
        
        if not successful_responses:
            raise HTTPException(
                status_code=404, 
                detail=f"Chiave '{key}' non trovata in alcun nodo."
            )
    
    # Estrai il valore dal primo nodo che ha risposto con successo
    value = successful_responses[0].value["value"]
    
    return KeyValueResponse(
        key=key,
        value=value,
        replicas=len(replica_nodes),
        responses=node_responses
    )

@app.put("/key/{key}")
async def put_value(key: str, item: KeyValue, background_tasks: BackgroundTasks):
    """Inserisce o aggiorna un valore sui nodi replicati"""
    if not KVS_NODES:
        raise HTTPException(status_code=500, detail="Nessun nodo KV Store configurato")
    
    # Determina quali nodi dovrebbero avere questa chiave
    replica_nodes = get_replica_nodes(key)
    
    if not replica_nodes:
        raise HTTPException(status_code=500, detail="Impossibile determinare i nodi per la chiave")
    
    successful_writes = 0
    node_responses = []
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "PUT", f"/key/{key}", json={"value": item.value}) for node in replica_nodes]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            node_responses.append(response)
            if response.success:
                successful_writes += 1
    
    # Verifica se la scrittura è avvenuta con successo su almeno un nodo
    if successful_writes == 0:
        raise HTTPException(
            status_code=500, 
            detail=f"Impossibile scrivere la chiave '{key}' su alcun nodo."
        )
    
    # Se non abbiamo scritto su tutti i nodi, registro un avviso
    if successful_writes < len(replica_nodes):
        logger.warning(f"Chiave '{key}' scritta solo su {successful_writes}/{len(replica_nodes)} nodi.")
    
    return KeyValueResponse(
        key=key,
        value=item.value,
        replicas=successful_writes,
        responses=node_responses
    )

@app.delete("/key/{key}")
async def delete_value(key: str):
    """Elimina una chiave da tutti i nodi che dovrebbero averla"""
    if not KVS_NODES:
        raise HTTPException(status_code=500, detail="Nessun nodo KV Store configurato")
    
    # Determina quali nodi dovrebbero avere questa chiave
    replica_nodes = get_replica_nodes(key)
    
    if not replica_nodes:
        raise HTTPException(status_code=500, detail="Impossibile determinare i nodi per la chiave")
    
    successful_deletes = 0
    node_responses = []
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "DELETE", f"/key/{key}") for node in replica_nodes]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            node_responses.append(response)
            if response.success:
                successful_deletes += 1
    
    # Se non abbiamo trovato la chiave in nessun nodo previsto, cerchiamo in tutti gli altri
    if successful_deletes == 0:
        other_nodes = [node for node in KVS_NODES if node not in replica_nodes]
        if other_nodes:
            async with httpx.AsyncClient() as client:
                tasks = [request_node(client, node, "DELETE", f"/key/{key}") for node in other_nodes]
                responses = await asyncio.gather(*tasks)
                
                for response in responses:
                    node_responses.append(response)
                    if response.success:
                        successful_deletes += 1
    
    if successful_deletes == 0:
        raise HTTPException(
            status_code=404, 
            detail=f"Chiave '{key}' non trovata su alcun nodo o errore durante la cancellazione."
        )
    
    return StatusResponse(
        status="success", 
        message=f"Chiave '{key}' cancellata con successo da {successful_deletes} nodi."
    )

@app.post("/sharding/reconfigure")
async def reconfigure_sharding(config: ShardingConfig):
    """Riconfigura lo sharding (fattore di replica e nodi virtuali)"""
    global REPLICATION_FACTOR, VIRTUAL_NODES, hash_ring
    
    # Validazione
    if config.replication_factor <= 0 or config.replication_factor > 1:
        raise HTTPException(
            status_code=400, 
            detail=f"replication_factor deve essere tra 0 e 1, ricevuto: {config.replication_factor}"
        )
    
    if config.virtual_nodes < 1:
        raise HTTPException(
            status_code=400, 
            detail=f"virtual_nodes deve essere almeno 1, ricevuto: {config.virtual_nodes}"
        )
    
    # Aggiorna la configurazione
    old_replication = REPLICATION_FACTOR
    old_virtual_nodes = VIRTUAL_NODES
    
    REPLICATION_FACTOR = config.replication_factor
    VIRTUAL_NODES = config.virtual_nodes
    
    # Ricostruisci l'hash ring
    hash_ring = ConsistentHashRing(KVS_NODES, VIRTUAL_NODES)
    
    logger.info(f"Sharding riconfigurato: replication_factor da {old_replication} a {REPLICATION_FACTOR}, "
                f"virtual_nodes da {old_virtual_nodes} a {VIRTUAL_NODES}")
    
    return {
        "status": "success",
        "message": "Configurazione sharding aggiornata",
        "old_config": {"replication_factor": old_replication, "virtual_nodes": old_virtual_nodes},
        "new_config": {"replication_factor": REPLICATION_FACTOR, "virtual_nodes": VIRTUAL_NODES}
    }

@app.post("/sharding/add-node/{node}")
async def add_node(node: str):
    """Aggiunge un nodo al sistema di sharding"""
    if node in KVS_NODES:
        return {"status": "warning", "message": f"Il nodo {node} è già nel sistema"}
    
    # Aggiungi il nodo alla lista
    KVS_NODES.append(node)
    
    # Aggiungi il nodo all'hash ring
    hash_ring.add_node(node)
    
    logger.info(f"Aggiunto nodo {node} al sistema di sharding")
    
    return {"status": "success", "message": f"Nodo {node} aggiunto al sistema"}

@app.post("/sharding/remove-node/{node}")
async def remove_node(node: str):
    """Rimuove un nodo dal sistema di sharding"""
    if node not in KVS_NODES:
        return {"status": "warning", "message": f"Il nodo {node} non è nel sistema"}
    
    # Rimuovi il nodo dalla lista
    KVS_NODES.remove(node)
    
    # Rimuovi il nodo dall'hash ring
    hash_ring.remove_node(node)
    
    logger.info(f"Rimosso nodo {node} dal sistema di sharding")
    
    return {"status": "success", "message": f"Nodo {node} rimosso dal sistema"}

@app.get("/sharding/node-for-key/{key}")
async def get_node_for_key(key: str):
    """Restituisce i nodi responsabili per una chiave specifica"""
    replica_nodes = get_replica_nodes(key)
    return {
        "key": key,
        "responsible_nodes": replica_nodes,
        "replica_count": len(replica_nodes)
    }

@app.get("/sharding/ring")
async def get_ring():
    """Ottiene l'hash ring con le posizioni dei nodi"""
    nodes = hash_ring.get_ring()
    distribution = hash_ring.get_node_distribution()
    
    return {
        "total_nodes": len(KVS_NODES),
        "virtual_nodes": len(nodes),
        "ring": [{"node": node.node, "position": node.position} for node in nodes[:100]],  # Limitato a 100 per leggibilità
        "distribution": distribution
    }

@app.get("/sharding/node-keys/{node}")
async def get_node_keys(node: str):
    """Ottiene le chiavi presenti su un nodo specifico"""
    if node not in KVS_NODES:
        raise HTTPException(status_code=404, detail=f"Nodo '{node}' non trovato")
    
    async with httpx.AsyncClient() as client:
        response = await request_node(client, node, "GET", "/keys")
        
        if not response.success:
            raise HTTPException(
                status_code=500, 
                detail=f"Errore durante il recupero delle chiavi dal nodo {node}: {response.error}"
            )
    
    node_keys = response.value.get("keys", [])
    return {
        "node": node,
        "keys_count": len(node_keys),
        "keys": node_keys
    }

@app.get("/stats")
async def get_stats():
    """Ottiene le statistiche da tutti i nodi"""
    node_stats = {}
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "GET", "/stats") for node in KVS_NODES]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            if response.success:
                node_stats[response.node] = response.value
    
    # Calcola metriche di sharding
    ring_stats = hash_ring.get_node_distribution()
    
    return {
        "coordinator": {
            "nodes_configured": len(KVS_NODES),
            "nodes_responding": len(node_stats),
            "replication_factor": REPLICATION_FACTOR,
            "virtual_nodes": VIRTUAL_NODES
        },
        "sharding": {
            "virtual_node_distribution": ring_stats
        },
        "nodes": node_stats
    }

@app.post("/force-sync")
async def force_sync():
    """Forza la sincronizzazione su tutti i nodi"""
    results = []
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "POST", "/force-sync") for node in KVS_NODES]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            results.append(response)
    
    return {
        "status": "completed",
        "message": f"Sincronizzazione forzata completata su {sum(1 for r in results if r.success)}/{len(KVS_NODES)} nodi.",
        "results": results
    }

@app.post("/rebalance")
async def rebalance_shards():
    """Ribilancia le chiavi tra i nodi secondo l'attuale configurazione dello sharding"""
    # Prima ottieni tutte le chiavi esistenti
    all_keys = set()
    async with httpx.AsyncClient() as client:
        for node in KVS_NODES:
            response = await request_node(client, node, "GET", "/keys")
            if response.success and response.value and "keys" in response.value:
                all_keys.update(response.value["keys"])
    
    # Calcola la nuova distribuzione delle chiavi
    key_nodes_map = {}
    for key in all_keys:
        key_nodes_map[key] = get_replica_nodes(key)
    
    # Per ogni chiave, assicurati che sia sui nodi corretti
    rebalanced_keys = 0
    total_operations = 0
    failed_operations = 0
    
    async with httpx.AsyncClient() as client:
        # Per ogni chiave, controlla dove è attualmente
        for key in all_keys:
            target_nodes = key_nodes_map[key]
            value_found = False
            current_value = None
            
            # Cerca il valore della chiave nei nodi attuali
            for node in KVS_NODES:
                response = await request_node(client, node, "GET", f"/key/{key}")
                total_operations += 1
                
                if response.success:
                    value_found = True
                    current_value = response.value["value"]
                    
                    # Verifica se il nodo dovrebbe avere questa chiave
                    if node not in target_nodes:
                        # Rimuovi la chiave da questo nodo
                        delete_resp = await request_node(client, node, "DELETE", f"/key/{key}")
                        total_operations += 1
                        if not delete_resp.success:
                            failed_operations += 1
                            logger.warning(f"Impossibile rimuovere la chiave '{key}' dal nodo {node}")
                    
                    break
            
            if value_found and current_value is not None:
                # Aggiungi la chiave ai nodi che dovrebbero averla
                for node in target_nodes:
                    # Verifica se la chiave è già presente
                    check_resp = await request_node(client, node, "GET", f"/key/{key}")
                    total_operations += 1
                    
                    if not check_resp.success:
                        # Aggiungi la chiave a questo nodo
                        put_resp = await request_node(client, node, "PUT", f"/key/{key}", json={"value": current_value})
                        total_operations += 1
                        
                        if put_resp.success:
                            rebalanced_keys += 1
                        else:
                            failed_operations += 1
                            logger.warning(f"Impossibile aggiungere la chiave '{key}' al nodo {node}")
    
    return {
        "status": "completed",
        "message": f"Ribilanciamento completato: {rebalanced_keys} chiavi ribilanciate, {failed_operations} operazioni fallite",
        "details": {
            "total_keys": len(all_keys),
            "rebalanced_keys": rebalanced_keys,
            "total_operations": total_operations,
            "failed_operations": failed_operations
        }
    }

# Punto di ingresso
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
