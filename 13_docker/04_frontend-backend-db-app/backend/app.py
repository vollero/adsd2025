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
