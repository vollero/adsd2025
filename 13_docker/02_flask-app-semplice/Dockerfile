# Usa un'immagine ufficiale Python come base
# python:3.9-slim è una buona scelta perché è più leggera della versione completa
FROM python:3.9-slim

# Imposta la directory di lavoro all'interno del container
WORKDIR /app

# Copia prima il file delle dipendenze e installale
# Questo sfrutta il caching di Docker: se requirements.txt non cambia,
# questo layer non verrà ricostruito, velocizzando le build successive.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice dell'applicazione
COPY . .

# Esponi la porta su cui l'applicazione Flask è in ascolto
EXPOSE 5000

# Variabile d'ambiente per Flask (opzionale ma buona pratica)
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_DEBUG=1 # Puoi anche impostare il debug qui invece che nel codice

# Comando per avviare l'applicazione Flask
CMD ["flask", "run"]
