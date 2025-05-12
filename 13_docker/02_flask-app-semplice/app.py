from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Ciao dal mio servizio Flask in un container Docker!"

@app.route('/api/info')
def info():
    return jsonify({
        "applicazione": "Flask App Semplice",
        "versione": "1.0",
        "messaggio": "Servizio API di base"
    })

if __name__ == '__main__':
    # Ascolta su tutte le interfacce di rete (0.0.0.0)
    # e sulla porta 5000 (porta di default di Flask)
    app.run(host='0.0.0.0', port=5000, debug=True)
