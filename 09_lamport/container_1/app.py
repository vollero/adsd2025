import time
import random
import requests
import os

PROCESS_ID = 1
LOGICAL_CLOCK = 0
OTHER_CONTAINERS = ["container_2", "container_3"]
MESSAGE_INTERVAL = 5  # Secondi
EVENT_INTERVAL = random.uniform(1, 3)  # Secondi

def log_event(event):
    global LOGICAL_CLOCK
    LOGICAL_CLOCK += 1
    print(f"Container {PROCESS_ID}: {event} (Clock: {LOGICAL_CLOCK})")

def send_message(recipient, message):
    global LOGICAL_CLOCK
    LOGICAL_CLOCK += 1
    timestamp = LOGICAL_CLOCK
    log_event(f"Sending '{message}' to {recipient} with timestamp {timestamp}")
    try:
        requests.post(f"http://{recipient}:5000/receive", json={"sender_id": PROCESS_ID, "message": message, "timestamp": timestamp})
    except requests.exceptions.ConnectionError as e:
        print(f"Container {PROCESS_ID}: Error sending to {recipient}: {e}")

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/receive', methods=['POST'])
def receive_message():
    global LOGICAL_CLOCK
    data = request.get_json()
    sender_id = data['sender_id']
    message = data['message']
    received_timestamp = data['timestamp']
    LOGICAL_CLOCK = max(LOGICAL_CLOCK, received_timestamp) + 1
    log_event(f"Received '{message}' from Container {sender_id} (Sender's Clock: {received_timestamp})")
    return jsonify({"status": "received", "local_clock": LOGICAL_CLOCK}), 200

def simulate_task():
    time.sleep(random.uniform(2, 5))
    log_event("Completed a part of the task")

if __name__ == '__main__':
    import threading

    def worker():
        while True:
            simulate_task()
            time.sleep(EVENT_INTERVAL)

    def communicator():
        while True:
            time.sleep(MESSAGE_INTERVAL)
            recipient = random.choice(OTHER_CONTAINERS)
            send_message(recipient, f"Progress update from Container {PROCESS_ID}")

    task_thread = threading.Thread(target=worker)
    comm_thread = threading.Thread(target=communicator)

    task_thread.start()
    comm_thread.start()

    app.run(host='0.0.0.0', port=5000)
