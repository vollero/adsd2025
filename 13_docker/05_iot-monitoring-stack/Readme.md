# Esempio Avanzato: Architettura di Monitoraggio IoT con Docker Compose

Questo esempio dimostra come costruire un sistema di monitoraggio per sensori virtuali utilizzando Docker Compose per orchestrare vari servizi.

**Architettura Proposta:**

1.  **InfluxDB (Database):** Database time-series per memorizzare i dati dei sensori.
2.  **Sensore Virtuale (Applicazione):** Container Python che simula sensori e invia dati a InfluxDB.
3.  **Grafana (Visualizzazione/Monitoraggio):** Strumento per creare dashboard e visualizzare i dati dei sensori da InfluxDB.
4.  **Portainer (Gestione Container):** Interfaccia utente per la gestione di Docker.

Tutti i servizi sono orchestrati da un singolo file `docker-compose.yml`.

---

**Struttura della Cartella del Progetto:**

```
iot-monitoring-stack/
├── virtual-sensor/
│   ├── sensor.py
│   ├── requirements.txt
│   └── Dockerfile
├── grafana-provisioning/
│   └── datasources/
│       
└── influxdb-datasource.yml
└── docker-compose.yml
```

---

**Contenuto dei File:**

**1. `docker-compose.yml`**

```yaml
version: '3.8'

services:
  influxdb:
    image: influxdb:2.7 # Specifica una versione stabile di InfluxDB 2.x
    container_name: influxdb_server
    ports:
      - "8086:8086" # Porta API e UI di InfluxDB
    volumes:
      - influxdb_data:/var/lib/influxdb2 # Persistenza dei dati di InfluxDB
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin          # Sostituisci con il tuo utente
      - DOCKER_INFLUXDB_INIT_PASSWORD=password123    # Sostituisci con una password robusta!
      - DOCKER_INFLUXDB_INIT_ORG=my-iot-org          # Sostituisci con la tua organizzazione
      - DOCKER_INFLUXDB_INIT_BUCKET=iot_bucket       # Sostituisci con il nome del tuo bucket
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=mysecretadmintoken # Sostituisci con un token sicuro!
    restart: unless-stopped
    networks:
      - iot_network

  virtual_sensor:
    build:
      context: ./virtual-sensor # Percorso alla cartella del Dockerfile del sensore
    container_name: virtual_sensor_1
    depends_on:
      - influxdb # Il sensore si avvia dopo InfluxDB
    environment:
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN=mysecretadmintoken # Deve corrispondere a DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
      - INFLUXDB_ORG=my-iot-org           # Deve corrispondere a DOCKER_INFLUXDB_INIT_ORG
      - INFLUXDB_BUCKET=iot_bucket        # Deve corrispondere a DOCKER_INFLUXDB_INIT_BUCKET
      - SENSOR_ID=sensor_alpha_001
      - REPORT_INTERVAL=10 # Intervallo di invio dati in secondi
    restart: unless-stopped
    networks:
      - iot_network

  grafana:
    image: grafana/grafana:10.4.2 # Specifica una versione stabile
    container_name: grafana_dashboard
    ports:
      - "3000:3000" # Porta UI di Grafana
    volumes:
      - grafana_data:/var/lib/grafana # Persistenza dei dati di Grafana
      - ./grafana-provisioning/datasources:/etc/grafana/provisioning/datasources # Provisioning del datasource
    environment:
      - GF_SECURITY_ADMIN_USER=admin         # Utente admin di Grafana
      - GF_SECURITY_ADMIN_PASSWORD=grafanapass # Password admin di Grafana (cambiala!)
    depends_on:
      - influxdb # Grafana si avvia dopo InfluxDB
    restart: unless-stopped
    networks:
      - iot_network

  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer_ui
    ports:
      - "9443:9443" # Porta HTTPS di Portainer
      - "9000:9000" # Porta HTTP di Portainer (opzionale, se preferisci HTTP)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock # Permette a Portainer di gestire Docker
      - portainer_data:/data # Persistenza dei dati di Portainer
    restart: unless-stopped

volumes:
  influxdb_data:
  grafana_data:
  portainer_data:

networks:
  iot_network:
    driver: bridge
```


**2. `virtual-sensor/Dockerfile`**

```dockerfile
# Usa un'immagine Python leggera
FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia il file delle dipendenze
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia lo script del sensore
COPY sensor.py .

# Comando per eseguire lo script del sensore quando il container parte
CMD ["python", "-u", "sensor.py"]
```


**3. `virtual-sensor/requirements.txt`***

```txt
influxdb-client==1.39.0
python-dotenv==0.21.0
schedule==1.2.0
```

**4. `virtual-sensor/sensor.py`**

