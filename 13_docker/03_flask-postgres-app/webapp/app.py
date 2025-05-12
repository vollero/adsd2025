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
