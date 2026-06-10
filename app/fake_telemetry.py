"""
fake_telemetry.py
-----------------
PURPOSE : Generate simulated (fake) NOC telemetry data for the dashboard.

WHY FAKE? : Real submarine cable operators never expose live data such as
            current throughput, packet loss, threat levels, or sensor readings.
            This is kept private. So we simulate what a real NOC would monitor.

WHAT IS FAKE HERE :
  - Physical Environment  (water temp, pressure, depth, wave height, etc.)
  - Network Operations    (throughput, latency, packet loss, bandwidth, jitter)
  - Security Center       (threat level, DDoS risk, intrusion alerts)
  - Disaster Recovery     (RTO, RPO, failover status)
  - DevOps Infrastructure (Docker, Jenkins, Kubernetes health)

CABLE NAMES are REAL. Status/metrics are SIMULATED.
"""

import random
from datetime import datetime, timezone
from prometheus_client import Gauge

# Use real station data as our active sensor count.
import arcgis_client

# ── Prometheus Gauges ──────────────────────────────────────────────────────────
ACTIVE_CABLES   = Gauge('deepocean_active_cables',   'Number of active cables')
THROUGHPUT_TBPS = Gauge('deepocean_throughput_tbps', 'Global throughput in Tbps')
LATENCY_MS      = Gauge('deepocean_latency_ms',      'Average global latency in ms')
PACKET_LOSS     = Gauge('deepocean_packet_loss_pct', 'Global packet loss percentage')
SECURITY_SCORE  = Gauge('deepocean_security_score',  'Security score percentage')

