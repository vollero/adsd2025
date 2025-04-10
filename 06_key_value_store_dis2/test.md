# Genera 5000 chiavi e analizza la loro distribuzione (non scrive nei database)
python test_client.py test-distribution --count 5000

# Cambia il fattore di replica al 30%
python test_client.py reconfigure --replication-factor 0.3 --virtual-nodes 100

# Ribilancia le chiavi
python test_client.py rebalance

# Verifica la nuova distribuzione
python test_client.py sharding-info

# Genera 5000 chiavi e analizza la loro distribuzione (non scrive nei database)
python test_client.py test-distribution --count 5000

# Prova con una replica al 70%
python test_client.py reconfigure --replication-factor 0.7 --virtual-nodes 100
python test_client.py rebalance
python test_client.py sharding-info

# Genera 5000 chiavi e analizza la loro distribuzione (non scrive nei database)
python test_client.py test-distribution --count 5000

# Usa pochi nodi virtuali
python test_client.py reconfigure --replication-factor 0.5 --virtual-nodes 10
python test_client.py ebalance
python test_client.py test-distribution --count 1000

# Usa molti nodi virtuali
python test_client reconfigure --replication-factor 0.5 --virtual-nodes 200
python test_client.py rebalance
python test_client.py test-distribution --count 1000

# Inserisci una chiave di test
python test_client.py put test_key1 "valore di test"

# Verifica dove è memorizzata
python test_client.py node-for-key test_key1

# Controlla se è presente sui nodi previsti
# Sostituisci "kvstore1:8050" con un nodo restituito dal comando precedente
python test_client.py node-keys kvstore1:8050


# 1. Configura il sistema
python test_clientg.py reconfigure --replication-factor 0.5 --virtual-nodes 100

# 2. Crea alcune chiavi
python test_client.py put chiave1 "valore1"
python test_client.py put chiave2 "valore2"
python test_client.py put chiave3 "valore3"

# 3. Verifica la distribuzione
python test_client.py node-for-key chiave1
python test_client.py node-for-key chiave2
python test_client.py node-for-key chiave3

# 4. Recupera le chiavi
python test_client.py get chiave1
python test_client.py get chiave2
python test_client.py get chiave3

# 5. Modifica una chiave
python test_client.py put chiave2 "nuovo-valore2"
python test_client.py get chiave2

# 6. Elimina una chiave
python test_client.py delete chiave3
python test_client.py keys

# 7. Visualizza statistiche
python test_client.py stats



# 1. Inserisci un buon numero di chiavi
for i in {1..50}; do python test_client.py put key$i "value$i"; done

# 2. Verifica la distribuzione iniziale
python test_client.py sharding-info

# 3. Cambia la configurazione
python test_client.py reconfigure --replication-factor 0.6 --virtual-nodes 150

# 4. Esegui il ribilanciamento
python test_client.py rebalance

# 5. Verifica la nuova distribuzione
python test_client.py sharding-info

# 6. Verifica che le chiavi siano ancora accessibili
python test_client.py get key10
python test_client.py get key20
python test_client.py get key30

