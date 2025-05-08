# Proposte di Elaborato: Architetture dei Sistemi Distribuiti

## Consegna Generale per gli Studenti

Per ciascuna delle seguenti proposte, lo studente (o il gruppo di studenti) dovrà affrontare un percorso completo che simula la realizzazione di un sistema distribuito in un contesto reale. Questo percorso include le seguenti fasi e relativi deliverable:

1.  **Analisi dei Requisiti**: Partendo dalla "Descrizione del Sistema" fornita per la traccia scelta, estrarre e documentare in modo chiaro le specifiche funzionali (cosa il sistema deve fare) e non funzionali (prestazioni, scalabilità, affidabilità, sicurezza, etc.).
2.  **Progettazione Architetturale**:
    * Definire l'architettura del sistema, identificando i componenti software principali (es. microservizi, moduli), le loro responsabilità e le interazioni tra di essi (es. API, protocolli di comunicazione).
    * Motivare le scelte tecnologiche (es. linguaggi, framework, sistemi di message queuing, database/key-value store, protocolli di comunicazione).
    * Descrivere come verranno indirizzati aspetti chiave dei sistemi distribuiti, quali: scalabilità, bilanciamento del carico, caching, consistenza dei dati, tolleranza ai guasti e resilienza.
    * Utilizzare diagrammi (es. diagrammi di componenti, di deployment, di sequenza) per illustrare l'architettura.
3.  **Piano di Sviluppo**: Delineare un piano di sviluppo per la realizzazione del Proof of Concept (PoC), identificando le principali milestone e attività.
4.  **Sviluppo del Proof of Concept (PoC)**:
    * Implementare una versione funzionante ma semplificata del sistema che dimostri le funzionalità chiave e l'applicazione pratica dei concetti di architetture distribuite discussi a lezione.
    * È richiesto l'uso appropriato di tecnologie viste durante il corso, come ad esempio: comunicazioni client-server, sistemi a broker (es. RabbitMQ, Kafka, MQTT o simili), interfacce/API RESTful, e container (es. Docker) per il deployment dei componenti. L'uso di key-value store distribuiti (o loro simulazione concettuale) è incoraggiato dove pertinente.
5.  **Test**:
    * Definire una strategia di test per il PoC, includendo test unitari per i componenti critici e test di integrazione per verificare le interazioni tra i servizi.
    * Eseguire i test e documentarne i risultati.
6.  **Documentazione**: Produrre una relazione tecnica completa che includa:
    * L'analisi dei requisiti.
    * La progettazione architetturale (con diagrammi e motivazioni delle scelte).
    * Il piano di sviluppo.
    * Una descrizione dell'implementazione del PoC, evidenziando le parti più significative e le sfide affrontate.
    * I risultati dei test.
    * Una guida essenziale per il deployment e l'esecuzione del PoC.
    * Eventuali considerazioni su evoluzioni future del sistema.

---

## Proposte di Sistemi da Sviluppare

### Proposta 1: Sistema di Gestione Distribuito per una Catena di "Food Delivery Ghost Kitchen"