# ── REAL cable names, routes, owners, lengths — FAKE status/metrics ────────────
# 30 cables: 10 Indian-operated + 20 global majors
CABLE_FLEET = [
    # ── Indian Cables ─────────────────────────────────────────────────────────
    # Reliance Jio
    {"id": "india-europe-express-iex",   "name": "IEX (Reliance Jio)",      "route": "Mumbai ↔ Marseille",         "length_km": 9775,   "owner": "Reliance Jio Platforms"},
    {"id": "flag-europe-asia",           "name": "FLAG Europe Asia (GCX)",  "route": "London ↔ Tokyo",             "length_km": 28000,  "owner": "GCX — Reliance Globalcom"},
    {"id": "jio-gcs",                    "name": "Jio GCS",                 "route": "Mumbai ↔ Singapore",         "length_km": 5500,   "owner": "Reliance Jio Infocomm"},

    # Tata Communications
    {"id": "seacomtata-tgn-eurasia",     "name": "Tata TGN-Eurasia",        "route": "London ↔ Singapore",         "length_km": 15000,  "owner": "Tata Communications"},
    {"id": "tata-tgn-atlantic",          "name": "Tata TGN-Atlantic",       "route": "New York ↔ London",          "length_km": 6000,   "owner": "Tata Communications"},
    {"id": "tata-tgn-pacific",           "name": "Tata TGN-Pacific",        "route": "San Jose ↔ Tokyo",           "length_km": 8650,   "owner": "Tata Communications"},
    {"id": "tata-tgn-gulf",              "name": "Tata TGN-Gulf",           "route": "Mumbai ↔ Fujairah (UAE)",    "length_km": 2000,   "owner": "Tata Communications"},
    {"id": "i2i",                        "name": "Tata i2i",                "route": "Chennai ↔ Singapore",        "length_km": 3100,   "owner": "Tata Communications + SingTel"},

    # Bharti Airtel
    {"id": "india-middle-east-western-europe-imewe", "name": "IMEWE (Airtel)", "route": "Mumbai ↔ Marseille", "length_km": 12091,  "owner": "Airtel, Tata, STC, France Telecom"},
    {"id": "bay-of-bengal-gateway-bobg", "name": "Bay of Bengal Gateway",   "route": "Chennai ↔ Singapore",        "length_km": 10900,  "owner": "Bharti Airtel, Tata, SingTel"},

    # BSNL / Government of India
    {"id": "chennai-andaman-nicobar-island-cani-cable", "name": "CANI (BSNL)", "route": "Chennai ↔ Port Blair", "length_km": 2313,   "owner": "BSNL — Bharat Sanchar Nigam Ltd"},
    {"id": "bharat-lanka-cable-system-blcs", "name": "Bharat Lanka (BLCS)", "route": "Tuticorin ↔ Colombo",       "length_km": 450,    "owner": "BSNL + Sri Lanka Telecom"},

    # ── Global Cables ─────────────────────────────────────────────────────────
    # Europe — Asia
    {"id": "sea-me-we-3",                "name": "SEA-ME-WE 3 (SMW-3)",    "route": "Okinawa ↔ Norden (Germany)", "length_km": 39000,  "owner": "Consortium (VSNL, France Telecom)"},
    {"id": "sea-me-we-4",                "name": "SEA-ME-WE 4 (SMW-4)",    "route": "Singapore ↔ Marseille",      "length_km": 18800,  "owner": "Consortium (SingTel, FT, Tata)"},
    {"id": "sea-me-we-5",                "name": "SEA-ME-WE 5",            "route": "Singapore ↔ Marseille",      "length_km": 20000,  "owner": "Consortium (Orange, SingTel, Tata)"},
    {"id": "sea-me-we-6",                "name": "SEA-ME-WE 6",            "route": "Singapore ↔ France",         "length_km": 19200,  "owner": "Consortium (SingTel, China Mobile)"},
    {"id": "asia-africa-europe-1-aae-1", "name": "AAE-1",                   "route": "Hong Kong ↔ Marseille",      "length_km": 25000,  "owner": "Consortium (du, Ooredoo, STC, Tata)"},

    # Trans-Atlantic
    {"id": "marea",                      "name": "MAREA",                   "route": "Virginia Beach ↔ Bilbao",    "length_km": 6600,   "owner": "Microsoft + Meta (Facebook)"},
    {"id": "dunant",                     "name": "Dunant",                  "route": "Virginia Beach ↔ France",    "length_km": 6600,   "owner": "Google"},

    # Trans-Pacific
    {"id": "faster",                     "name": "FASTER",                  "route": "Tokyo ↔ Los Angeles",        "length_km": 9000,   "owner": "Google, KDDI, China Mobile"},
    {"id": "jupiter",                    "name": "JUPITER",                 "route": "Los Angeles ↔ Tokyo",        "length_km": 14500,  "owner": "Google, Meta, SoftBank, Amazon"},
    {"id": "south-east-asia-japan-cable-sjc", "name": "SJC",                "route": "Tokyo ↔ Singapore",          "length_km": 8900,   "owner": "Google, Bharti Airtel, KDDI"},

    # Africa
    {"id": "2africa",                    "name": "2Africa",                 "route": "UK ↔ Cape Town (via Africa)", "length_km": 45000, "owner": "Meta, MTN, Orange (21-member)"},
    {"id": "equiano",                    "name": "Equiano",                 "route": "Lisbon ↔ Cape Town",         "length_km": 15000,  "owner": "Google"},
    {"id": "seacomtata-tgn-eurasia",     "name": "SEACOM",                  "route": "Cape Town ↔ Mumbai",         "length_km": 17000,  "owner": "SEACOM Ltd (Africa)"},
    {"id": "eastern-africa-submarine-cable-system-eassy", "name": "EASSy",  "route": "Cape Town ↔ Port Sudan",     "length_km": 10500,  "owner": "Consortium (Airtel, MTN, Vodacom)"},
    {"id": "africa-coast-to-europe-ace", "name": "ACE",                     "route": "France ↔ Cape Town",         "length_km": 17000,  "owner": "Orange (lead), Senegal, Maroc"},
    {"id": "south-africa-far-east-safe", "name": "SAFE",                    "route": "Cape Town ↔ Penang",         "length_km": 13000,  "owner": "Tata Communications, Airtel"},

    # Middle East / China
    {"id": "peace-cable",                "name": "PEACE Cable",             "route": "Karachi ↔ Marseille",        "length_km": 15000,  "owner": "PEACE Cable International"},

    # Pacific Islands
    {"id": "southern-cross-next",        "name": "Southern Cross NEXT",     "route": "Sydney ↔ Los Angeles",       "length_km": 13700,  "owner": "Telstra, Singtel, Optus"},
]

