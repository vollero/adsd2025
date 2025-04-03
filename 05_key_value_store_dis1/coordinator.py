import asyncio
import os
import logging
import random
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
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
    quorum_size: int
    responses: List[NodeResponse]

# Configurazione
KVS_NODES = os.environ.get("KVS_NODES", "").split(",")
QUORUM_SIZE = int(os.environ.get("QUORUM_SIZE", max(len(KVS_NODES) // 2 + 1, 1)))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 10))  # secondi

logger.info(f"Configurato coordinatore con {len(KVS_NODES)} nodi e quorum di {QUORUM_SIZE}")
logger.info(f"Nodi configurati: {KVS_NODES}")

# Inizializzazione FastAPI
app = FastAPI(title="KV Store Coordinator")

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

# Routes
@app.get("/")
async def root():
    return {"message": "KV Store Coordinator", "nodes": KVS_NODES, "quorum_size": QUORUM_SIZE}

@app.get("/keys")
async def get_all_keys():
    """Ottiene tutte le chiavi da almeno un nodo"""
    all_keys = set()
    
    async with httpx.AsyncClient() as client:
        for node in KVS_NODES:
            response = await request_node(client, node, "GET", "/keys")
            if response.success and response.value and "keys" in response.value:
                all_keys.update(response.value["keys"])
    
    return {"keys": list(all_keys)}

@app.get("/key/{key}")
async def get_value(key: str):
    """Ottiene il valore associato a una chiave con quorum"""
    if not KVS_NODES:
        raise HTTPException(status_code=500, detail="Nessun nodo KV Store configurato")
    
    # Mischia i nodi per distribuire il carico
    nodes = random.sample(KVS_NODES, len(KVS_NODES))
    successful_responses = []
    node_responses = []
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "GET", f"/key/{key}") for node in nodes]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            node_responses.append(response)
            if response.success:
                successful_responses.append(response)
                
                # Se abbiamo raggiunto il quorum, possiamo interrompere
                if len(successful_responses) >= QUORUM_SIZE:
                    break
    
    # Verifica se abbiamo raggiunto il quorum
    if len(successful_responses) < QUORUM_SIZE:
        raise HTTPException(
            status_code=404, 
            detail=f"Quorum non raggiunto per la chiave '{key}'. Ottenute {len(successful_responses)} risposte su {QUORUM_SIZE} richieste."
        )
    
    # Estrai il valore dal primo nodo che ha risposto con successo
    value = successful_responses[0].value["value"]
    
    return KeyValueResponse(
        key=key,
        value=value,
        quorum_size=QUORUM_SIZE,
        responses=node_responses
    )

@app.put("/key/{key}")
async def put_value(key: str, item: KeyValue, background_tasks: BackgroundTasks):
    """Inserisce o aggiorna un valore su tutti i nodi (replicazione completa)"""
    if not KVS_NODES:
        raise HTTPException(status_code=500, detail="Nessun nodo KV Store configurato")
    
    successful_writes = 0
    node_responses = []
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "PUT", f"/key/{key}", json={"value": item.value}) for node in KVS_NODES]
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
    
    # Se non abbiamo scritto su tutti i nodi, pianifica riprova in background
    if successful_writes < len(KVS_NODES):
        logger.warning(f"Chiave '{key}' scritta solo su {successful_writes}/{len(KVS_NODES)} nodi. Pianificazione riprova...")
        # In una implementazione reale, qui aggiungeresti un task di background per riprovare con i nodi falliti
    
    return KeyValueResponse(
        key=key,
        value=item.value,
        quorum_size=successful_writes,
        responses=node_responses
    )

@app.delete("/key/{key}")
async def delete_value(key: str):
    """Elimina una chiave da tutti i nodi"""
    if not KVS_NODES:
        raise HTTPException(status_code=500, detail="Nessun nodo KV Store configurato")
    
    successful_deletes = 0
    node_responses = []
    
    async with httpx.AsyncClient() as client:
        tasks = [request_node(client, node, "DELETE", f"/key/{key}") for node in KVS_NODES]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            node_responses.append(response)
            if response.success:
                successful_deletes += 1
    
    # Verifica se la cancellazione è avvenuta con successo su almeno un nodo
    if successful_deletes == 0:
        raise HTTPException(
            status_code=404, 
            detail=f"Chiave '{key}' non trovata su alcun nodo o errore durante la cancellazione."
        )
    
    return StatusResponse(
        status="success", 
        message=f"Chiave '{key}' cancellata con successo da {successful_deletes}/{len(KVS_NODES)} nodi."
    )

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
    
    return {
        "coordinator": {
            "nodes_configured": len(KVS_NODES),
            "nodes_responding": len(node_stats),
            "quorum_size": QUORUM_SIZE
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

# Punto di ingresso
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