* **Descrizione del Sistema:**
    Una catena emergente di "ghost kitchen" (cucine che operano esclusivamente per il delivery, senza servizio al tavolo) necessita di un sistema software centralizzato ma distribuito per ottimizzare le proprie operazioni. Ogni cucina affiliata alla catena possiede un menu specifico, che può subire variazioni frequenti (es. disponibilità giornaliera di ingredienti, offerte speciali). Gli ordini possono pervenire da diverse fonti (es. app proprietaria, piattaforme di delivery terze).
    Il sistema deve essere in grado di:
    1.  Ricevere ordini e instradarli intelligentemente alla cucina più idonea (considerando vicinanza al cliente, specializzazione della cucina, carico di lavoro attuale, disponibilità degli ingredienti per l'ordine specifico).
    2.  Permettere alle singole cucine di aggiornare in tempo reale la disponibilità dei piatti del proprio menu e il proprio stato operativo (aperta/chiusa, oberata di lavoro).
    3.  Tracciare lo stato di ogni ordine attraverso le sue fasi: ricevuto, accettato dalla cucina, in preparazione, pronto per il ritiro del rider, consegnato.
    4.  Fornire un pannello di controllo (dashboard) per la gestione centrale, che permetta di visualizzare le performance aggregate, lo stato delle cucine, e gestire centralmente aggiornamenti di menu di base o promozioni valide per tutta la catena o per gruppi di cucine.
    5.  Notificare i clienti (o le piattaforme esterne) sugli stati significativi dell'ordine.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi (es. Servizio Ordini, Servizio Menu, Servizio Cucine, Servizio Notifiche).
    * API REST per la comunicazione tra servizi e con entità esterne.
    * Sistemi a broker (es. Kafka, RabbitMQ) per la gestione asincrona degli ordini, degli aggiornamenti di stato e delle notifiche.
    * Key-value store distribuiti per la gestione dinamica dei menu, dello stato in tempo reale delle cucine e della cache di sessione degli ordini.
    * Strategie di bilanciamento del carico per i servizi esposti (es. ricezione ordini).
    * Meccanismi di caching per i dati frequently accessed (es. menu popolari, informazioni sulle cucine).
    * Containerizzazione (Docker) dei servizi.
    * Considerazioni sulla scalabilità orizzontale dei componenti.

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Implementare il servizio di ricezione ordini.
    * Simulare un meccanismo di base per l'instradamento di un ordine a una cucina (es. basato su un criterio semplice come la disponibilità).
    * Permettere a una "cucina" (simulata) di aggiornare lo stato di un ordine (es. "in preparazione", "pronto").
    * Implementare un servizio per la gestione dei menu (CRUD per i piatti di una cucina).
    * Esporre API REST per le funzionalità implementate.
    * Utilizzare un sistema a broker per almeno una comunicazione asincrona (es. notifica di nuovo ordine a un potenziale pool di cucine).
    * Containerizzare almeno due servizi distinti.

---

### Proposta 2: Piattaforma Distribuita per la Condivisione e Valutazione di Configurazioni per Gaming ("GameSetupHub")

* **Descrizione del Sistema:**
    Molti videogiocatori dedicano tempo a ottimizzare le configurazioni dei propri giochi (impostazioni grafiche, mappatura dei controlli, mod, ecc.) per migliorare l'esperienza di gioco o le performance. "GameSetupHub" si propone come una piattaforma comunitaria dove gli utenti possono caricare, ricercare, visualizzare, commentare e valutare (es. con un sistema di upvote/downvote o rating a stelle) le configurazioni per un vasto catalogo di videogiochi.
    Il sistema dovrà:
    1.  Permettere agli utenti di registrarsi e creare un profilo.
    2.  Consentire agli utenti autenticati di caricare configurazioni per giochi specifici. Una configurazione può includere testo descrittivo, file di configurazione (o il loro contenuto testuale), e tag.
    3.  Indicizzare e rendere ricercabili le configurazioni per gioco, per popolarità, per data di caricamento, o per tag.
    4.  Gestire un sistema di valutazione e commenti per ogni configurazione.
    5.  Potenzialmente, tracciare le versioni di una configurazione.
    6.  Garantire una buona performance nella ricerca e nella visualizzazione delle configurazioni, anche con un numero elevato di utenti e contenuti.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi (es. Servizio Utenti, Servizio Configurazioni, Servizio Ricerca, Servizio Valutazioni/Commenti).
    * API REST per l'interazione con la piattaforma.
    * Key-value store distribuiti o document store (es. MongoDB, Elasticsearch) per memorizzare le configurazioni (che sono dati semi-strutturati), i profili utente e le valutazioni.
    * Un motore di ricerca (o una sua implementazione semplificata basata sul data store scelto) per la funzionalità di ricerca.
    * Caching delle configurazioni più popolari o frequentemente accessi, e dei risultati di ricerca comuni.
    * Bilanciamento del carico per i servizi di frontend e di API.
    * Containerizzazione dei servizi.
    * Considerazioni sulla scalabilità per gestire un crescente numero di utenti, giochi, e configurazioni.
    * Potenziale uso di overlay networks per gestire comunità di utenti o gruppi di interesse (avanzato).

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Implementare la registrazione utente e l'upload di una configurazione (testo descrittivo e alcuni parametri chiave-valore).
    * Memorizzare le configurazioni in un data store idoneo (anche simulato se complesso, ma con API definite).
    * Permettere la visualizzazione di una configurazione caricata.
    * Implementare una ricerca base per nome del gioco.
    * Implementare un semplice sistema di "like" per una configurazione.
    * Esporre API REST per le funzionalità.
    * Containerizzare almeno due servizi.

---

### Proposta 3: Sistema Distribuito per il Monitoraggio e l'Allerta Precoce di Consumi Energetici Anomali ("EnergyGuard")

* **Descrizione del Sistema:**
    "EnergyGuard" è un sistema progettato per monitorare i consumi energetici di edifici o impianti industriali (simulati), identificare anomalie e generare allerte precoci. Sensori (simulati) installati presso diverse utenze inviano periodicamente (es. ogni minuto) dati di consumo energetico (es. kWh, potenza istantanea) al sistema centrale.
    Il sistema deve:
    1.  Ingerire in modo affidabile e scalabile i flussi di dati provenienti da un numero potenzialmente elevato di sensori.
    2.  Archiviare i dati storici dei consumi per analisi future.
    3.  Analizzare i dati in tempo (quasi) reale per identificare pattern di consumo anomali (es. picchi improvvisi, consumi fuori dalla media storica per quella fascia oraria/giorno della settimana, consumi a vuoto).
    4.  Permettere agli amministratori di definire soglie di allerta personalizzate per diverse utenze o tipi di sensori.
    5.  Generare notifiche (es. email, SMS simulati, webhook) quando vengono rilevate anomalie o superate le soglie.
    6.  Fornire un'interfaccia API per visualizzare i dati di consumo attuali e storici, e lo stato delle allerte.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura orientata agli eventi e microservizi (es. Servizio Ingestione Dati, Servizio Analisi/Rilevamento Anomalie, Servizio Notifiche, Servizio Archiviazione, Servizio API).
    * Sistemi a broker (es. Kafka, MQTT) per l'ingestione scalabile e disaccoppiata dei dati dai sensori.
    * Key-value store distribuiti o time-series database (o una loro implementazione concettuale) per l'archiviazione efficiente dei dati di telemetria e per stati intermedi dell'analisi.
    * Stream processing (opzionale, per analisi complesse in tempo reale).
    * API REST per la configurazione e la visualizzazione dei dati.
    * Containerizzazione dei servizi.
    * Scalabilità dei componenti di ingestione e analisi.
    * Caching per i dati di dashboard o per i risultati di analisi recenti.
    * Strategie di bilanciamento del carico per i punti di ingestione e le API.

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Simulare l'invio di dati da parte di alcuni sensori.
    * Implementare un servizio di ingestione che riceva i dati (preferibilmente tramite un broker) e li memorizzi in un data store (anche un semplice K-V store per il PoC).
    * Implementare una logica base di rilevamento anomalie (es. superamento di una soglia statica) sui dati ricevuti.
    * Generare una "notifica" (es. un log, una entry in un database dedicato) quando un'anomalia è rilevata.
    * Esporre un'API REST per inviare dati "simulati" e per visualizzare le ultime N misurazioni o le allerte recenti.
    * Containerizzare almeno il servizio di ingestione e il servizio di analisi/notifica.

---

### Proposta 4: Sistema di Coordinamento Distribuito per Flotte di Droni per Consegne (Simulato) ("DroneDispatch")

* **Descrizione del Sistema:**
    Un'azienda sta sperimentando l'uso di droni per piccole consegne in aree urbane. È necessario un sistema "DroneDispatch" per coordinare una flotta di droni (simulati). Il sistema deve ricevere richieste di consegna (origine, destinazione, peso pacco). Deve assegnare una consegna a un drone disponibile e idoneo (es. con sufficiente batteria, capacità di carico), tenendo conto della sua posizione attuale. Il sistema deve tracciare la posizione dei droni (simulata), lo stato della batteria (simulata) e lo stato della consegna (in attesa, in volo, consegnato). Deve essere possibile visualizzare lo stato della flotta e delle consegne in corso.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi.
    * API REST per l'invio di richieste di consegna e per interrogare lo stato del sistema.
    * Comunicazione client-server (i droni simulati comunicano il loro stato).
    * Un sistema a broker per la gestione degli eventi (nuova richiesta di consegna, aggiornamento stato drone, completamento consegna).
    * Un key-value store distribuito per mantenere lo stato in tempo reale dei droni (posizione, batteria, disponibilità) e delle consegne.
    * Algoritmi (semplificati) di scheduling/assegnazione delle consegne ai droni (potrebbe coinvolgere un overlay logico per la gestione delle zone).
    * Bilanciamento del carico se il numero di richieste di consegna è elevato.
    * Caching dello stato dei droni o delle zone per decisioni rapide di assegnazione.
    * Container per il deployment.
    * Scalabilità per gestire più droni e più richieste.

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Implementare la registrazione di un drone simulato nel sistema.
    * La ricezione di una richiesta di consegna.
    * Un algoritmo base per assegnare la consegna a un drone disponibile (es. il più vicino o il primo disponibile).
    * Simulazione dell'aggiornamento dello stato del drone (posizione, batteria) e della consegna.
    * Un endpoint API per visualizzare lo stato di un drone e di una consegna.
    * Utilizzo di un broker per la gestione delle richieste di consegna o degli aggiornamenti di stato.
    * 
 ---

### Proposta 5: Sistema di Gestione Code Distribuito ("QMaster")

* **Descrizione del Sistema:**
    "QMaster" è un sistema progettato per gestire code di attesa in contesti diversi, come uffici pubblici, cliniche mediche, eventi con ingressi contingentati o attrazioni in parchi divertimento. Gli utenti (o il personale addetto) possono richiedere un "numero" per una specifica coda o servizio. Il sistema deve:
    1.  Assegnare numeri progressivi in modo univoco per ciascuna coda attiva.
    2.  Permettere agli operatori (o a un sistema automatico) di "chiamare" il numero successivo per ogni coda.
    3.  Consentire agli utenti di visualizzare lo stato attuale di una o più code (es. ultimo numero chiamato, numeri in attesa) tramite display informativi (simulati) o un'interfaccia web/mobile (API).
    4.  Gestire più code contemporaneamente, potenzialmente distribuite in diverse postazioni o sportelli.
    5.  Offrire la possibilità (opzionale) agli utenti di richiedere un numero da remoto (tramite un'app simulata o API) e ricevere una notifica quando il proprio turno si avvicina.
    6.  Garantire l'affidabilità del sistema anche in caso di guasto di un singolo componente che gestisce una postazione.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi (es. Servizio Gestione Code, Servizio Assegnazione Numeri, Servizio Notifiche, Servizio Display).
    * API REST per l'interazione con gli operatori, i display e le richieste remote.
    * Sistemi a broker (es. RabbitMQ, Redis Pub/Sub) per la gestione delle richieste di avanzamento coda, per le notifiche agli utenti e per l'aggiornamento dei display in tempo reale.
    * Key-value store distribuiti (es. Redis, etcd) per mantenere lo stato corrente delle code (ultimo numero chiamato, lista d'attesa), garantendo accessi rapidi e consistenza.
    * Meccanismi di locking distribuito o strategie per la gestione della concorrenza nell'assegnazione dei numeri e nella chiamata.
    * Scalabilità per gestire un elevato numero di code e utenti concorrenti.
    * Caching dello stato delle code per i display.
    * Containerizzazione dei servizi.

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Implementare la creazione di una coda.
    * Permettere la richiesta di un nuovo numero per una coda specifica.
    * Permettere a un operatore di "chiamare" il numero successivo.
    * Esporre API REST per visualizzare lo stato di una coda (ultimo numero chiamato, prossimo da chiamare).
    * Utilizzare un sistema a broker per notificare l'aggiornamento dello stato della coda a un "display" simulato (es. un client che logga l'evento).
    * Memorizzare lo stato della coda in un key-value store (o simulazione).
    * Containerizzare almeno due servizi.

---

### Proposta 6: Piattaforma Collaborativa Semplificata di Annotazione Testi ("TextAnnotate")

* **Descrizione del Sistema:**
    "TextAnnotate" è una piattaforma web-based che permette a gruppi di utenti di collaborare all'annotazione di documenti testuali. Gli utenti possono caricare documenti di testo semplice. Una volta caricato un documento, gli utenti autorizzati possono selezionare porzioni di testo e associare ad esse etichette (tag) o brevi commenti. Il sistema deve:
    1.  Gestire l'autenticazione degli utenti e i permessi di accesso ai documenti (chi può visualizzare, chi può annotare).
    2.  Permettere l'upload di documenti di testo.
    3.  Consentire la creazione, visualizzazione, modifica (limitata) e cancellazione di annotazioni su specifiche porzioni di testo (identificate ad esempio da indici di inizio/fine).
    4.  Visualizzare il testo con le relative annotazioni in modo chiaro.
    5.  Gestire la concorrenza in modo che più utenti possano visualizzare un documento contemporaneamente, con strategie semplici per la gestione di annotazioni concorrenti sullo stesso frammento (es. last-write-wins con timestamp, o versionamento semplice).
    6.  Mantenere uno storico delle annotazioni o delle versioni del documento annotato (funzionalità opzionale per il PoC).

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi (es. Servizio Documenti, Servizio Annotazioni, Servizio Utenti/Permessi).
    * API REST per tutte le interazioni client-server.
    * Key-value store distribuiti o document-oriented database (es. MongoDB) per memorizzare i documenti, le annotazioni (che possono essere JSON complessi) e i metadati.
    * Tecnologie per la comunicazione in tempo reale (opzionale, es. WebSockets) per notificare agli altri visualizzatori le nuove annotazioni.
    * Caching dei documenti e delle annotazioni più frequentemente accessi.
    * Strategie di gestione della consistenza per le annotazioni.
    * Containerizzazione dei servizi.
    * Scalabilità per supportare molti utenti e documenti.

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Implementare l'upload di un documento di testo.
    * Permettere a un utente di aggiungere un'annotazione (tag testuale) a una porzione di testo selezionata (identificata da offset).
    * Memorizzare il documento e le sue annotazioni.
    * Visualizzare il documento con le annotazioni esistenti.
    * Esporre API REST per le funzionalità.
    * Gestire una forma base di concorrenza (es. le annotazioni vengono semplicemente aggiunte, senza lock complessi per il PoC).
    * Containerizzare almeno due servizi.

---

### Proposta 7: Servizio di Notifica Eventi Personalizzati Basato su Abbonamento ("EventAlert")

* **Descrizione del Sistema:**
    "EventAlert" è un servizio che consente agli utenti di abbonarsi a notifiche per specifici argomenti o eventi di loro interesse. Le fonti degli eventi possono essere svariate (altri sistemi, feed RSS simulati, inserimenti manuali da amministratori). Quando un nuovo evento che corrisponde ai criteri di sottoscrizione di un utente viene pubblicato nel sistema, l'utente riceve una notifica (es. email simulata, messaggio in un log, webhook verso un endpoint specificato dall'utente). Il sistema deve:
    1.  Permettere agli utenti (o sistemi client) di creare, visualizzare, modificare ed eliminare sottoscrizioni a specifici "topic" o pattern di eventi (es. "nuovi_prodotti_elettronica", "meteo_milano_pioggia", "aggiornamento_sistema_X").
    2.  Fornire un'interfaccia (API) per la pubblicazione di nuovi eventi nel sistema, specificando il topic e il payload dell'evento.
    3.  Realizzare un motore di "matching" che, alla ricezione di un nuovo evento, identifichi tutti gli utenti/sottoscrizioni corrispondenti.
    4.  Inviare le notifiche in modo affidabile e scalabile.
    5.  Gestire un elevato numero di sottoscrizioni e un alto volume di eventi e notifiche.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi (Servizio Sottoscrizioni, Servizio Pubblicazione Eventi, Servizio Matching/Dispatching Notifiche, Servizio Notifiche Effettive).
    * Sistemi a broker (es. Kafka, RabbitMQ, NATS) come cuore del sistema per la pubblicazione degli eventi e il loro smistamento ai dispatcher.
    * API REST per la gestione delle sottoscrizioni e la pubblicazione degli eventi.
    * Key-value store distribuiti (es. Redis, Cassandra) per memorizzare le sottoscrizioni utente (indicizzate per topic per ricerche veloci) e potenzialmente lo stato delle notifiche.
    * Scalabilità orizzontale dei componenti di matching e notifica.
    * Caching dei topic popolari o delle regole di matching.
    * Containerizzazione dei servizi.
    * Considerazioni sulla resilienza (es. ritentativi per le notifiche fallite).

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Implementare un endpoint API per creare una sottoscrizione a un "topic" specifico da parte di un utente (simulato).
    * Implementare un endpoint API per pubblicare un evento su un "topic".
    * Quando un evento è pubblicato, il sistema deve identificare le sottoscrizioni corrispondenti (matching per topic esatto).
    * Simulare l'invio di una notifica (es. scrivendo un log "Notifica per utente X: evento Y su topic Z").
    * Utilizzare un sistema a broker per la gestione degli eventi pubblicati.
    * Memorizzare le sottoscrizioni in un K-V store (o simulazione).
    * Containerizzare almeno due servizi.

---

### Proposta 8: Sistema di Prenotazione Distribuito per Risorse Condivise ("ResourceBooker")

* **Descrizione del Sistema:**
    "ResourceBooker" è un sistema per la gestione e la prenotazione di risorse condivise all'interno di un'organizzazione (es. aule riunioni in un'azienda, attrezzature speciali in un laboratorio universitario, campi da gioco in un centro sportivo). Il sistema deve:
    1.  Permettere agli amministratori di definire le risorse disponibili, le loro caratteristiche (es. capacità, attrezzature presenti) e gli slot temporali prenotabili (es. fasce orarie, giorni della settimana).
    2.  Consentire agli utenti autenticati di cercare risorse disponibili in base a criteri (es. data, ora, tipo di risorsa, capacità minima).
    3.  Permettere agli utenti di prenotare uno slot disponibile per una risorsa.
    4.  Prevenire doppie prenotazioni (conflitti) per la stessa risorsa nello stesso slot temporale.
    5.  Consentire agli utenti di visualizzare e cancellare le proprie prenotazioni.
    6.  Inviare notifiche di conferma prenotazione e reminder (opzionale per il PoC).
    7.  Essere scalabile per gestire numerose risorse e un alto volume di richieste di prenotazione.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi (es. Servizio Risorse, Servizio Prenotazioni, Servizio Utenti, Servizio Notifiche).
    * API REST per tutte le interazioni.
    * Key-value store distribuiti o database SQL/NoSQL con buone capacità di gestione della concorrenza per memorizzare lo stato delle risorse, gli slot disponibili e le prenotazioni.
    * Meccanismi di locking distribuito o transazioni distribuite (semplificate) per garantire la consistenza durante la prenotazione e prevenire conflitti.
    * Caching della disponibilità delle risorse per periodi di tempo specifici per velocizzare le ricerche.
    * Sistemi a broker per gestire le notifiche asincrone (conferme, reminder).
    * Containerizzazione dei servizi.
    * Bilanciamento del carico per i servizi API.

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Implementare la definizione di una risorsa con slot temporali (es. orari fissi per un giorno).
    * Permettere a un utente di visualizzare gli slot disponibili per una risorsa in una data specifica.
    * Permettere a un utente di prenotare uno slot disponibile.
    * Impedire la prenotazione di uno slot già occupato (gestione base dei conflitti).
    * Esporre API REST per le funzionalità.
    * Memorizzare le risorse e le prenotazioni in un data store.
    * Containerizzare almeno due servizi.

---

### Proposta 9: Backend Distribuito per la Raccolta e Analisi Preliminare di Log da Dispositivi IoT ("IoTLogHub")

* **Descrizione del Sistema:**
    "IoTLogHub" è un sistema backend progettato per raccogliere, archiviare ed effettuare un'analisi preliminare dei log provenienti da una vasta flotta di dispositivi IoT (Internet of Things) simulati. Ogni dispositivo invia periodicamente messaggi di log contenenti informazioni sul suo stato, errori, o eventi specifici. Il sistema deve:
    1.  Fornire un endpoint sicuro e scalabile per l'ingestione dei messaggi di log dai dispositivi IoT. I log possono avere formati diversi (es. JSON, testo semplice strutturato).
    2.  Validare e processare preliminarmente i log in arrivo (es. parsing, arricchimento con timestamp di ricezione, identificativo del dispositivo).
    3.  Archiviare i log in modo efficiente per consentire ricerche e analisi successive.
    4.  Effettuare analisi di base in tempo (quasi) reale o batch sui log ricevuti, come il conteggio di errori per tipo di dispositivo, il rilevamento di pattern frequenti, o la generazione di statistiche aggregate.
    5.  Fornire API per interrogare i log archiviati (es. per dispositivo, per intervallo di tempo, per tipo di errore) e per visualizzare i risultati delle analisi preliminari.
    6.  Essere in grado di scalare per gestire un numero elevato di dispositivi e un alto volume di messaggi di log.

* **Tecnologie e Concetti Chiave Suggeriti per la Riflessione:**
    * Architettura a microservizi (es. Servizio Ingestione, Servizio Processing/Parsing, Servizio Archiviazione, Servizio Analisi, Servizio API Query).
    * Protocolli di comunicazione leggeri per IoT (es. MQTT, CoAP, o HTTP per la simulazione) per l'invio dei log.
    * Sistemi a broker (es. Kafka, RabbitMQ, MQTT broker) per l'ingestione disaccoppiata e resiliente dei log.
    * Key-value store distribuiti, document store, o time-series database (es. Elasticsearch, InfluxDB, Cassandra) ottimizzati per l'archiviazione e l'interrogazione di grandi volumi di dati di log.
    * Framework di stream processing (opzionale, es. Apache Flink/Spark Streaming, Kafka Streams) per analisi in tempo reale.
    * API REST per l'interrogazione dei log e dei risultati delle analisi.
    * Containerizzazione di tutti i servizi.
    * Bilanciamento del carico sui punti di ingestione e sulle API di query.
    * Strategie di partizionamento e indicizzazione dei dati per ricerche efficienti.

* **Obiettivi Minimi del Proof of Concept (PoC):**
    * Simulare l'invio di messaggi di log (strutturati, es. JSON) da parte di alcuni dispositivi IoT (client simulati).
    * Implementare un servizio di ingestione che riceva i log (preferibilmente tramite un broker) e li memorizzi.
    * Implementare un parser base se i log non sono già in formato facilmente interrogabile.
    * Memorizzare i log in un data store (es. K-V store o document store).
    * Esporre un'API REST per recuperare i log di un dispositivo specifico o gli ultimi N log ricevuti.
    * Implementare una semplice analisi (es. contare il numero di log con un certo "livello di errore" per dispositivo).
    * Containerizzare almeno il servizio di ingestione e un servizio di query/analisi.
    * Containerizzare almeno due servizi.