# Weighted random — mostly healthy
STATUSES = ["HEALTHY", "HEALTHY", "HEALTHY", "HEALTHY", "DEGRADED", "DEGRADED", "CRITICAL"]

def get_all_cables():
    """
    Combine our priority CABLE_FLEET list with the rest of the 400+ cables 
    loaded from arcgis_client (if the map data cache is populated).
    """
    cables = list(CABLE_FLEET)
    
    # Check if map data is already fetched and cached
    if arcgis_client._cache["data"]:
        try:
            map_cables = arcgis_client._cache["data"].get("cables", [])
            existing_names = {c["name"].lower() for c in cables}
            for mc in map_cables:
                name = mc.get("name")
                cid = mc.get("id")
                if name and name.lower() not in existing_names:
                    cables.append({
                        "id": cid,
                        "name": name,
                        "route": mc.get("route", "Global Submarine Cable Route"),
                        "length_km": mc.get("length", "N/A"),
                        "owner": mc.get("owners", "Consortium"),
                    })
        except Exception as e:
            print(f"Error merging map cables: {e}")
            
    return cables


def generate_noc_data():
    """
    Generate a complete fake NOC snapshot.
    Called by /api/noc-status every 3 seconds.
    """
    all_cables_list = get_all_cables()
    cables = []
    
    for c in all_cables_list:
        status = random.choice(STATUSES)
        
        # Telemetry metrics specific to this cable
        latency = random.randint(18, 130)
        pkt_loss = round(random.uniform(0, 2.5), 3)
        bw_pct = round(random.uniform(40, 99), 1)
        throughput = round(random.uniform(2.0, 12.0), 1)
        avail = round(random.uniform(85.0, 99.0), 4)
        jitter = round(random.uniform(0.5, 5.0), 1)
        
        # Physical Environment
        temp = round(random.uniform(2.0, 15.0), 1)
        pressure = round(random.uniform(200.0, 500.0), 1)
        depth = random.randint(500, 5500)
        wave_height = round(random.uniform(0.3, 6.0), 1)
        signal_power = round(random.uniform(-22.0, -10.0), 1)
        seabed = random.choice(['Stable', 'Stable', 'Stable', 'Minor Movement'])
        
        # Security Center
        threat = random.choice(["LOW", "LOW", "LOW", "MEDIUM", "HIGH"])
        ddos = "LOW" if threat == "LOW" else "MEDIUM"
        intrusion = random.randint(0, 4)
        sec_score = round(random.uniform(85.0, 99.0), 1)
        
        # Disaster Recovery
        rto = random.randint(10, 20)
        rpo = random.randint(1, 5)
        readiness = round(random.uniform(85.0, 99.0), 1)
        
        cables.append({
            "id":              c.get("id", ""),
            "name":            c["name"],
            "route":           c["route"],
            "length_km":       c["length_km"],
            "owner":           c.get("owner", "Consortium"),
            "status":          status,
            "latency_ms":      latency,
            "packet_loss_pct": pkt_loss,
            "bandwidth_pct":   bw_pct,
            "throughput_tbps": throughput,
            "avail_pct":       avail,
            "jitter_ms":       jitter,
            "water_temp_c":    temp,
            "pressure_bars":   pressure,
            "depth_m":         depth,
            "wave_height_m":   wave_height,
            "signal_power_dbm": signal_power,
            "seabed_stability": seabed,
            "threat_level":    threat,
            "ddos_risk":       ddos,
            "intrusion_alerts": intrusion,
            "security_score":  sec_score,
            "rto_mins":        rto,
            "rpo_mins":        rpo,
            "readiness_pct":   readiness,
        })

    healthy  = sum(1 for c in cables if c["status"] == "HEALTHY")
    degraded = sum(1 for c in cables if c["status"] == "DEGRADED")
    critical = sum(1 for c in cables if c["status"] == "CRITICAL")

    throughput   = round(random.uniform(14.0, 22.0), 1)
    avg_latency  = round(random.uniform(40, 75), 1)
    avg_pkt_loss = round(random.uniform(0.1, 0.8), 3)
    security_sc  = round(random.uniform(85.0, 99.0), 1)
    threat_level = random.choice(["LOW", "LOW", "LOW", "MEDIUM", "HIGH"])

    ACTIVE_CABLES.set(len(cables))
    THROUGHPUT_TBPS.set(throughput)
    LATENCY_MS.set(avg_latency)
    PACKET_LOSS.set(avg_pkt_loss)
    SECURITY_SCORE.set(security_sc)

    alerts = []
    for c in cables:
        if c["status"] == "CRITICAL":
            alerts.append({"cable": c["name"], "msg": random.choice([
                "Critical fault — rerouting traffic",
                "Fiber cut detected — emergency repair initiated",
                "Cable rupture — immediate failover active",
                "Severe signal loss — backup route activated",
                "System outage — disaster recovery engaged",
            ])})
        elif c["status"] == "DEGRADED":
            alerts.append({"cable": c["name"], "msg": random.choice([
                "Packet Loss > 2%",
                "High Latency detected",
                "Signal degradation on segment",
                "Maintenance window scheduled",
            ])})
    if not alerts:
        alerts.append({"cable": "SEA-ME-WE 5", "msg": "Scheduled maintenance — 02:00 UTC"})

    station_count = len(arcgis_client.fetch_map_data().get("stations", []))

    return {
        "active_cables":   len(cables),
        "active_sensors":  station_count,
        "active_alerts":   len(alerts),
        "security_score":  security_sc,
        "throughput_tbps": throughput,
        "ocean_status":    random.choice(["Normal", "Normal", "Normal", "Advisory"]),
        "healthy_cables":  healthy,
        "degraded_cables": degraded,
        "critical_cables": critical,
        "cables": cables,
        "noc": {
            "throughput_tbps":    throughput,
            "latency_ms":         avg_latency,
            "packet_loss_pct":    avg_pkt_loss,
            "availability_pct":   round(random.uniform(85.0, 99.0), 4),
            "active_connections": f"{random.randint(28, 52)}M",
            "jitter_ms":          round(random.uniform(0.5, 4.5), 1),
            "bandwidth_util_pct": round(random.uniform(62, 89), 1),
            "dns_resolve_ms":     round(random.uniform(1.2, 8.5), 1),
        },
        "env": {
            "water_temp_c":        round(random.uniform(2, 15), 1),
            "pressure_bars":       round(random.uniform(200, 500), 1),
            "depth_m":             random.randint(500, 5500),
            "current_speed_knots": round(random.uniform(0.5, 5.5), 1),
            "current_direction":   random.choice(["NE", "SW", "E", "NW", "SE"]),
            "wave_height_m":       round(random.uniform(0.3, 6.0), 1),
            "seabed_stability":    random.choice(["Stable", "Stable", "Stable", "Minor Movement"]),
            "signal_power_dbm":    round(random.uniform(-22, -10), 2),
            "attenuation_db_km":   round(random.uniform(0.15, 0.35), 3),
            "bit_error_rate":      f"1e-{random.randint(9, 12)}",
            "maintenance_status":  random.choice(["Operational", "Operational", "Scheduled"]),
            "backup_route":        random.choice(["Available", "Available", "Standby"]),
            "repair_team":         random.choice(["On Standby", "Deployed", "On Standby"]),
        },
        "security": {
            "threat_level":          threat_level,
            "firewall_status":       "ACTIVE",
            "ddos_risk":             "LOW" if threat_level == "LOW" else "MEDIUM",
            "intrusion_alerts":      random.randint(0, 4),
            "unauthorized_attempts": random.randint(0, 12),
            "security_score":        security_sc,
        },
        "dr": {
            "backup_route":    "AVAILABLE",
            "failover_status": "READY",
            "rto_mins":        random.randint(10, 20),
            "rpo_mins":        random.randint(1, 5),
            "replication":     "ACTIVE",
            "readiness_pct":   round(random.uniform(85.0, 99.0), 1),
        },
        "devops": {
            "docker":     "Healthy",
            "jenkins":    "Healthy",
            "kubernetes": "Healthy",
            "hpa":        "Active",
            "prometheus": "Scraping",
            "grafana":    "Online",
            "fluent_bit": "Running",
            "terraform":  "Provisioned",
        },
        "alerts":    alerts[:6],
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
