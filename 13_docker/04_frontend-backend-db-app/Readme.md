## Esempio 4: Frontend, Backend e Database

**Concetto:** Creazione di un'applicazione composta da tre container distinti:
1.  **Frontend:** Una semplice applicazione statica (HTML + JavaScript) servita da un container Nginx.
2.  **Backend:** L'applicazione API Python/Flask che abbiamo sviluppato, che ora esporrà alcuni endpoint per il frontend.
3.  **Database:** Il database PostgreSQL, come nell'esempio precedente.

Utilizzeremo ancora **Docker Compose** per orchestrare questi tre servizi.

**Obiettivo:** Comprendere la separazione dei componenti frontend e backend in container distinti, come farli comunicare e come Docker Compose facilita la gestione di questa architettura a più livelli.

---

**Struttura della Cartella del Progetto:**

Crea una nuova cartella (es. `frontend-backend-db-app`) e organizza i file come segue:

```
frontend-backend-db-app/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── html/
│   │   ├── index.html
│   │   └── script.js
│   └── Dockerfile
└── docker-compose.yml
```

---

**Materiale:**

**1. Dentro la cartella `backend/`:**

   **a) File `backend/requirements.txt`:**
   Modifica il file per includere `Flask-CORS` (per gestire le richieste Cross-Origin Resource Sharing dal frontend) e `gunicorn` (se non l'hai già fatto nell'esempio precedente):

   ```txt
   Flask==2.3.2
   psycopg2-binary==2.9.9
   gunicorn==22.0.0
   Flask-CORS==4.0.1 
   ```
   *(Nota: le versioni potrebbero variare, usa quelle più recenti stabili o quelle indicate).*

   **b) File `backend/app.py`:**
   Modifichiamo l'applicazione Flask per aggiungere endpoint API per interagire con una tabella `items` e abilitare CORS.

   ```python
   import os
   import time
   from flask import Flask, jsonify, request
   from flask_cors import CORS # Importa CORS
   import psycopg2
   import psycopg2.extras # Per dizionari come risultato delle query

   app = Flask(__name__)
   CORS(app) # Abilita CORS per tutte le rotte e origini (per semplicità)
            # In produzione, dovresti configurare origini specifiche: CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080"}})


   def get_db_connection():
       db_host = os.environ.get('DB_HOST', 'db')
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
               break
           except psycopg2.OperationalError as e:
               print(f"Errore di connessione al database: {e}")
               retries -= 1
               print(f"Tentativo di riconnessione... {retries} tentativi rimasti.")
               time.sleep(5)
       
       if conn is None:
           print("Impossibile connettersi al database dopo diversi tentativi.")
       return conn

   def initialize_db():
       conn = get_db_connection()
       if not conn:
           print("DB non connesso, impossibile inizializzare la tabella.")
           return
       try:
           cur = conn.cursor()
           cur.execute("""
               CREATE TABLE IF NOT EXISTS items (
                   id SERIAL PRIMARY KEY,
                   name VARCHAR(255) NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               );
           """)
           conn.commit()
           cur.close()
           print("Tabella 'items' inizializzata (o già esistente).")
       except Exception as e:
           print(f"Errore durante l'inizializzazione della tabella 'items': {str(e)}")
       finally:
           if conn:
               conn.close()

   @app.route('/')
   def home():
       return "API Backend per l'applicazione Frontend/Backend/DB"

   @app.route('/api/items', methods=['GET'])
   def get_items():
       conn = get_db_connection()
       if not conn:
           return jsonify({"status": "errore", "message": "Impossibile connettersi al database."}), 500
       
       items = []
       try:
           cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # Ottieni risultati come dizionari
           cur.execute("SELECT id, name, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at FROM items ORDER BY id;")
           items = [dict(row) for row in cur.fetchall()]
           cur.close()
       except Exception as e:
           return jsonify({"error": str(e)}), 500
       finally:
           if conn:
               conn.close()
       return jsonify(items)

   @app.route('/api/items', methods=['POST'])
   def add_item():
       conn = get_db_connection()
       if not conn:
           return jsonify({"status": "errore", "message": "Impossibile connettersi al database."}), 500

       try:
           data = request.get_json()
           item_name = data.get('name')
           if not item_name:
               return jsonify({"error": "Il nome dell'item è richiesto"}), 400

           cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
           cur.execute("INSERT INTO items (name) VALUES (%s) RETURNING id, name, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at;", (item_name,))
           new_item = dict(cur.fetchone())
           conn.commit()
           cur.close()
           return jsonify(new_item), 201
       except Exception as e:
           return jsonify({"error": str(e)}), 500
       finally:
           if conn:
               conn.close()
               
   @app.route('/db_status')
   def db_status():
       conn = get_db_connection()
       if conn:
           try:
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

   if __name__ == '__main__':
       initialize_db() # Chiama la funzione per creare la tabella all'avvio (se necessario)
       app.run(host='0.0.0.0', port=5000, debug=True) # Per debug. Gunicorn sarà usato da docker-compose.
   else: # Quando eseguito da Gunicorn
       initialize_db()
   ```
   **Spiegazione `backend/app.py`:**
   * `from flask_cors import CORS` e `CORS(app)`: Abilita le richieste Cross-Origin. Il frontend sarà servito da un'origine (porta) diversa rispetto al backend, quindi il browser bloccherebbe le richieste AJAX per motivi di sicurezza se CORS non fosse abilitato sul backend.
   * `initialize_db()`: Una funzione per creare la tabella `items` se non esiste già. Viene chiamata all'avvio dell'app.
   * `cursor_factory=psycopg2.extras.DictCursor`: Fa sì che le query restituiscano righe come dizionari (più facile da convertire in JSON).
   * `/api/items` (GET): Recupera tutti gli item dal database.
   * `/api/items` (POST): Aggiunge un nuovo item al database. Prende un JSON con un campo `name`.
   * `TO_CHAR(...) as created_at`: Formatta il timestamp per una migliore leggibilità nel JSON.

   **c) File `backend/Dockerfile`:**
   Questo file rimane identico a quello dell'esempio precedente (Esempio 3), che usa Gunicorn.

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

   # Esponi la porta su cui l'applicazione Flask (Gunicorn) è in ascolto
   EXPOSE 5000

   # Comando per avviare l'applicazione con Gunicorn
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
   ```

---

**2. Dentro la cartella `frontend/`:**

   **a) File `frontend/html/index.html`:**

   ```html
   <!DOCTYPE html>
   <html lang="it">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>App Frontend</title>
       <style>
           body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }
           h1, h2 { color: #333; }
           #items-list { list-style-type: none; padding: 0; }
           #items-list li { background-color: #fff; border: 1px solid #ddd; margin-bottom: 8px; padding: 10px; border-radius: 4px; }
           .item-name { font-weight: bold; }
           .item-date { font-size: 0.9em; color: #777; }
           input[type="text"] { padding: 8px; margin-right: 8px; border: 1px solid #ccc; border-radius: 4px; }
           button { padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
           button:hover { background-color: #0056b3; }
           #error-message { color: red; margin-top: 10px; }
       </style>
   </head>
   <body>
       <h1>Applicazione Frontend Semplice</h1>

       <h2>Aggiungi un Item:</h2>
       <input type="text" id="itemName" placeholder="Nome dell'item">
       <button onclick="addItem()">Aggiungi Item</button>
       <p id="error-message"></p>

       <h2>Items Esistenti:</h2>
       <ul id="items-list">
           </ul>

       <script src="script.js"></script>
   </body>
   </html>
   ```

   **b) File `frontend/html/script.js`:**

   ```javascript
   // Assicurati che l'URL del backend corrisponda a come esponi il backend
   // Se docker-compose mappa la porta 5000 del backend alla 5001 dell'host:
   const BACKEND_URL = 'http://localhost:5001/api'; // Modifica la porta se necessario

   async function fetchItems() {
       const itemsList = document.getElementById('items-list');
       const errorMessage = document.getElementById('error-message');
       itemsList.innerHTML = '<li>Caricamento...</li>'; // Messaggio di caricamento
       errorMessage.textContent = '';

       try {
           const response = await fetch(`${BACKEND_URL}/items`);
           if (!response.ok) {
               throw new Error(`Errore HTTP: ${response.status} - ${response.statusText}`);
           }
           const items = await response.json();
           
           itemsList.innerHTML = ''; // Pulisci la lista
           if (items.length === 0) {
               itemsList.innerHTML = '<li>Nessun item trovato.</li>';
           } else {
               items.forEach(item => {
                   const listItem = document.createElement('li');
                   listItem.innerHTML = `<span class="item-name">${item.name}</span> (ID: ${item.id}) <br><span class="item-date">Creato: ${item.created_at}</span>`;
                   itemsList.appendChild(listItem);
               });
           }
       } catch (error) {
           console.error('Errore nel fetch degli items:', error);
           itemsList.innerHTML = '<li>Errore nel caricare gli items.</li>';
           errorMessage.textContent = `Impossibile caricare gli items: ${error.message}. Assicurati che il backend sia in esecuzione e raggiungibile.`;
       }
   }

   async function addItem() {
       const itemNameInput = document.getElementById('itemName');
       const itemName = itemNameInput.value.trim();
       const errorMessage = document.getElementById('error-message');
       errorMessage.textContent = '';

       if (!itemName) {
           errorMessage.textContent = 'Il nome dell\'item non può essere vuoto.';
           return;
       }

       try {
           const response = await fetch(`${BACKEND_URL}/items`, {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json',
               },
               body: JSON.stringify({ name: itemName }),
           });

           if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText })); // Prova a leggere il JSON di errore
                throw new Error(`Errore HTTP: ${response.status} - ${errorData.error || errorData.detail || response.statusText}`);
           }
           
           // const newItem = await response.json(); // Non necessario se non usiamo newItem
           await response.json(); 
           itemNameInput.value = ''; // Pulisci l'input
           fetchItems(); // Ricarica la lista degli items
       } catch (error) {
           console.error('Errore nell\'aggiungere l\'item:', error);
           errorMessage.textContent = `Impossibile aggiungere l'item: ${error.message}`;
       }
   }

   // Carica gli items quando la pagina è pronta
   document.addEventListener('DOMContentLoaded', fetchItems);
   ```
   **Spiegazione `frontend/html/script.js`:**
   * `BACKEND_URL`: È l'URL a cui il frontend farà le chiamate API. **Importante:** deve puntare alla porta *host* che mapperai al container del backend (es. `http://localhost:5001/api` se mappi `5001` dell'host alla `5000` del backend).
   * `WorkspaceItems()`: Recupera gli items dal backend (`GET /api/items`) e li visualizza.
   * `addItem()`: Invia un nuovo item al backend (`POST /api/items`).
   * Include una gestione basilare degli errori.

   **c) File `frontend/Dockerfile`:**
   Questo Dockerfile userà Nginx per servire i file statici HTML e JavaScript.

   ```dockerfile
   # Usa un'immagine ufficiale Nginx come base
   FROM nginx:alpine

   # Copia i file statici del frontend nella directory di Nginx
   # La cartella 'html' nel contesto di build (frontend/html) viene copiata in /usr/share/nginx/html
   COPY ./html/ /usr/share/nginx/html/

   # Esponi la porta 80 (Nginx ascolta sulla 80 di default)
   EXPOSE 80

   # Il comando CMD è ereditato dall'immagine base nginx:alpine e avvia Nginx.
   # Non è necessario specificarlo di nuovo a meno che tu non voglia cambiarlo.
   ```
   **Spiegazione `frontend/Dockerfile`:**
   * `FROM nginx:alpine`: Usa l'immagine Nginx leggera.
   * `RUN rm /etc/nginx/conf.d/default.conf`: (Opzionale ma buona pratica) Rimuove il file di configurazione di default di Nginx se non si vuole che interferisca o se si fornirà una configurazione completamente personalizzata. In questo caso semplice, la configurazione di default per servire file da `/usr/share/nginx/html` va bene anche senza questa riga, ma è utile saperlo.
   * `COPY ./html/ /usr/share/nginx/html/`: Copia il contenuto della sottocartella `html` (dove si trovano `index.html` e `script.js`) nella directory radice del server web Nginx.

