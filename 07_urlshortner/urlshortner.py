from flask import Flask, request, redirect, jsonify
import sqlite3
import hashlib

app = Flask(__name__)

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY, short_url TEXT, long_url TEXT)')
        db.commit()

def get_db():
    db = sqlite3.connect('urls.db')
    db.row_factory = sqlite3.Row
    return db

@app.route('/')
def index():
    return 'URL Shortener API'

# Endpoint to create a short URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.json['url']
    url_hash = hashlib.sha256(long_url.encode()).hexdigest()[:6]
    db = get_db()
    db.execute('INSERT INTO urls (short_url, long_url) VALUES (?, ?)', (url_hash, long_url))
    db.commit()
    db.close()
    return jsonify({'short_url': f'http://localhost:6000/{url_hash}'})

# Redirect from a short URL
@app.route('/<short_url>')
def redirect_short_url(short_url):
    db = get_db()
    url_data = db.execute('SELECT long_url FROM urls WHERE short_url = ?', (short_url,)).fetchone()
    db.close()
    if url_data:
        #return redirect(url_data['long_url']) #default 302
        return redirect(url_data['long_url'], 301)
    return 'URL not found', 404

init_db()
app.run(debug=True)
