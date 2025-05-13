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
        # Potrebbe essere necessario gestire errori di connessione qui e tentare di riconnettersi
        if "Connection refused" in str(e) or "Failed to establish a new connection" in str(e):
            print("Connessione rifiutata da InfluxDB. Riconnessione al prossimo tentativo.")
            # Resettare il client potrebbe forzare un nuovo tentativo di connessione
            global influx_client
            influx_client = None 
            write_api = None


if __name__ == "__main__":
    # Tenta la connessione iniziale
    while not connect_to_influxdb():
        print(f"Connessione a InfluxDB fallita. Nuovo tentativo tra {REPORT_INTERVAL} secondi...")
        time.sleep(REPORT_INTERVAL)

    # Pianifica l'invio dei dati all'intervallo specificato
    schedule.every(REPORT_INTERVAL).seconds.do(send_data_to_influxdb)
    print(f"Invio dati pianificato ogni {REPORT_INTERVAL} secondi.")

    # Ciclo principale per eseguire le attività pianificate
    while True:
        schedule.run_pending()
        time.sleep(1)

