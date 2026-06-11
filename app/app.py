"""
app.py — DeepOcean Nexus Flask Backend
=======================================

ROUTES:
  /                    → Serves the dashboard HTML page
  /api/map-data        → REAL DATA  : submarine cable routes + landing stations (from ArcGIS)
  /api/noc-status      → FAKE DATA  : simulated NOC telemetry (refreshed every call)
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
def noc_status():
    """
    Returns simulated NOC telemetry.
    Physical Environment, Security, DR, DevOps data is all randomly generated.
    """
    return jsonify(fake_telemetry.generate_noc_data())


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
def _find_free_port(start, attempts=20):
    """Return the first free TCP port starting from `start`."""
    for p in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', p))
                return p
            except OSError:
                continue
    return start   # Let Flask raise the error itself


if __name__ == '__main__':
    # ── Prometheus metrics server (port 8000) ──────────────────────────────────
    try:
        start_http_server(8000)
        print("[DeepOcean] ✅ Prometheus metrics  → http://0.0.0.0:8000")
    except OSError as e:
        print(f"[DeepOcean] ⚠️  Prometheus port 8000 busy, skipping ({e})")

    # ── Flask dashboard (default 5001 to avoid macOS AirPlay on 5000) ─────────
    # macOS Monterey+ binds AirPlay Receiver on port 5000.
    # We use 5001 by default and auto-increment if that's busy too.
    preferred = int(os.environ.get('PORT', 5000))
    port      = _find_free_port(preferred)
    if port != preferred:
        print(f"[DeepOcean] ⚠️  Port {preferred} busy — using {port} instead")

    print(f"[DeepOcean] 🚀 Dashboard          → http://127.0.0.1:{port}")
    print(f"[DeepOcean] 📡 Metrics (Flask)    → http://127.0.0.1:{port}/metrics")
    app.run(host='0.0.0.0', port=port, debug=False)

