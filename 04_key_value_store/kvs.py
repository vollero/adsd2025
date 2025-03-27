import time
import sqlite3
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

# Configurazione del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='kv_store.log'
)
logger = logging.getLogger("kv_store")

# Modelli Pydantic
class KeyValue(BaseModel):
    value: Any

class StatusResponse(BaseModel):
    status: str
    message: str

# Cache in memoria
memory_cache: Dict[str, Any] = {}

# Lock per la sincronizzazione della cache
cache_lock = threading.RLock()

# Configurazione del database SQLite
DB_FILE = "kv_store.db"

def get_db_connection():
    """Crea una connessione al database SQLite"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inizializza il database creando la tabella se non esiste"""
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS kv_store (
        key TEXT PRIMARY KEY,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS kv_store_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT,
        value TEXT,
        operation TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Batch di operazioni per la sincronizzazione con il database
pending_operations: List[Tuple[str, str, str]] = []
batch_lock = threading.RLock()
batch_size_threshold = 10
last_batch_time = time.time()
batch_time_threshold = 60  # secondi

def add_to_batch(key: str, value: Optional[str], operation: str):
    """Aggiunge un'operazione al batch per la sincronizzazione con il database"""
    with batch_lock:
        pending_operations.append((key, value, operation))
        current_time = time.time()
        
        if (len(pending_operations) >= batch_size_threshold or 
                current_time - last_batch_time >= batch_time_threshold):
            return True
    return False

def sync_batch_to_db(background_tasks: BackgroundTasks):
    """Sincronizza il batch di operazioni con il database"""
    background_tasks.add_task(_sync_batch)

def _sync_batch():
    """Funzione di sincronizzazione del batch che viene eseguita in background"""
    global last_batch_time
    operations_to_process = []
    
    with batch_lock:
        if not pending_operations:
            return
            
        operations_to_process = pending_operations.copy()
        pending_operations.clear()
        last_batch_time = time.time()
    
    conn = get_db_connection()
    try:
        for key, value, operation in operations_to_process:
            if operation == "PUT":
                conn.execute(
                    "INSERT INTO kv_store (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                    "ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP",
                    (key, value, value)
                )
            elif operation == "DELETE":
                conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            
            # Registra l'operazione nella cronologia
            conn.execute(
                "INSERT INTO kv_store_history (key, value, operation) VALUES (?, ?, ?)",
                (key, value, operation)
            )
        
        conn.commit()
        logger.info(f"Sincronizzate {len(operations_to_process)} operazioni nel database")
    except Exception as e:
        conn.rollback()
        logger.error(f"Errore durante la sincronizzazione del batch: {e}")
    finally:
        conn.close()

# Lifespan 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice di startup
    init_db()
    
    # Carica i dati dal database nella cache
    conn = get_db_connection()
    rows = conn.execute("SELECT key, value FROM kv_store").fetchall()
    conn.close()
    
    with cache_lock:
        for row in rows:
            memory_cache[row["key"]] = row["value"]
    
    logger.info(f"Inizializzato il key-value store con {len(memory_cache)} chiavi dalla persistenza")
    
    yield  # Questo punto è dove l'applicazione viene eseguita
    
    # Codice di shutdown
    # Forza la sincronizzazione all'arresto
    background_tasks = BackgroundTasks()
    sync_batch_to_db(background_tasks)
    # Esegue la sincronizzazione in modo sincrono dato che il server sta per arrestarsi
    _sync_batch()
    logger.info("Key-value store arrestato correttamente")

# Inizializzazione FastAPI con lifespan
app = FastAPI(title="Key-Value Store Distribuito", lifespan=lifespan)

# Routes
@app.get("/")
async def root():
    return {"message": "Key-Value Store Distribuito"}

@app.get("/keys")
async def get_all_keys():
    """Ottiene tutte le chiavi presenti nel key-value store"""
    with cache_lock:
        return {"keys": list(memory_cache.keys())}

@app.get("/key/{key}")
async def get_value(key: str):
    """Ottiene il valore associato a una chiave"""
    logger.info(f"GET request for key: {key}")
    
    with cache_lock:
        if key in memory_cache:
            return {"key": key, "value": memory_cache[key]}
    
    # Se non è in cache, prova a cercarlo nel database
    conn = get_db_connection()
    value = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,)).fetchone()
    conn.close()
    
    if value:
        # Aggiorna la cache
        with cache_lock:
            memory_cache[key] = value["value"]
        return {"key": key, "value": value["value"]}
    
    raise HTTPException(status_code=404, detail=f"Key '{key}' not found")

@app.put("/key/{key}")
async def put_value(key: str, item: KeyValue, background_tasks: BackgroundTasks):
    """Inserisce o aggiorna un valore associato a una chiave"""
    logger.info(f"PUT request for key: {key} with value: {item.value}")
    
    # Aggiorna la cache
    with cache_lock:
        memory_cache[key] = item.value
    
    # Aggiunge l'operazione al batch
    value_str = str(item.value)
    if add_to_batch(key, value_str, "PUT"):
        sync_batch_to_db(background_tasks)
    
    return {"key": key, "value": item.value}

@app.delete("/key/{key}")
async def delete_value(key: str, background_tasks: BackgroundTasks):
    """Elimina una chiave e il suo valore associato"""
    logger.info(f"DELETE request for key: {key}")
    
    # Rimuove dalla cache
    with cache_lock:
        if key not in memory_cache:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        del memory_cache[key]
    
    # Aggiunge l'operazione al batch
    if add_to_batch(key, None, "DELETE"):
        sync_batch_to_db(background_tasks)
    
    return {"status": "success", "message": f"Key '{key}' deleted"}

@app.post("/force-sync")
async def force_sync(background_tasks: BackgroundTasks):
    """Forza la sincronizzazione del batch di operazioni con il database"""
    sync_batch_to_db(background_tasks)
    return {"status": "success", "message": "Batch synchronization initiated"}

@app.get("/stats")
async def get_stats():
    """Ottiene le statistiche del key-value store"""
    with cache_lock:
        cache_size = len(memory_cache)
    
    conn = get_db_connection()
    db_size = conn.execute("SELECT COUNT(*) as count FROM kv_store").fetchone()["count"]
    history_count = conn.execute("SELECT COUNT(*) as count FROM kv_store_history").fetchone()["count"]
    conn.close()
    
    with batch_lock:
        pending_count = len(pending_operations)
    
    return {
        "cache_size": cache_size,
        "db_size": db_size,
        "history_count": history_count,
        "pending_operations": pending_count
    }

# Esecuzione dell'applicazione
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
