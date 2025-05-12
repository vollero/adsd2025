## Livello 2, Esempio 3: Applicazione Web con Database

**Concetto:** Creazione di un'applicazione composta da due container:
1.  Un'applicazione web (continueremo con Python/Flask per coerenza).
2.  Un database PostgreSQL.

Utilizzeremo **Docker Compose** per definire, configurare ed eseguire questa applicazione multi-container.

**Obiettivo:** Introdurre Docker Compose per orchestrare più container, gestire le reti tra container in modo che possano comunicare, e la persistenza dei dati del database utilizzando i volumi Docker.

---

**Struttura della Cartella del Progetto:**

Crea una nuova cartella (es. `flask-postgres-app`) e al suo interno crea una sottocartella per l'applicazione web (es. `webapp`):

```
flask-postgres-app/
├── webapp/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml
```

---

**Materiale:**

**1. Dentro la cartella `webapp/`:**

   **a) File `webapp/requirements.txt`:**
   Crea il file con il seguente contenuto:

   ```txt
   Flask==2.3.2
   psycopg2-binary==2.9.9
   ```
   * `psycopg2-binary`: È l'adattatore Python per PostgreSQL, necessario per connettere l'applicazione Flask al database PostgreSQL.

   **b) File `webapp/app.py`:**
   Crea il file con il seguente contenuto:

   ```python
   import os
   import time
   from flask import Flask, jsonify
   import psycopg2

   app = Flask(__name__)

   def get_db_connection():
       # Prendi i parametri di connessione dalle variabili d'ambiente
       db_host = os.environ.get('DB_HOST', 'db') # 'db' è il nome del servizio del database in docker-compose
       db_name = os.environ.get('DB_NAME', 'exampledb')
       db_user = os.environ.get('DB_USER', 'exampleuser')
       db_password = os.environ.get('DB_PASSWORD', 'examplepass')
       
       conn = None
       retries = 5
       while retries > 0:
           try:
               conn = psycopg2.connect(
                   host=db_host,
                   dbname=db_name,
                   user=db_user,
                   password=db_password
               )
               print("Connessione al database stabilita con successo!")
               break # Esce dal ciclo se la connessione ha successo
           except psycopg2.OperationalError as e:
               print(f"Errore di connessione al database: {e}")
               retries -= 1
               print(f"Tentativo di riconnessione... {retries} tentativi rimasti.")
               time.sleep(5) # Aspetta 5 secondi prima di riprovare
       
       if conn is None:
           print("Impossibile connettersi al database dopo diversi tentativi.")
       return conn

   @app.route('/')
   def home():
       return "Ciao dal servizio Flask! Prova l'endpoint /db_status per verificare la connessione al DB."

   @app.route('/db_status')
   def db_status():
       conn = get_db_connection()
       if conn:
           try:
               # Prova ad eseguire una semplice query
               cur = conn.cursor()
               cur.execute('SELECT version();')
               db_version = cur.fetchone()
               cur.close()
               conn.close()
               return jsonify({
                   "status": "successo",
                   "message": "Connesso a PostgreSQL!",
                   "db_version": db_version[0] if db_version else "N/A"
               })
           except Exception as e:
               return jsonify({"status": "errore", "message": f"Errore durante la query al DB: {str(e)}"}), 500
       else:
           return jsonify({"status": "errore", "message": "Impossibile connettersi al database."}), 500
   
   @app.route('/create_table_test')
   def create_table_test():
       conn = get_db_connection()
       if not conn:
           return jsonify({"status": "errore", "message": "Impossibile connettersi al database."}), 500
       
       try:
           cur = conn.cursor()
           cur.execute("""
               CREATE TABLE IF NOT EXISTS test_items (
                   id SERIAL PRIMARY KEY,
                   name VARCHAR(255) NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               );
           """)
           conn.commit() # Necessario per rendere effettive le modifiche come CREATE TABLE
           cur.close()
           conn.close()
           return jsonify({"status": "successo", "message": "Tabella 'test_items' creata (o già esistente)." })
       except Exception as e:
           return jsonify({"status": "errore", "message": f"Errore durante la creazione della tabella: {str(e)}"}), 500


   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000, debug=True)
   ```

   **Spiegazione `webapp/app.py`:**
   * Importa `os` per leggere le variabili d'ambiente e `psycopg2` per interagire con PostgreSQL.
   * La funzione `get_db_connection()` tenta di connettersi al database.
        * Legge i parametri di connessione (host, nome DB, utente, password) dalle **variabili d'ambiente**. Questo è fondamentale per la configurazione in ambienti containerizzati, poiché non vogliamo codificare le credenziali direttamente nel codice.
        * Il nome host del database `db_host` di default è `db`. Questo corrisponderà al nome del servizio del database che definiremo nel file `docker-compose.yml`. Docker Compose fornisce una risoluzione DNS interna che permette ai container di trovarsi tramite i nomi dei servizi.
        * Include un semplice **meccanismo di retry** perché l'applicazione web potrebbe avviarsi prima che il database sia completamente pronto ad accettare connessioni.
   * L'endpoint `/` è un semplice saluto.
   * L'endpoint `/db_status` tenta di connettersi al database, esegue una query per ottenere la versione di PostgreSQL e restituisce lo stato.
   * L'endpoint `/create_table_test` tenta di creare una semplice tabella `test_items` se non esiste già. Questo ci permette di verificare che possiamo scrivere nel database.
   * Come prima, `app.run(host='0.0.0.0', ...)` assicura che Flask sia accessibile dall'esterno del container.

   **c) File `webapp/Dockerfile`:**
   Crea il file con il seguente contenuto (è molto simile a quello dell'esempio precedente):

   ```dockerfile
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
   ```
   **Spiegazione `webapp/Dockerfile`:**
   * L'unica modifica significativa rispetto all'esempio precedente è il `CMD`.
   * Invece di `flask run` (che usa il server di sviluppo di Flask), qui usiamo `gunicorn`. Gunicorn è un server WSGI HTTP Python per UNIX. È più robusto e adatto per esecuzioni che vanno oltre il semplice sviluppo.
        * `gunicorn --bind 0.0.0.0:5000 app:app`:
            * `--bind 0.0.0.0:5000`: Dice a Gunicorn di ascoltare su tutte le interfacce sulla porta 5000.
            * `app:app`: Specifica il modulo Python da cui caricare l'applicazione (`app.py`) e il nome dell'istanza Flask all'interno di quel modulo (l'oggetto `app`).
   * Per installare Gunicorn, dovresti aggiungerlo al `webapp/requirements.txt`:
        ```txt
        Flask==2.3.2
        psycopg2-binary==2.9.9
        gunicorn==22.0.0
        ```
        Assicurati di aggiornare `requirements.txt` e poi ricostruire l'immagine se necessario.

