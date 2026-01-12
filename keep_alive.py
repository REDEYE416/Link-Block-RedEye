from flask import Flask, jsonify
from threading import Thread
import time
import requests
import os

app = Flask(__name__)

# Health check endpoint
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Discord Link Remover Bot",
        "timestamp": time.time()
    })

# Health check endpoint for Render
@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# Ping endpoint to keep alive
@app.route('/ping')
def ping():
    return "pong", 200

# Bot status endpoint
@app.route('/status')
def status():
    return jsonify({
        "bot": "Link Remover Bot",
        "owner_id": os.environ.get('OWNER_ID', 'Not set'),
        "env": "production"
    })

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_keep_alive():
    """
    Start Flask server in a separate thread
    This keeps the Render web service alive
    """
    print("🌐 Starting Flask keep-alive server...")
    t = Thread(target=run, daemon=True)
    t.start()
    print(f"✅ Keep-alive server started on port {os.environ.get('PORT', 8080)}")
    return t

if __name__ == "__main__":
    start_keep_alive()
    # Keep the main thread alive
    while True:
        time.sleep(60)
