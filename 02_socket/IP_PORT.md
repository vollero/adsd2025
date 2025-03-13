# Indirizzo IP e Porta di Comunicazione

## Cos'è un Indirizzo IP?
Un **indirizzo IP (Internet Protocol Address)** è un identificatore numerico assegnato a ogni dispositivo connesso a una rete informatica basata sul protocollo Internet (IP). Gli indirizzi IP servono per identificare un dispositivo univocamente e per instradare i dati attraverso una rete.

### Tipologie di Indirizzi IP
Gli indirizzi IP si suddividono principalmente in due categorie:
- **IPv4**: un indirizzo a 32 bit, rappresentato in formato decimale separato da punti (es. `192.168.1.1`).
- **IPv6**: un indirizzo a 128 bit, scritto in notazione esadecimale separata da due punti (es. `2001:0db8:85a3::8a2e:0370:7334`).

### Classi di Indirizzi IPv4
Gli indirizzi IPv4 sono suddivisi in diverse classi, ognuna con un intervallo specifico:
- **Classe A**: `1.0.0.0 - 126.255.255.255`
- **Classe B**: `128.0.0.0 - 191.255.255.255`
- **Classe C**: `192.0.0.0 - 223.255.255.255`
- **Classe D**: `224.0.0.0 - 239.255.255.255` (Multicast)
- **Classe E**: `240.0.0.0 - 255.255.255.255` (Riservato)

### Indirizzi IP Privati e Pubblici
- **Indirizzi privati**: utilizzati nelle reti locali e non instradabili su Internet. Gli intervalli più comuni sono:
  - `10.0.0.0 - 10.255.255.255`
  - `172.16.0.0 - 172.31.255.255`
  - `192.168.0.0 - 192.168.255.255`
- **Indirizzi pubblici**: assegnati da un provider Internet (ISP) e accessibili da Internet.

---

## Cos'è una Porta di Comunicazione?
Una **porta di comunicazione** è un numero che identifica un processo o un servizio specifico in esecuzione su un dispositivo di rete. Le porte consentono a più servizi di operare simultaneamente su una singola macchina.

### Classificazione delle Porte
Le porte sono numerate da **0 a 65535** e sono suddivise in tre categorie:
- **Porte Well-Known (0-1023)**: utilizzate per servizi standard (es. `HTTP` su porta `80`, `HTTPS` su porta `443`, `SSH` su porta `22`).
- **Porte Registrate (1024-49151)**: assegnate a servizi specifici (es. `MySQL` su porta `3306`).
- **Porte Dinamiche o Private (49152-65535)**: utilizzate temporaneamente da applicazioni client per connessioni.

### Associazione tra IP e Porta
Un dispositivo può essere identificato tramite una coppia `IP:Porta`. Ad esempio:
- `192.168.1.10:80` indica che il dispositivo con IP `192.168.1.10` sta offrendo un servizio HTTP sulla porta `80`.

---
