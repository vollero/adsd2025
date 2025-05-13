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