```python
import os
import time
import random
import schedule
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configurazione Iniziale ---
# Carica le configurazioni dalle variabili d'ambiente
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'my-token') # Token di InfluxDB
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'my-org')       # Organizzazione InfluxDB
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'my-bucket') # Bucket InfluxDB

SENSOR_ID = os.getenv('SENSOR_ID', 'default_sensor')
REPORT_INTERVAL = int(os.getenv('REPORT_INTERVAL', 10)) # Intervallo in secondi

print(f"--- Sensore Virtuale ({SENSOR_ID}) Avviato ---")
print(f"Collegamento a InfluxDB: URL={INFLUXDB_URL}, Org={INFLUXDB_ORG}, Bucket={INFLUXDB_BUCKET}")
print(f"Intervallo di report: {REPORT_INTERVAL} secondi")

# Variabile globale per il client InfluxDB
influx_client = None
write_api = None

def connect_to_influxdb():
    global influx_client, write_api
    print("Tentativo di connessione a InfluxDB...")
    try:
        influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG, timeout=30000) # Timeout 30s
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        
        # Verifica la connessione
        health = influx_client.health()
        if health.status == "pass":
            print(f"Connessione a InfluxDB ({health.version}) stabilita con successo!")
            return True
        else:
            print(f"Stato di salute di InfluxDB: {health.status} - {health.message}")
            return False
    except Exception as e:
        print(f"Errore durante la connessione a InfluxDB: {e}")
        influx_client = None # Resetta il client in caso di fallimento
        write_api = None
        return False

def generate_sensor_data():
    """Genera dati simulati per il sensore."""
    temperature = round(random.uniform(15.0, 30.0), 2)  # Gradi Celsius
    humidity = round(random.uniform(30.0, 70.0), 2)     # Percentuale
    pressure = round(random.uniform(980.0, 1050.0), 2)  # hPa
    print(f"[{SENSOR_ID}] Dati generati: Temp={temperature}°C, Hum={humidity}%, Pres={pressure}hPa")
    return temperature, humidity, pressure

def send_data_to_influxdb():
    """Invia i dati generati a InfluxDB."""
    global write_api
    if not write_api:
        print("API di scrittura InfluxDB non disponibile. Tentativo di riconnessione...")
        if not connect_to_influxdb() or not write_api: # Assicurati che write_api sia aggiornato
            print("Impossibile inviare dati: connessione a InfluxDB fallita.")
            return

    temp, hum, pres = generate_sensor_data()

    point = Point("sensor_metrics") \
        .tag("sensorId", SENSOR_ID) \
        .tag("location", "virtual_lab") \
        .field("temperature", temp) \
        .field("humidity", hum) \
        .field("pressure", pres) \
        .time(time.time_ns(), WritePrecision.NS)

    try:
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print(f"[{SENSOR_ID}] Dati inviati con successo a InfluxDB.")
    except Exception as e:
        print(f"[{SENSOR_ID}] Errore durante l'invio dei dati a InfluxDB: {e}")
        if "Connection refused" in str(e) or "Failed to establish a new connection" in str(e):
            print("Connessione rifiutata da InfluxDB. Riconnessione al prossimo tentativo.")
            global influx_client
            influx_client = None 
            write_api = None


if __name__ == "__main__":
    while not connect_to_influxdb():
        print(f"Connessione a InfluxDB fallita. Nuovo tentativo tra {REPORT_INTERVAL} secondi...")
        time.sleep(REPORT_INTERVAL)

    schedule.every(REPORT_INTERVAL).seconds.do(send_data_to_influxdb)
    print(f"Invio dati pianificato ogni {REPORT_INTERVAL} secondi.")

    while True:
        schedule.run_pending()
        time.sleep(1)
```

**`5. grafana-provisioning/datasources/influxdb-datasource.yml`**

```yml
# Questo file configura automaticamente InfluxDB come sorgente dati in Grafana
apiVersion: 1

datasources:
  - name: InfluxDB_IoT_Data # Nome della sorgente dati in Grafana
    type: influxdb
    access: proxy # Grafana fa da proxy per le richieste
    url: http://influxdb:8086 # URL del servizio InfluxDB (come definito in docker-compose)
    jsonData:
      version: Flux # Specifica che si usa InfluxDB 2.x con linguaggio Flux
      organization: my-iot-org      # Deve corrispondere a DOCKER_INFLUXDB_INIT_ORG
      defaultBucket: iot_bucket     # Bucket di default da usare
      tlsSkipVerify: true # Impostare a false se InfluxDB usa HTTPS con un certificato valido
    secureJsonData:
      token: mysecretadmintoken # Deve corrispondere a DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
```

**Istruzioni per l'Esecuzione:**

**1. Crea la Struttura delle Cartelle:** Come descritto sopra.

**2. Salva i File:** Popola le cartelle con i contenuti dei file corrispondenti.

**3. Modifica le Credenziali (IMPORTANTE):**

   * Nel `docker-compose.yml`, aggiorna le password e i token per influxdb e grafana.

   * Assicurati che i token e i nomi di organizzazione/bucket siano consistenti tra `docker-compose.yml` (servizi influxdb e virtual_sensor) e `grafana-provisioning/datasources/influxdb-datasource.yml`.

**4. Avvia lo Stack:**

Dal terminale, nella cartella radice `iot-monitoring-stack/`:

```bash
sudo docker-compose up --build -d
```
Attendi qualche minuto per l'inizializzazione.

**Accesso ai Servizi:**

* Portainer (Gestione Container): 

```url
https://localhost:9443 
```

(o `http://localhost:9000`)

Crea un utente admin al primo accesso.

* InfluxDB (Database UI): 

```url
http://localhost:8086
```

Login con utente/password definiti nel `docker-compose.yml`.

* Grafana (Visualizzazione): 

```url
http://localhost:3000
```

Login con utente/password definiti nel `docker-compose.yml` (es. admin/grafanapass).
