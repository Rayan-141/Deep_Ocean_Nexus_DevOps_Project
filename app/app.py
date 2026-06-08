from flask import Flask, jsonify, render_template
import random, os
from datetime import datetime
from prometheus_client import start_http_server, Gauge

app = Flask(__name__)

status_gauge = Gauge('cable_status', 'Cable Health', ['cable_id'])
latency_gauge = Gauge('cable_latency_ms', 'Latency', ['cable_id'])

def generate_fake_data():
    data = {
        "cable_id": "Asia-Europe-Link-1",
        "overall_status": random.choice(["HEALTHY", "DEGRADED", "CRITICAL"]),
        "damage_percentage": round(random.uniform(0, 15), 2),
        "recovery_percentage": round(random.uniform(85, 100), 1),
        "fault_location_km": round(random.uniform(50, 4500), 1),
        "time_since_last_fault": f"{random.randint(0, 72)} hours",
        "estimated_repair_time": f"{random.randint(4, 48)} hours",
        "cable_temperature_c": round(random.uniform(4, 12), 1),
        "water_temperature_c": round(random.uniform(2, 15), 1),
        "pressure_bars": round(random.uniform(200, 500), 1),
        "depth_meters": random.randint(100, 5500),
        "ocean_current_speed_knots": round(random.uniform(0.5, 5.5), 1),
        "ocean_current_direction": random.choice(["NE", "SW", "E", "NW"]),
        "vibration_level": round(random.uniform(0.1, 4.5), 2),
        "seismic_activity": random.choice(["Low", "Moderate", "High"]),
        "salinity_ppt": round(random.uniform(34, 36), 2),
        "turbidity_ntu": round(random.uniform(0.1, 5), 2),
        "optical_signal_power_dbm": round(random.uniform(-25, -10), 2),
        "attenuation_db_per_km": round(random.uniform(0.15, 0.35), 3),
        "bit_error_rate": f"1e-{random.randint(8,12)}",
        "latency_ms": random.randint(12, 95),
        "bandwidth_utilization": round(random.uniform(45, 98), 1),
        "data_throughput_tbps": round(random.uniform(2.5, 12.8), 2),
        "packet_loss": round(random.uniform(0, 1.5), 3),
        "active_sensors": random.randint(850, 1200),
        "daily_events": random.randint(1200000, 8500000),
        "resilience_score": round(random.uniform(92, 99.8), 1),
        "cyber_threat_level": random.choice(["LOW", "MEDIUM", "HIGH"]),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    status_gauge.labels(data["cable_id"]).set(1 if data["overall_status"] == "HEALTHY" else 0.5)
    latency_gauge.labels(data["cable_id"]).set(data["latency_ms"])
    return data

@app.route('/')
def home():
    return render_template('index.html', data=generate_fake_data())

@app.route('/api/cable-status')
def cable_status():
    return jsonify(generate_fake_data())

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "DeepOcean Nexus"})

@app.route('/version')
def version():
    return jsonify({
        "version": "1.0.0",
        "project": "DeepOcean Nexus"
    })

if __name__ == "__main__":
    start_http_server(8000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

