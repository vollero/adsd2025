# Cos'è una Socket?

Una socket è un'interfaccia di comunicazione tra due processi, sia all'interno dello stesso sistema (Inter-Process Communication, IPC) che tra macchine diverse connesse in rete. È il principale meccanismo utilizzato per realizzare la comunicazione tra client e server in ambienti distribuiti.

## Tipologie di Socket

Le socket si possono classificare in diverse categorie:

**Socket di dominio locale** (**Unix Domain Sockets** - **UDS**): utilizzate per la comunicazione tra processi sullo stesso sistema operativo.

**Socket di rete**: utilizzano protocolli come **TCP** e **UDP** per la comunicazione tra dispositivi connessi in rete.

**TCP** (Transmission Control Protocol): offre una comunicazione affidabile e orientata alla connessione.

**UDP** (User Datagram Protocol): offre una comunicazione senza connessione, veloce ma meno affidabile.

## Protocolli di Comunicazione: TCP e UDP

### Transmission Control Protocol (TCP)

Il TCP (Transmission Control Protocol) è un protocollo di livello trasporto che fornisce un servizio di comunicazione affidabile e orientato alla connessione. Le sue caratteristiche principali includono:

- Affidabilità: garantisce la consegna dei dati senza errori e nella sequenza corretta.

- Controllo di congestione: previene il sovraccarico della rete.

- Ritrasmissione: i pacchetti persi vengono automaticamente ritrasmessi.

- Handshake a tre vie: stabilisce una connessione tramite un processo di negoziazione in tre fasi.

RFC di riferimento:

- RFC 793 - Transmission Control Protocol

- RFC 1122 - Requirements for Internet Hosts

### User Datagram Protocol (UDP)

L'UDP (User Datagram Protocol) è un protocollo di livello trasporto che fornisce un servizio di comunicazione senza connessione. Le sue caratteristiche principali includono:

- Bassa latenza: adatto per applicazioni in tempo reale come VoIP e streaming.

- Assenza di ritrasmissione: non garantisce la consegna dei pacchetti né l'ordine corretto.

- Semplicità: utilizza meno overhead rispetto a TCP, risultando più veloce.

RFC di riferimento:

- RFC 768 - User Datagram Protocol

- RFC 1122 - Requirements for Internet Hosts
