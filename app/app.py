from flask import Flask, request
import socket
import os

app = Flask(__name__)

@app.route('/')
def home():
    host_ip = request.host.split(':')[0]  # Get IP from the request
    host_name = socket.gethostname()      # Get hostname
    return f"Hello from VM running on {host_name} (IP: {host_ip})"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)