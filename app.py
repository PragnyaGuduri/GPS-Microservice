from flask import Flask, jsonify, Response
import requests
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

REQUEST_COUNT = Counter('gps_request_total', 'Total requests', ['endpoint'])
REQUEST_LATENCY = Histogram('gps_request_latency_seconds', 'Request latency', ['endpoint'])

def get_location_from_ip():
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        if data["status"] == "success":
            return {
                "name": "Classroom (Auto-detected)",
                "latitude": data["lat"],
                "longitude": data["lon"],
                "city": data["city"],
                "region": data["regionName"],
                "country": data["country"],
                "source": "IP Geolocation"
            }
    except Exception:
        return None

@app.route("/", methods=["GET"])
def home():
    REQUEST_COUNT.labels(endpoint="/").inc()
    return jsonify({"message": "GPS Microservice is running", "status": "healthy"})

@app.route("/location", methods=["GET"])
def get_location():
    REQUEST_COUNT.labels(endpoint="/location").inc()
    start = time.time()

    location = get_location_from_ip()

    REQUEST_LATENCY.labels(endpoint="/location").observe(time.time() - start)

    if location:
        return jsonify({
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "location": location
        })

    return jsonify({"status": "error", "message": "Could not fetch location"}), 500

@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)