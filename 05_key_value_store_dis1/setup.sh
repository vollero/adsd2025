#!/bin/bash

# Configurazioni
DEFAULT_NODES=3
DEFAULT_QUORUM_SIZE=2
DEFAULT_PORT=8020

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Leggi i parametri di input
read -p "Numero di nodi KV Store da istanziare [default: $DEFAULT_NODES]: " NODES
NODES=${NODES:-$DEFAULT_NODES}

# Calcola il quorum predefinito (maggioranza)
DEFAULT_QUORUM_SIZE=$(( NODES / 2 + 1 ))
read -p "Dimensione del quorum [default: $DEFAULT_QUORUM_SIZE]: " QUORUM_SIZE
QUORUM_SIZE=${QUORUM_SIZE:-$DEFAULT_QUORUM_SIZE}

read -p "Porta su cui esporre il coordinatore [default: $DEFAULT_PORT]: " PORT
PORT=${PORT:-$DEFAULT_PORT}

# Verifica che il quorum non sia maggiore del numero di nodi
if [ $QUORUM_SIZE -gt $NODES ]; then
    echo -e "${RED}Errore: La dimensione del quorum ($QUORUM_SIZE) non può essere maggiore del numero di nodi ($NODES).${NC}"
    exit 1
fi

echo -e "${BLUE}Generazione del docker-compose.yml dinamico con $NODES nodi e quorum $QUORUM_SIZE...${NC}"

# Genera il file docker-compose.yml
cat > docker-compose.yml <<EOL
version: '3.8'

services:
  coordinator:
    build:
      context: .
      dockerfile: Dockerfile.coordinator
    ports:
      - "$PORT:8020"
    environment:
      - KVS_NODES=$(for i in $(seq 1 $NODES); do echo -n "kvstore$i:8050"; if [ $i -lt $NODES ]; then echo -n ","; fi; done)
      - QUORUM_SIZE=$QUORUM_SIZE
      - REQUEST_TIMEOUT=10
    depends_on:
$(for i in $(seq 1 $NODES); do echo "      - kvstore$i"; done)
    networks:
      - kvs_net
      - frontend_net
    restart: unless-stopped
    volumes:
      - coordinator_logs:/app/logs

EOL

# Aggiungi i servizi KV Store
for i in $(seq 1 $NODES); do
  cat >> docker-compose.yml <<EOL
  kvstore$i:
    build:
      context: .
      dockerfile: Dockerfile.kvstore
    volumes:
      - kvstore${i}_data:/app/data
    networks:
      - kvs_net
    restart: unless-stopped
    environment:
      - MAX_CACHE_ITEMS=1000
      - MAX_CACHE_SIZE_BYTES=10485760  # 10 MB
      - DB_FILE=/app/data/kv_store.db
      - LOG_FILE=/app/data/kv_store.log

EOL
done

# Aggiungi le reti e i volumi
cat >> docker-compose.yml <<EOL
networks:
  kvs_net:
    internal: true  # Questa rete non è accessibile dall'esterno
  frontend_net:
    # Questa rete è accessibile dall'esterno

volumes:
  coordinator_logs:
EOL

# Aggiungi i volumi per i nodi
for i in $(seq 1 $NODES); do
  echo "  kvstore${i}_data:" >> docker-compose.yml
done

# Crea i Dockerfile
echo -e "${BLUE}Creazione dei Dockerfile...${NC}"

# Dockerfile per kvstore
cat > Dockerfile.kvstore <<EOL
FROM python:3.9-slim

WORKDIR /app

# Installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia l'applicazione
COPY kvs_limited_cache_modified.py .

# Esponi la porta
EXPOSE 8050

# Comando di avvio
CMD ["python", "kvs_limited_cache_modified.py"]
EOL

# Dockerfile per coordinator
cat > Dockerfile.coordinator <<EOL
FROM python:3.9-slim

WORKDIR /app

# Installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia l'applicazione
COPY coordinator.py .

# Esponi la porta
EXPOSE 8000

# Comando di avvio
CMD ["python", "coordinator.py"]
EOL

echo -e "${GREEN}Preparazione completata! Per avviare il sistema, esegui:${NC}"
echo -e "${BLUE}docker-compose up -d${NC}"
echo -e "${GREEN}Il coordinatore sarà disponibile su http://localhost:$PORT${NC}"