---

**2. Nella cartella radice `flask-postgres-app/`:**

   **a) File `docker-compose.yml`:**
   Crea il file con il seguente contenuto:

   ```yaml
   version: '3.8' # Specifica la versione della sintassi di Docker Compose

   services:
     webapp: # Nome del servizio dell'applicazione web
       build:
         context: ./webapp # Percorso alla directory contenente il Dockerfile per l'app web
         dockerfile: Dockerfile
       ports:
         - "5001:5000" # Mappa la porta 5001 dell'host alla porta 5000 del container webapp
       environment: # Variabili d'ambiente per il servizio webapp
         FLASK_ENV: development # Imposta l'ambiente Flask (opzionale, 'development' o 'production')
         # FLASK_DEBUG: "1" # Abilita il debug di Flask se usi CMD ["flask", "run"]
         DB_HOST: db # Nome host del servizio database, come definito sotto
         DB_NAME: exampledb
         DB_USER: exampleuser
         DB_PASSWORD: examplepass
       depends_on: # Specifica che webapp dipende dal servizio db
         db:
           condition: service_healthy # Attende che il servizio 'db' sia 'healthy' prima di avviare webapp
       volumes:
        - ./webapp:/app # Monta il codice sorgente locale in /app nel container per live reloading (solo sviluppo)

     db: # Nome del servizio del database
       image: postgres:15-alpine # Usa l'immagine ufficiale di PostgreSQL 15 (versione Alpine, più leggera)
       environment: # Variabili d'ambiente per il servizio db (PostgreSQL le usa per l'inizializzazione)
         POSTGRES_DB: exampledb
         POSTGRES_USER: exampleuser
         POSTGRES_PASSWORD: examplepass
       ports:
         - "5432:5432" # Mappa la porta 5432 dell'host alla 5432 del container (opzionale, per accesso diretto al DB dall'host)
       volumes:
         - postgres_data:/var/lib/postgresql/data # Volume nominato per la persistenza dei dati del database
       healthcheck: # Controlla lo stato di salute del database
         test: ["CMD-SHELL", "pg_isready -U exampleuser -d exampledb"]
         interval: 10s
         timeout: 5s
         retries: 5

   volumes: # Definizione dei volumi nominati
     postgres_data: # Il nome del volume, Docker lo gestirà
   ```

   **Spiegazione `docker-compose.yml`:**
   * `version: '3.8'`: Indica la versione del formato del file Docker Compose.
   * `services:`: Definisce i vari container (servizi) che compongono l'applicazione.
       * **`webapp:`**
           * `build:`: Dice a Docker Compose di costruire l'immagine per questo servizio.
               * `context: ./webapp`: Specifica che il contesto di build (dove si trovano il Dockerfile e il codice sorgente) è la sottocartella `webapp`.
               * `dockerfile: Dockerfile`: Il nome del Dockerfile da usare.
           * `ports:`:
               * `- "5001:5000"`: Mappa la porta `5001` del computer host alla porta `5000` del container `webapp` (dove Gunicorn/Flask è in ascolto).
           * `environment:`: Imposta le variabili d'ambiente all'interno del container `webapp`.
               * `DB_HOST: db`: Questo è cruciale. `db` è il nome che abbiamo dato al servizio del database (vedi sotto). Docker Compose crea una rete virtuale per i servizi definiti nel file, e ogni servizio è raggiungibile dagli altri usando il suo nome come hostname.
               * `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Devono corrispondere a quelle usate per inizializzare il database PostgreSQL.
           * `depends_on:`:
               * `db:`: Dice a Docker Compose che il servizio `webapp` dipende dal servizio `db`.
               * `condition: service_healthy`: Docker Compose attenderà che il servizio `db` passi il suo `healthcheck` prima di avviare il container `webapp`. Questo aiuta a prevenire che l'app web tenti di connettersi al DB prima che sia pronto.
           * `volumes:`
               * `- ./webapp:/app`: Questo è un **bind mount** (montaggio di collegamento). Monta la cartella `./webapp` del tuo host nella cartella `/app` all'interno del container. **Utile per lo sviluppo**: se modifichi il codice in `webapp/app.py` sul tuo host, le modifiche si rifletteranno immediatamente nel container (Gunicorn con `--reload` o il server di sviluppo di Flask in modalità debug rileveranno il cambiamento e si riavvieranno). **Per la produzione, di solito si copia il codice nell'immagine durante la build e non si usano bind mount per il codice dell'applicazione.**
       * **`db:`**
           * `image: postgres:15-alpine`: Usa l'immagine Docker ufficiale `postgres` versione 15, variante `alpine` (leggera). Docker scaricherà questa immagine da Docker Hub se non è presente localmente.
           * `environment:`: Imposta variabili d'ambiente per il container PostgreSQL. L'immagine `postgres` ufficiale le usa per inizializzare il database alla prima esecuzione:
               * `POSTGRES_DB: exampledb`: Crea un database chiamato `exampledb`.
               * `POSTGRES_USER: exampleuser`: Crea un utente `exampleuser`.
               * `POSTGRES_PASSWORD: examplepass`: Imposta la password per `exampleuser`.
           * `ports:`:
               * `- "5432:5432"`: Mappa la porta `5432` dell'host alla porta `5432` del container (la porta standard di PostgreSQL). Questo è opzionale e ti permette di connetterti al database PostgreSQL dall'host usando un client DB come pgAdmin o DBeaver, se necessario. Per la comunicazione tra `webapp` e `db` all'interno della rete Docker, questa mappatura di porta non è necessaria.
           * `volumes:`:
               * `- postgres_data:/var/lib/postgresql/data`: Questo è un **volume nominato**.
                   * `postgres_data`: È il nome che diamo al volume. Docker gestirà la creazione e la memorizzazione di questo volume.
                   * `/var/lib/postgresql/data`: È la directory all'interno del container PostgreSQL dove vengono memorizzati i dati del database.
                   * Usando un volume, i dati del database persisteranno anche se il container `db` viene fermato, rimosso e ricreato. Senza un volume, i dati andrebbero persi ogni volta che il container viene rimosso.
           * `healthcheck:`: Definisce un comando per verificare se il database è pronto ad accettare connessioni.
               * `test: ["CMD-SHELL", "pg_isready -U exampleuser -d exampledb"]`: Esegue il comando `pg_isready` che controlla lo stato del server PostgreSQL.
               * `interval`, `timeout`, `retries`: Configurano la frequenza e la tolleranza del controllo.
   * `volumes:` (a livello radice):
       * `postgres_data:`: Dichiara il volume nominato `postgres_data` in modo che Docker Compose possa gestirlo.

---

**Come Eseguirlo:**

1.  **Assicurati di aver aggiunto `gunicorn` a `webapp/requirements.txt`** come indicato sopra.
2.  **Apri un terminale o un prompt dei comandi.**
3.  **Naviga nella cartella radice del progetto** (`flask-postgres-app`), dove si trova il file `docker-compose.yml`.
    ```bash
    cd percorso/della/tua/cartella/flask-postgres-app
    ```
4.  **Avvia l'applicazione multi-container:**
    ```bash
    docker-compose up --build
    ```
    * `docker-compose up`: È il comando per avviare i servizi definiti nel `docker-compose.yml`.
    * `--build`: Forza Docker Compose a (ri)costruire le immagini prima di avviare i container (utile se hai fatto modifiche al `Dockerfile` o al codice sorgente che viene copiato nell'immagine). La prima volta è implicitamente necessario.

    Vedrai l'output dei log di entrambi i container (webapp e db) nel tuo terminale. Attendi finché non vedi messaggi che indicano che il database è pronto e che l'applicazione Flask (Gunicorn) è partita e in ascolto sulla porta 5000.

5.  **Verifica:**
    * Apri il tuo browser web e vai a `http://localhost:5001` (la porta mappata per `webapp`). Dovresti vedere: `Ciao dal servizio Flask! Prova l'endpoint /db_status per verificare la connessione al DB.`
    * Vai a `http://localhost:5001/db_status`. Se tutto è configurato correttamente, dovresti vedere una risposta JSON che indica una connessione riuscita e la versione di PostgreSQL. Potrebbe volerci qualche secondo la prima volta affinché il DB sia completamente inizializzato e l'app si connetta.
    * Vai a `http://localhost:5001/create_table_test`. Dovresti ricevere un messaggio che la tabella `test_items` è stata creata. Puoi ricaricare la pagina, e dovrebbe dire che esiste già.

---

**Comandi Docker Compose Utili:**

* **Avviare i servizi in background (detached mode):**
    ```bash
    docker-compose up -d
    ```
* **Vedere i log dei servizi (se eseguiti in detached mode):**
    ```bash
    docker-compose logs
    docker-compose logs webapp
    docker-compose logs -f webapp # Per seguire i log
    ```
* **Fermare i servizi:**
    ```bash
    docker-compose down
    ```
    Questo comando ferma *e rimuove* i container. Per fermare senza rimuovere: `docker-compose stop`.
* **Fermare e rimuovere i container E i volumi (ATTENZIONE: cancella i dati del DB se usi `down -v`):**
    ```bash
    docker-compose down -v
    ```
* **Elencare i container gestiti da Compose:**
    ```bash
    docker-compose ps
    ```
* **Ricostruire le immagini:**
    ```bash
    docker-compose build
    ```

---
