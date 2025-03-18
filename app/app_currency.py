from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import threading
import time

app = Flask(__name__)
API_URL = "https://open.er-api.com/v6/latest/USD"

currency_data = {"time": "", "currencies": []}

def update_currency_data():
    global currency_data
    while True:
        response = requests.get(API_URL)
        data = response.json()
        currencies = sorted(data['rates'].items(), key=lambda x: x[1], reverse=True)[:10]
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        currency_data = {"time": current_time, "currencies": currencies}
        time.sleep(30)  # Update every 30 seconds

@app.route('/')
def home():
    return render_template("index.html", currencies=currency_data["currencies"], time=currency_data["time"])

@app.route('/data')
def data():
    return jsonify(currency_data)

if __name__ == '__main__':
    threading.Thread(target=update_currency_data, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)