#!/bin/bash
# Esempi di chiamate cURL per il Key-Value Store

# Ottieni informazioni generali
curl -X GET "http://localhost:8050/" -H "accept: application/json"; echo

# Ottieni tutte le chiavi presenti
curl -X GET "http://localhost:8050/keys" -H "accept: application/json"; echo

# Inserisci un nuovo valore
curl -X PUT "http://localhost:8050/key/miachiave" \
  -H "Content-Type: application/json" \
  -d '{"value": "miovalore"}'; echo

# Leggi un valore
curl -X GET "http://localhost:8050/key/miachiave" -H "accept: application/json"; echo

# Aggiorna un valore esistente
curl -X PUT "http://localhost:8050/key/miachiave" \
  -H "Content-Type: application/json" \
  -d '{"value": "nuovo_valore"}'; echo

# Elimina una chiave
curl -X DELETE "http://localhost:8050/key/miachiave" -H "accept: application/json"; echo

# Forza la sincronizzazione del batch con il database
curl -X POST "http://localhost:8050/force-sync" -H "accept: application/json"; echo

# Ottieni statistiche sul sistema
curl -X GET "http://localhost:8050/stats" -H "accept: application/json"; echo

# Cancella la cache
curl -X POST "http://localhost:8050/clear-cache" -H "accept: application/json"; echo

# Esempi di messa sotto stress del sistema
# ---------------------------------------

# Script per inserire 2000 chiavi con valori casuali
#for i in {1..2000}; do
#  curl -s -X PUT "http://localhost:8050/key/stress_key_$i" \
#    -H "Content-Type: application/json" \
#    -d "{\"value\": \"valore_casuale_$RANDOM\"}" > /dev/null
#  echo "Inserita chiave stress_key_$i"
#done

# Inserimento di un valore grande per testare i limiti della cache (dimensione ridotta)
big_value=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 50000 | head -n 1)
curl -X PUT "http://localhost:8050/key/grande_valore" \
  -H "Content-Type: application/json" \
  -d "{\"value\": \"$big_value\"}"

# Richieste parallele per testare la concorrenza
# Richiede GNU Parallel: sudo apt-get install parallel
if command -v parallel &> /dev/null; then
  seq 1 20 | parallel -j 10 curl -s -X GET "http://localhost:8050/key/stress_key_{}" -H "accept: application/json"
fi

# Ottieni un valore che non esiste (dovrebbe restituire 404)
curl -X GET "http://localhost:8050/key/non_esiste" -H "accept: application/json"; echo

# Esempio di operazioni in batch
# ------------------------------

# Inserisce 5 chiavi senza forzare la sincronizzazione
for i in {1..5}; do
  curl -s -X PUT "http://localhost:8050/key/batch_key_$i" \
    -H "Content-Type: application/json" \
    -d "{\"value\": \"batch_value_$i\"}" > /dev/null
done

# Verifica lo stato del batch
curl -X GET "http://localhost:8050/stats" -H "accept: application/json"; echo

# Forza la sincronizzazione
curl -X POST "http://localhost:8050/force-sync" -H "accept: application/json"; echo

# Verifica lo stato dopo la sincronizzazione
curl -X GET "http://localhost:8050/stats" -H "accept: application/json"; echo
