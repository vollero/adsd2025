import time
import random
import requests
import os
import json

PROCESS_ID = 2  # Indice nel vettore orologio
NUM_PROCESSES = 3
VECTOR_CLOCK = [0] * NUM_PROCESSES
OTHER_CONTAINERS = ["container_1", "container_2"]
MESSAGE_INTERVAL = 5
EVENT_INTERVAL = random.uniform(1, 3)

def log_event(event):
    global VECTOR_CLOCK
    VECTOR_CLOCK[PROCESS_ID] += 1
    print(f"Container {PROCESS_ID + 1}: {event} (Clock: {VECTOR_CLOCK})")

def send_message(recipient, message):
    global VECTOR_CLOCK
    VECTOR_CLOCK[PROCESS_ID] += 1
    timestamp = list(VECTOR_CLOCK)
    log_event(f"Sending '{message}' to {recipient} with timestamp {timestamp}")
    try:
        requests.post(f"http://{recipient}:5000/receive", json={"sender_id": PROCESS_ID + 1, "message": message, "timestamp": timestamp})
    except requests.exceptions.ConnectionError as e:
        print(f"Container {PROCESS_ID + 1}: Error sending to {recipient}: {e}")

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/receive', methods=['POST'])
def receive_message():
    global VECTOR_CLOCK
    data = request.get_json()
    sender_id = data['sender_id'] - 1
    message = data['message']
    received_timestamp = data['timestamp']

    for i in range(NUM_PROCESSES):
        VECTOR_CLOCK[i] = max(VECTOR_CLOCK[i], received_timestamp[i])
    VECTOR_CLOCK[PROCESS_ID] += 1
    log_event(f"Received '{message}' from Container {sender_id + 1} (Sender's Clock: {received_timestamp})")
    return jsonify({"status": "received", "local_clock": VECTOR_CLOCK}), 200

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
            recipient_name = random.choice(OTHER_CONTAINERS)
            send_message(recipient_name, f"Progress update from Container {PROCESS_ID + 1}")

    task_thread = threading.Thread(target=worker)
    comm_thread = threading.Thread(target=communicator)

    task_thread.start()
    comm_thread.start()

    app.run(host='0.0.0.0', port=5000)
