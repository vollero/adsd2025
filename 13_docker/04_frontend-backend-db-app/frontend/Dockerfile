# Usa un'immagine ufficiale Nginx come base
FROM nginx:alpine

# Rimuovi la configurazione di default di Nginx
# RUN rm /etc/nginx/conf.d/default.conf

# Copia i file statici del frontend nella directory di Nginx
# La cartella 'html' nel contesto di build (frontend/html) viene copiata in /usr/share/nginx/html
COPY ./html/ /usr/share/nginx/html/

# Esponi la porta 80 (Nginx ascolta sulla 80 di default)
EXPOSE 80

# Il comando CMD è ereditato dall'immagine base nginx:alpine e avvia Nginx.
# Non è necessario specificarlo di nuovo a meno che tu non voglia cambiarlo.
