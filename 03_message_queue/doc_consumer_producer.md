# Documentazione del Pattern Producer-Consumer

## Panoramica

Questo script dimostra il pattern di comunicazione **Producer-Consumer** utilizzando il sistema di message queue implementato. Il codice crea un semplice esempio in cui un producer genera messaggi e li pubblica su un topic, mentre un consumer si sottoscrive allo stesso topic e legge periodicamente i messaggi disponibili.

**Caratteristiche principali:**
- Implementazione di un producer che genera messaggi di test
- Implementazione di un consumer che legge e visualizza i messaggi ricevuti
- Esecuzione concorrente di producer e consumer tramite thread separati
- Comunicazione asincrona attraverso il sistema di message queue

Questo esempio rappresenta un caso d'uso tipico per i sistemi di message queue, dove componenti indipendenti possono comunicare in modo disaccoppiato, senza la necessità di sincronizzazione diretta.

## Funzionamento Dettagliato

### Struttura Generale

Lo script è organizzato in tre parti principali:
1. La funzione `producer()` che pubblica messaggi
2. La funzione `consumer()` che legge i messaggi
3. Il blocco principale che avvia entrambe le funzioni in thread separati

### Il Producer

```python
def producer():
    """Funzione di esempio per un producer."""
    client = MessageQueueClient()
    
    for i in range(5):
        message = {
            "id": i,
            "content": f"Messaggio di test #{i}",
            "timestamp": time.time()
        }
        
        print(f"Pubblicazione messaggio: {message}")
        response = client.publish("esempi", message)
        print(f"Risposta: {response}")
        
        time.sleep(1)
    
    client.close()
```

Il producer:
1. **Inizializzazione**: Crea un'istanza del `MessageQueueClient`
2. **Generazione di messaggi**: Esegue un ciclo che genera 5 messaggi di test, ciascuno con:
   - Un identificativo numerico (`id`)
   - Un contenuto descrittivo (`content`)
   - Un timestamp che rappresenta il momento di creazione
3. **Pubblicazione**: Invia ogni messaggio al topic "esempi" tramite il metodo `publish()` del client
4. **Feedback**: Stampa a console la risposta ricevuta dal server per ogni pubblicazione
5. **Tempo**: Introduce un ritardo di 1 secondo tra le pubblicazioni consecutive
6. **Chiusura**: Al termine, chiude la connessione al server

La struttura del messaggio è un dizionario JSON, facilmente estensibile per includere dati più complessi in base alle necessità dell'applicazione.

### Il Consumer

```python
def consumer():
    """Funzione di esempio per un consumer."""
    client = MessageQueueClient()
    
    # Sottoscrivi al topic
    client.subscribe("esempi")
    
    # Leggi messaggi periodicamente
    for _ in range(10):
        messages = client.get_messages("esempi")
        if messages:
            print(f"Ricevuti {len(messages)} messaggi:")
            for msg in messages:
                print(f" - {msg}")
        else:
            print("Nessun messaggio disponibile")
        
        time.sleep(2)
    
    client.close()
```

Il consumer:
1. **Inizializzazione**: Crea un'istanza del `MessageQueueClient`
2. **Sottoscrizione**: Si sottoscrive al topic "esempi" tramite il metodo `subscribe()` del client
3. **Polling**: Esegue un ciclo di 10 iterazioni in cui:
   - Richiede i messaggi disponibili sul topic tramite il metodo `get_messages()`
   - Elabora e visualizza i messaggi ricevuti (in questo caso li stampa a console)
   - Se non ci sono messaggi, notifica che nessun messaggio è disponibile
4. **Tempo**: Introduce un ritardo di 2 secondi tra le letture consecutive
5. **Chiusura**: Al termine, chiude la connessione al server

Questo consumer utilizza un approccio di polling, richiedendo periodicamente i messaggi invece di riceverli automaticamente quando vengono pubblicati (push model). Questo è coerente con l'implementazione del sistema di message queue.

### Esecuzione Concorrente

```python
if __name__ == "__main__":
    import threading
    
    # Avvia producer e consumer in thread separati
    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)
    
    producer_thread.start()
    time.sleep(1)  # Piccolo ritardo per assicurarsi che il producer inizi prima
    consumer_thread.start()
    
    producer_thread.join()
    consumer_thread.join()
```

La parte principale dello script:
1. **Creazione dei thread**: Crea due thread separati, uno per il producer e uno per il consumer
2. **Avvio sequenziale**: 
   - Avvia prima il thread del producer
   - Attende 1 secondo per dare al producer il tempo di iniziare a pubblicare
   - Avvia il thread del consumer
3. **Sincronizzazione**: Utilizza `join()` su entrambi i thread per attendere il loro completamento prima di terminare lo script

Il ritardo tra l'avvio del producer e del consumer è una scelta di design che garantisce che ci siano già alcuni messaggi disponibili quando il consumer inizia a leggere.

## Flusso di Esecuzione

1. **Avvio dello script**: Il programma inizia, importa i moduli necessari e definisce le funzioni
2. **Creazione dei thread**: Vengono creati due thread per eseguire producer e consumer in parallelo
3. **Esecuzione del producer**: 
   - Il producer si connette al server
   - Genera e pubblica i messaggi a intervalli regolari
   - Completa dopo aver pubblicato 5 messaggi
4. **Esecuzione del consumer**: 
   - Il consumer si connette al server e si sottoscrive al topic
   - Inizia a leggere i messaggi a intervalli regolari
   - Continua a leggere per 10 iterazioni, anche dopo che il producer ha terminato
5. **Terminazione**: Lo script attende il completamento di entrambi i thread e termina

## Considerazioni e Comportamento Atteso

1. **Ricezione dei messaggi**: Il consumer potrebbe ricevere più messaggi in una singola lettura, soprattutto se il producer pubblica più velocemente di quanto il consumer legga
2. **Persistenza**: I messaggi pubblicati dal producer rimangono disponibili nel server anche dopo che il producer ha terminato, permettendo al consumer di leggerli in seguito
3. **Perdita potenziale**: Se il server ha un limite sulla dimensione della coda per topic (es. 100 messaggi), i messaggi più vecchi potrebbero essere scartati se si accumulano troppi messaggi
4. **Indipendenza**: Producer e consumer operano indipendentemente l'uno dall'altro, dimostrando il disaccoppiamento offerto dal pattern message queue

## Casi d'Uso Reali

Questo semplice esempio dimostra un pattern che può essere esteso per numerosi scenari reali:

1. **Elaborazione asincrona**: Gestire attività che non richiedono una risposta immediata
2. **Bilanciamento del carico**: Distribuire il lavoro tra più consumer
3. **Buffering dei picchi di carico**: Assorbire picchi di attività senza sovraccaricare i sistemi di backend
4. **Comunicazione tra microservizi**: Consentire a servizi indipendenti di comunicare senza accoppiamento diretto
5. **Pipeline di elaborazione**: Implementare flussi di lavoro a più stadi

## Estensioni Possibili

Questo esempio base potrebbe essere esteso in vari modi:

1. **Consumer multipli**: Aggiungere più consumer che leggono dallo stesso topic
2. **Producer multipli**: Avere più producer che pubblicano sullo stesso topic
3. **Acknowledgement**: Implementare conferme di lettura per i messaggi
4. **Elaborazione reale**: Sostituire la semplice stampa con elaborazione effettiva dei dati
5. **Gestione degli errori**: Aggiungere logica per la gestione di errori di connessione e retry
6. **Filtraggio dei messaggi**: Implementare un sistema di selezione basato su criteri specifici
