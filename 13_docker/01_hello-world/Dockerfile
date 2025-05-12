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
