# Cos'è una Socket?

Una socket è un'interfaccia di comunicazione tra due processi, sia all'interno dello stesso sistema (Inter-Process Communication, IPC) che tra macchine diverse connesse in rete. È il principale meccanismo utilizzato per realizzare la comunicazione tra client e server in ambienti distribuiti.

## Tipologie di Socket

Le socket si possono classificare in diverse categorie:

*Socket di dominio locale* (*Unix Domain Sockets - UDS*): utilizzate per la comunicazione tra processi sullo stesso sistema operativo.

*Socket di rete*: utilizzano protocolli come *TCP* e *UD*P per la comunicazione tra dispositivi connessi in rete.

*TCP* (Transmission Control Protocol): offre una comunicazione affidabile e orientata alla connessione.

*UDP* (User Datagram Protocol): offre una comunicazione senza connessione, veloce ma meno affidabile.
