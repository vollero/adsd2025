# Usa un'immagine ufficiale Python come base
FROM python:3.9-slim

# Imposta la directory di lavoro all'interno del container
WORKDIR /app

# Copia prima il file delle dipendenze e installale
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice dell'applicazione
COPY . .

# Esponi la porta su cui l'applicazione Flask è in ascolto
EXPOSE 5000

# Comando per avviare l'applicazione Flask
# Utilizziamo gunicorn per un server WSGI un po' più robusto del server di sviluppo di Flask
# CMD ["python", "app.py"] # Puoi usare questo per il debug semplice
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
