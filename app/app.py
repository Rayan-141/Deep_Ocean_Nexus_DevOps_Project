"""
app.py — DeepOcean Nexus Flask Backend
=======================================

ROUTES:
  /                    → Serves the dashboard HTML page
  /api/map-data        → REAL DATA  : submarine cable routes + landing stations (from ArcGIS)
  /api/noc-status      → FAKE DATA  : simulated NOC telemetry (refreshed every call)
  /api/dashboard-summary → FAKE DATA : lightweight dashboard summary for polling
  /api/cable-status    → FAKE DATA  : same as noc-status (kept for backward compatibility)
  /health              → Health check (used by Kubernetes liveness probe)
  /version             → App version info
  /metrics             → Prometheus metrics endpoint (scraped by Prometheus/Grafana)

MODULES:
  arcgis_client    → Fetches REAL cable data from ArcGIS TeleGeography API
  fake_telemetry   → Generates FAKE NOC telemetry (physical env, security, DR, devops)
"""

from flask import Flask, jsonify, render_template, Response
import os
import socket
from prometheus_client import start_http_server, Counter, generate_latest

# Our custom modules
import arcgis_client   # Real data from ArcGIS
import fake_telemetry  # Fake NOC telemetry

app = Flask(__name__)

# ── Prometheus: count how many times the dashboard is requested ────────────────
REQUEST_COUNT = Counter('deepocean_requests_total', 'Total DeepOcean Requests')


# ── Dashboard page ─────────────────────────────────────────────────────────────
@app.route('/')
def home():
    REQUEST_COUNT.inc()
    return render_template('index.html')


# ── REAL DATA: Cable routes + landing stations from ArcGIS (TeleGeography) ────
@app.route('/api/map-data')
def map_data():
    """
    Returns REAL submarine cable routes and landing stations.
    Data comes from ArcGIS REST API (TeleGeography dataset).
    Cached for 1 hour in arcgis_client memory.
    """
    data = arcgis_client.fetch_map_data()
    return jsonify(data)


# ── FAKE DATA: NOC telemetry (simulated, refreshes every 3 seconds) ───────────
@app.route('/api/noc-status')
@app.route('/noc-status')
def noc_status():
    """
    Returns simulated NOC telemetry.
    Physical Environment, Security, DR, DevOps data is all randomly generated.
    """
    return jsonify(fake_telemetry.generate_noc_data())


# ── FAKE DATA: Lightweight dashboard summary for polling ────────────────────
@app.route('/api/dashboard-summary')
def dashboard_summary():
    """
    Returns only the fields required to refresh the dashboard summary and
    live alert preview. This avoids sending the full cables + alerts payload
    on every refresh.
    """
    data = fake_telemetry.generate_noc_data()
    return jsonify({
        'active_cables':   data['active_cables'],
        'active_sensors':  data['active_sensors'],
        'active_alerts':   data['active_alerts'],
        'security_score':  data['security_score'],
        'throughput_tbps': data['throughput_tbps'],
        'ocean_status':    data['ocean_status'],
        'healthy_cables':  data['healthy_cables'],
        'degraded_cables': data['degraded_cables'],
        'critical_cables': data['critical_cables'],
        'noc':             data['noc'],
        'alerts':          data['alerts'][:6],
    })


# ── REAL METADATA: Dynamic metadata lookup on click ──────────────────────────
@app.route('/api/cable-details')
def cable_details():
    """
    Returns real metadata details (length, owners, RFS year, route) for a cable.
    """
    from flask import request
    cable_id = request.args.get('id', '')
    cable_name = request.args.get('name', '')
    details = arcgis_client.fetch_cable_details(cable_id, cable_name)
    return jsonify(details)



# Keep old route so existing Kubernetes health probes don't break
@app.route('/api/cable-status')
def cable_status():
    return jsonify(fake_telemetry.generate_noc_data())


# ── Health check (Kubernetes liveness/readiness probe) ────────────────────────
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "DeepOcean Nexus"})


# ── Version ────────────────────────────────────────────────────────────────────
@app.route('/version')
def version():
    return jsonify({"version": "3.0.0", "project": "DeepOcean Nexus"})


# ── Prometheus metrics (scraped by Prometheus every 15s) ──────────────────────
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    start_http_server(8000)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

