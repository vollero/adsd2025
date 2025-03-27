import time
import sqlite3
import logging
import threading
import sys
from typing import Dict, Any, Optional, List, Tuple, OrderedDict
from collections import OrderedDict
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

# Configurazione limiti cache
MAX_CACHE_ITEMS = 1000  # Numero massimo di elementi in cache
MAX_CACHE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB in bytes
current_cache_size = 0  # Dimensione attuale della cache in bytes

# Cache in memoria con LRU (Least Recently Used)
class LRUCache:
    def __init__(self, max_items=1000, max_size_bytes=10*1024*1024):
        self.cache = OrderedDict()
        self.max_items = max_items
        self.max_size_bytes = max_size_bytes
        self.current_size_bytes = 0
        self.lock = threading.RLock()
    
    def get(self, key):
        """Ottiene un valore dalla cache, aggiorna l'ordine LRU"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Sposta l'elemento alla fine (più recentemente usato)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
    
    def put(self, key, value):
        """Inserisce un valore nella cache, rispettando i limiti"""
        with self.lock:
            # Se la chiave esiste già, rimuovila prima di inserirla di nuovo
            if key in self.cache:
                old_value = self.cache.pop(key)
                self.current_size_bytes -= self._get_item_size(key, old_value)
            
            # Calcola la dimensione del nuovo elemento
            new_item_size = self._get_item_size(key, value)
            
            # Verifica se la dimensione del nuovo elemento è accettabile
            if new_item_size > self.max_size_bytes:
                logger.warning(f"L'elemento con chiave '{key}' è troppo grande per la cache ({new_item_size} bytes)")
                return False
            
            # Rimuovi elementi finché non c'è abbastanza spazio
            while (len(self.cache) >= self.max_items or 
                   self.current_size_bytes + new_item_size > self.max_size_bytes) and self.cache:
                oldest_key, oldest_value = self.cache.popitem(last=False)
                oldest_size = self._get_item_size(oldest_key, oldest_value)
                self.current_size_bytes -= oldest_size
                logger.debug(f"Rimosso dalla cache l'elemento '{oldest_key}' ({oldest_size} bytes)")
            
            # Inserisci il nuovo elemento
            self.cache[key] = value
            self.current_size_bytes += new_item_size
            return True
    
    def delete(self, key):
        """Elimina un elemento dalla cache"""
        with self.lock:
            if key in self.cache:
                value = self.cache.pop(key)
                self.current_size_bytes -= self._get_item_size(key, value)
                return True
            return False
    
    def _get_item_size(self, key, value):
        """Stima la dimensione in bytes di un elemento in cache"""
        # Questa è una stima approssimativa, la dimensione reale dipende da molti fattori
        key_size = sys.getsizeof(key)
        value_size = sys.getsizeof(value)
        return key_size + value_size
    
    def keys(self):
        """Restituisce tutte le chiavi nella cache"""
        with self.lock:
            return list(self.cache.keys())
    
    def clear(self):
        """Svuota la cache"""
        with self.lock:
            self.cache.clear()
            self.current_size_bytes = 0
    
    def get_stats(self):
        """Restituisce statistiche sulla cache"""
        with self.lock:
            return {
                "items_count": len(self.cache),
                "max_items": self.max_items,
                "size_bytes": self.current_size_bytes,
                "max_size_bytes": self.max_size_bytes,
                "utilization_percent": round((self.current_size_bytes / self.max_size_bytes) * 100, 2) if self.max_size_bytes > 0 else 0
            }

# Inizializzazione della cache
memory_cache = LRUCache(max_items=MAX_CACHE_ITEMS, max_size_bytes=MAX_CACHE_SIZE_BYTES)

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

# Lifespan (sostituzione di on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice di startup
    init_db()
    
    # Carica i dati dal database nella cache
    conn = get_db_connection()
    rows = conn.execute("SELECT key, value FROM kv_store").fetchall()
    conn.close()
    
    for row in rows:
        memory_cache.put(row["key"], row["value"])
    
    logger.info(f"Inizializzato il key-value store con {len(memory_cache.keys())} chiavi dalla persistenza")
    
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
    return {"keys": memory_cache.keys()}

@app.get("/key/{key}")
async def get_value(key: str):
    """Ottiene il valore associato a una chiave"""
    logger.info(f"GET request for key: {key}")
    
    value = memory_cache.get(key)
    if value is not None:
        return {"key": key, "value": value}
    
    # Se non è in cache, prova a cercarlo nel database
    conn = get_db_connection()
    db_value = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,)).fetchone()
    conn.close()
    
    if db_value:
        # Aggiorna la cache
        value = db_value["value"]
        memory_cache.put(key, value)
        return {"key": key, "value": value}
    
    raise HTTPException(status_code=404, detail=f"Key '{key}' not found")

@app.put("/key/{key}")
async def put_value(key: str, item: KeyValue, background_tasks: BackgroundTasks):
    """Inserisce o aggiorna un valore associato a una chiave"""
    logger.info(f"PUT request for key: {key} with value: {item.value}")
    
    # Aggiorna la cache
    value_str = str(item.value)
    cache_result = memory_cache.put(key, item.value)
    if not cache_result:
        logger.warning(f"Valore troppo grande per la cache, memorizzato solo nel database: {key}")
    
    # Aggiunge l'operazione al batch
    if add_to_batch(key, value_str, "PUT"):
        sync_batch_to_db(background_tasks)
    
    return {"key": key, "value": item.value}

@app.delete("/key/{key}")
async def delete_value(key: str, background_tasks: BackgroundTasks):
    """Elimina una chiave e il suo valore associato"""
    logger.info(f"DELETE request for key: {key}")
    
    # Rimuove dalla cache
    if not memory_cache.delete(key):
        # Verifica se esiste nel database
        conn = get_db_connection()
        db_value = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,)).fetchone()
        conn.close()
        
        if not db_value:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    
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
    cache_stats = memory_cache.get_stats()
    
    conn = get_db_connection()
    db_size = conn.execute("SELECT COUNT(*) as count FROM kv_store").fetchone()["count"]
    history_count = conn.execute("SELECT COUNT(*) as count FROM kv_store_history").fetchone()["count"]
    conn.close()
    
    with batch_lock:
        pending_count = len(pending_operations)
    
    return {
        "cache": cache_stats,
        "db_size": db_size,
        "history_count": history_count,
        "pending_operations": pending_count
    }

@app.post("/clear-cache")
async def clear_cache():
    """Svuota la cache"""
    memory_cache.clear()
    return {"status": "success", "message": "Cache cleared"}

# Esecuzione dell'applicazione
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
