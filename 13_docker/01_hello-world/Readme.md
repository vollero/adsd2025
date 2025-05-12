## Esempio 1: Hello World Statico

**Concetto:** Creazione di un container Docker che esegue un server web Nginx per servire una singola pagina HTML statica.

**Obiettivo:** Comprendere i concetti di base di Dockerfile, la creazione di un'immagine Docker e l'esecuzione di un container.

---

**Materiale:**

Abbiamo bisogno di due file in una nuova cartella (ad esempio `hello-world-statico`):

1.  `index.html`
2.  `Dockerfile`

---

**1. File `index.html`:**

Il `index.html` ha il seguente contenuto:

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello World Statico</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
            color: #333;
        }
        h1 {
            font-size: 3em;
            color: #007bff;
        }
    </style>
</head>
<body>
    <h1>Ciao Mondo, dal mio Container Nginx!</h1>
</body>
</html>
```

**Spiegazione `index.html`:**
* Questa è una semplicissima pagina HTML. Visualizza un messaggio di saluto.
* Utilizza un po' di stile CSS inline per renderla leggermente più gradevole.

---

**2. File `Dockerfile`:**

Il file `Dockerfile` (senza estensione) nella stessa cartella ha il seguente contenuto:

```dockerfile
# Usa un'immagine ufficiale Nginx come base
FROM nginx:alpine

# Copia il file index.html dalla cartella corrente del tuo host
# nella cartella di Nginx preposta a servire i file HTML nel container
COPY index.html /usr/share/nginx/html/index.html

# Esponi la porta 80 (la porta standard per HTTP)
EXPOSE 80

# Comando per avviare Nginx quando il container parte
# (questo comando è spesso già definito nell'immagine base di Nginx,
# quindi questa riga potrebbe essere omessa per Nginx, ma è buona pratica indicarla
# per chiarezza o per immagini base che non hanno un CMD predefinito).
CMD ["nginx", "-g", "daemon off;"]
```

**Spiegazione `Dockerfile`:**

* `FROM nginx:alpine`:
    * Questa istruzione dice a Docker di utilizzare l'immagine `nginx:alpine` come base per la nostra immagine.
    * `nginx` è l'immagine ufficiale di Nginx.
    * `:alpine` specifica una versione dell'immagine basata su Alpine Linux, che è molto leggera, risultando in un'immagine finale più piccola.
* `COPY index.html /usr/share/nginx/html/index.html`:
    * Questa istruzione copia il file `index.html` dalla directory corrente del tuo progetto (dove si trova il Dockerfile) nella directory `/usr/share/nginx/html/` all'interno del container.
    * Questa è la directory predefinita da cui Nginx serve i file statici.
* `EXPOSE 80`:
    * Questa istruzione documenta che il container espone la porta `80` all'interno della rete Docker. Non pubblica effettivamente la porta sull'host; serve più come documentazione per chi utilizza l'immagine o per la mappatura automatica in alcuni contesti.
* `CMD ["nginx", "-g", "daemon off;"]`:
    * Specifica il comando che verrà eseguito quando un container basato su questa immagine viene avviato.
    * `nginx -g "daemon off;"` avvia Nginx in primo piano (foreground). Questo è importante per i container Docker, poiché un container si arresta se il processo principale (PID 1) termina. Se Nginx fosse avviato come demone (in background), il container si avvierebbe e si fermerebbe immediatamente.

---

**Come Eseguire il codice:**

1.  **Apri un terminale o un prompt dei comandi.**
2.  **Naviga nella cartella** dove hai creato i file `index.html` e `Dockerfile`.
    ```bash
    cd percorso/della/tua/cartella/hello-world-statico
    ```
3.  **Builda l'immagine Docker:**
    ```bash
    docker build -t hello-static-nginx .
    ```
    * `docker build`: È il comando per costruire un'immagine Docker.
    * `-t hello-static-nginx`: Assegna un nome (tag) all'immagine. In questo caso, `hello-static-nginx`. Puoi scegliere il nome che preferisci.
    * `.`: Indica a Docker di cercare il `Dockerfile` nella directory corrente.

4.  **Esegui il container Docker dall'immagine creata:**
    ```bash
    docker run -d -p 8080:80 --name my-static-site hello-static-nginx
    ```
    * `docker run`: È il comando per eseguire un container.
    * `-d`: Esegue il container in modalità "detached" (in background), così il terminale rimane libero.
    * `-p 8080:80`: Mappa la porta `8080` del tuo computer (host) alla porta `80` del container (dove Nginx è in ascolto). Puoi scegliere un'altra porta host se `8080` è già in uso (es. `-p 8081:80`).
    * `--name my-static-site`: Assegna un nome al container in esecuzione, `my-static-site`, per facilitarne la gestione.
    * `hello-static-nginx`: È il nome dell'immagine che vogliamo eseguire.

5.  **Verifica:**
    Apri il tuo browser web e vai a `http://localhost:8080`. Dovresti vedere la tua pagina "Ciao Mondo, dal mio Container Nginx!".

---

**Comandi Docker Utili (Opzionali):**

* **Vedere i container in esecuzione:**
    ```bash
    docker ps
    ```
* **Vedere tutte le immagini Docker locali:**
    ```bash
    docker images
    ```
* **Fermare il container:**
    ```bash
    docker stop my-static-site
    ```
* **Rimuovere il container (dopo averlo fermato):**
    ```bash
    docker rm my-static-site
    ```
* **Rimuovere l'immagine (assicurati che nessun container la stia usando):**
    ```bash
    docker rmi hello-static-nginx
    ```

---
