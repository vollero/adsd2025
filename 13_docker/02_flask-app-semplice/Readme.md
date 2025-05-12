## Esempio 2: Applicazione Web Semplice (Mono-Container)

**Concetto:** Containerizzazione di una piccola applicazione web dinamica scritta in Python utilizzando il micro-framework Flask. L'intera applicazione (codice e dipendenze) risiederà in un singolo container.

**Obiettivo:** Imparare a gestire dipendenze dell'applicazione, esporre porte e gestire l'ambiente di esecuzione all'interno di un container per un'applicazione web.

---

**Materiale:**

Tre file in una nuova cartella (ad esempio, `flask-app-semplice`):

1.  `app.py` (il codice della nostra applicazione Flask)
2.  `requirements.txt` (per specificare le dipendenze Python)
3.  `Dockerfile`

---

**1. File `requirements.txt`:**

Crea un file chiamato `requirements.txt` con il seguente contenuto:

```txt
Flask==2.3.2
```

*(Nota: Potresti usare una versione più recente di Flask se disponibile, ma questa è una versione stabile al momento della scrittura. Puoi anche scrivere solo `Flask` per ottenere l'ultima versione, ma fissare la versione è una buona pratica per la riproducibilità).*

**Spiegazione `requirements.txt`:**
* Questo file elenca le librerie Python necessarie per la nostra applicazione. In questo caso, abbiamo solo bisogno di `Flask`.
* Il comando `pip install -r requirements.txt` (che useremo nel Dockerfile) leggerà questo file e installerà le dipendenze specificate.

---

**2. File `app.py`:**

Crea un file chiamato `app.py` con il seguente contenuto:

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Ciao dal mio servizio Flask in un container Docker!"

@app.route('/api/info')
def info():
    return jsonify({
        "applicazione": "Flask App Semplice",
        "versione": "1.0",
        "messaggio": "Servizio API di base"
    })

if __name__ == '__main__':
    # Ascolta su tutte le interfacce di rete (0.0.0.0)
    # e sulla porta 5000 (porta di default di Flask)
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**Spiegazione `app.py`:**
* `from flask import Flask, jsonify`: Importa le classi necessarie da Flask.
* `app = Flask(__name__)`: Crea un'istanza dell'applicazione Flask.
* `@app.route('/')`: Definisce una rotta per l'URL radice (`/`). Quando si accede a questo URL, viene eseguita la funzione `home()`.
* `def home()`: Restituisce una semplice stringa di testo.
* `@app.route('/api/info')`: Definisce un'altra rotta (`/api/info`) che restituisce dati in formato JSON.
* `def info()`: Utilizza `jsonify` per convertire un dizionario Python in una risposta JSON.
* `if __name__ == '__main__':`: Questa parte assicura che il server di sviluppo Flask venga avviato solo quando lo script viene eseguito direttamente (non quando viene importato come modulo).
* `app.run(host='0.0.0.0', port=5000, debug=True)`:
    * `host='0.0.0.0'`: È cruciale per Docker. Fa sì che il server Flask ascolti su tutte le interfacce di rete disponibili all'interno del container. Se fosse `127.0.0.1` (localhost), sarebbe accessibile solo dall'interno del container stesso, non dall'esterno tramite la porta mappata.
    * `port=5000`: Specifica la porta su cui l'applicazione Flask sarà in ascolto all'interno del container.
    * `debug=True`: Abilita la modalità di debug di Flask, utile durante lo sviluppo (ricarica automaticamente al cambio del codice, fornisce traceback dettagliati). Per produzione, questo dovrebbe essere `False`.

---

**3. File `Dockerfile`:**

Crea un file chiamato `Dockerfile` (senza estensione) nella stessa cartella con il seguente contenuto:

```dockerfile
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
```

**Spiegazione `Dockerfile`:**

* `FROM python:3.9-slim`:
    * Utilizza un'immagine ufficiale Python versione 3.9, variante "slim". Questa variante è ottimizzata per le dimensioni, includendo solo il minimo indispensabile per eseguire applicazioni Python.
* `WORKDIR /app`:
    * Imposta la directory di lavoro predefinita all'interno del container a `/app`. Tutti i comandi successivi (`COPY`, `RUN`, `CMD`) verranno eseguiti in questo contesto. Se la directory non esiste, viene creata.
* `COPY requirements.txt .`:
    * Copia il file `requirements.txt` dalla directory corrente del tuo host nella directory `/app` del container (che è la `WORKDIR` corrente).
* `RUN pip install --no-cache-dir -r requirements.txt`:
    * Esegue il comando `pip install` per installare le dipendenze elencate in `requirements.txt`.
    * `--no-cache-dir` disabilita la cache di pip, il che può aiutare a mantenere l'immagine più piccola.
    * Questo passaggio viene eseguito *prima* di copiare il resto del codice sorgente. Questo è un pattern comune per sfruttare il sistema di caching dei layer di Docker: se il file `requirements.txt` non cambia, Docker riutilizzerà il layer esistente con le dipendenze installate, rendendo le build successive (in cui magari cambia solo il codice Python) molto più veloci.
* `COPY . .`:
    * Copia tutto il contenuto della directory corrente del tuo host (incluso `app.py` e il `Dockerfile` stesso, anche se il `Dockerfile` non è necessario all'interno dell'immagine finale per l'esecuzione) nella directory `/app` del container.
* `EXPOSE 5000`:
    * Documenta che il container espone la porta `5000`, su cui Flask sarà in ascolto.
* `ENV FLASK_APP=app.py`:
    * Imposta la variabile d'ambiente `FLASK_APP`. Flask la usa per sapere quale file caricare.
* `ENV FLASK_RUN_HOST=0.0.0.0`:
    * Imposta la variabile d'ambiente `FLASK_RUN_HOST` a `0.0.0.0`. Questo dice a Flask di ascoltare su tutte le interfacce di rete, come specificato anche nel comando `app.run()` nel codice Python. È una buona pratica impostarla anche come variabile d'ambiente.
* `CMD ["flask", "run"]`:
    * Specifica il comando predefinito per eseguire l'applicazione quando il container parte.
    * `flask run` è il comando standard per avviare il server di sviluppo di Flask. Grazie alle variabili d'ambiente `FLASK_APP` e `FLASK_RUN_HOST` impostate precedentemente, sa quale app caricare e su quale host ascoltare.

---

**Come Eseguirlo:**

1.  **Apri un terminale o un prompt dei comandi.**
2.  **Naviga nella cartella** dove hai creato i file `app.py`, `requirements.txt` e `Dockerfile`.
    ```bash
    cd percorso/della/tua/cartella/flask-app-semplice
    ```
3.  **Builda l'immagine Docker:**
    ```bash
    docker build -t simple-flask-app .
    ```
    * `-t simple-flask-app`: Assegna il nome `simple-flask-app` all'immagine.

4.  **Esegui il container Docker dall'immagine creata:**
    ```bash
    docker run -d -p 5001:5000 --name my-flask-service simple-flask-app
    ```
    * `-d`: Esegue in background.
    * `-p 5001:5000`: Mappa la porta `5001` del tuo host alla porta `5000` del container (dove Flask è in ascolto). Se `5001` è occupata, scegline un'altra.
    * `--name my-flask-service`: Assegna un nome al container.
    * `simple-flask-app`: Il nome dell'immagine da eseguire.

5.  **Verifica:**
    * Apri il tuo browser web e vai a `http://localhost:5001`. Dovresti vedere: `Ciao dal mio servizio Flask in un container Docker!`
    * Prova anche l'endpoint API: `http://localhost:5001/api/info`. Dovresti vedere una risposta JSON.

---

**Per vedere i log dell'applicazione Flask (se non usi `-d` o se vuoi vederli dopo):**

```bash
docker logs my-flask-service
```
Se vuoi seguire i log in tempo reale:
```bash
docker logs -f my-flask-service
```

---