---

**3. Nella cartella radice `frontend-backend-db-app/`:**

   **a) File `docker-compose.yml`:**

   ```yaml
   version: '3.8'

   services:
     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile
       ports:
         - "8080:80" # Mappa la porta 8080 dell'host alla porta 80 del container frontend (Nginx)
       depends_on:
         - backend # Il frontend per funzionare correttamente dipende dal backend

     backend:
       build:
         context: ./backend
         dockerfile: Dockerfile
       ports:
         - "5001:5000" # Mappa la porta 5001 dell'host alla porta 5000 del container backend (Flask/Gunicorn)
       environment:
         FLASK_ENV: development
         # FLASK_DEBUG: "1" # Se si usa flask run direttamente
         DB_HOST: db
         DB_NAME: exampledb
         DB_USER: exampleuser
         DB_PASSWORD: examplepass
       depends_on:
         db:
           condition: service_healthy
       volumes:
         - ./backend:/app # Mount per sviluppo backend (opzionale, rimuovere per build di produzione)

     db:
       image: postgres:15-alpine
       environment:
         POSTGRES_DB: exampledb
         POSTGRES_USER: exampleuser
         POSTGRES_PASSWORD: examplepass
       ports:
         - "5432:5432" # O la porta host che hai scelto se la 5432 è occupata
       volumes:
         - postgres_data:/var/lib/postgresql/data
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U exampleuser -d exampledb"]
         interval: 10s
         timeout: 5s
         retries: 5

   volumes:
     postgres_data:
   ```
   **Spiegazione `docker-compose.yml`:**
   * Abbiamo ora tre servizi: `frontend`, `backend`, `db`.
   * **`frontend`:**
       * `build: ./frontend`: Costruisce l'immagine dalla cartella `frontend`.
       * `ports: - "8080:80"`: Espone l'Nginx del frontend sulla porta `8080` dell'host. Accederai all'applicazione tramite `http://localhost:8080`.
       * `depends_on: - backend`: Anche se il frontend può servire file statici indipendentemente, la sua piena funzionalità (caricare e aggiungere items) dipende dal backend.
   * **`backend`:**
       * `build: ./backend`: Costruisce l'immagine dalla cartella `backend`.
       * `ports: - "5001:5000"`: Espone il backend Flask/Gunicorn sulla porta `5001` dell'host. È a questo indirizzo (`http://localhost:5001`) che il `script.js` del frontend farà le sue chiamate API.
       * `volumes: - ./backend:/app`: Ancora presente per facilitare lo sviluppo del backend (live reload). Rimuovilo se stai simulando una build di produzione.
   * **`db`:** Rimane sostanzialmente invariato rispetto all'esempio precedente.
   * **Rete:** Docker Compose crea automaticamente una rete predefinita per questi servizi, permettendo loro di comunicare. Il frontend (Nginx) non comunica direttamente con il database. Il frontend (codice JavaScript nel browser dell'utente) comunica con il backend sulla porta esposta del backend. Il backend comunica con il database sulla rete interna di Docker usando il nome del servizio `db` e la sua porta interna `5432`.

---

**Come Eseguirlo:**

1.  **Assicurati che tutte le cartelle e i file siano creati come descritto.**
2.  **Apri un terminale o un prompt dei comandi.**
3.  **Naviga nella cartella radice del progetto** (`frontend-backend-db-app`), dove si trova il file `docker-compose.yml`.
    ```bash
    cd percorso/della/tua/cartella/frontend-backend-db-app
    ```
4.  **Avvia l'applicazione multi-container:**
    ```bash
    docker-compose up --build
    ```
    Attendi che tutti e tre i servizi siano avviati. Vedrai i log di Nginx, Gunicorn (Flask) e PostgreSQL.

5.  **Verifica:**
    * Apri il tuo browser web e vai a `http://localhost:8080` (la porta mappata per il `frontend`). Dovresti vedere la pagina HTML.
    * La lista "Items Esistenti" dovrebbe inizialmente mostrare "Caricamento..." e poi "Nessun item trovato" o gli items se ce ne sono già (dopo che `initialize_db` nel backend ha creato la tabella).
    * Prova ad aggiungere un item usando il campo di input e il bottone. L'item dovrebbe apparire nella lista.
    * Puoi anche controllare l'API del backend direttamente: `http://localhost:5001/api/items` (per GET) e `http://localhost:5001/db_status`.

---

**Considerazioni Importanti (CORS e URL del Backend):**

* **CORS:** Abbiamo aggiunto `Flask-CORS` al backend. Questo è necessario perché il JavaScript servito da `http://localhost:8080` (frontend) sta facendo richieste a `http://localhost:5001` (backend), che è un'origine diversa. Senza CORS, il browser bloccherebbe queste richieste.
* **URL del Backend in `script.js`:** La costante `BACKEND_URL` in `script.js` è impostata su `http://localhost:5001/api`. Questo funziona perché il browser dell'utente (che esegue JavaScript) accede a `localhost`, e la porta `5001` sull'host è mappata alla porta del container backend.

    * **Alternativa (Reverse Proxy):** In architetture più complesse o per evitare problemi di CORS in modo più robusto, potresti configurare Nginx (nel container frontend) per fare da *reverse proxy* per le richieste API. Ad esempio, tutte le richieste a `http://localhost:8080/api/*` potrebbero essere inoltrate da Nginx al servizio `backend` sulla rete Docker (es. `http://backend:5000/api/*`). Questo richiederebbe una configurazione Nginx più avanzata (`nginx.conf`) nel container frontend. Per questo esempio, abbiamo mantenuto la soluzione più semplice con CORS.

---
