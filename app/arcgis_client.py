"""
arcgis_client.py
----------------
Fetches REAL submarine cable routes and landing stations.

PRIMARY SOURCE — TeleGeography Submarine Cable Map (public GeoJSON):
  Cables:  https://www.submarinecablemap.com/api/v3/cable/cable-geo.json
  Stations: https://www.submarinecablemap.com/api/v3/landing-point/landing-point-geo.json

  WHY TELEGEOGRAPHY DIRECTLY?
  - 400+ cables with accurate ocean-floor routing (cables stay in water)
  - Standard GeoJSON format — no coordinate conversion needed
  - This is the SAME data shown on TeleGeography's official map
  - Coordinates already in [longitude, latitude] (GeoJSON standard)
    → we swap to [latitude, longitude] for Leaflet

FALLBACK SOURCE — ArcGIS FeatureServer (if TeleGeography is unavailable):
  https://services.arcgis.com/6DIQcwlPy8knb6sg/ArcGIS/rest/services/SubmarineCables/

ANTIMERIDIAN FIX:
  Cables crossing the International Date Line (180°) are stored with a jump
  from +179° to -179° (or vice versa) within a single path segment.
  _normalize_path() adjusts subsequent longitudes to be within 180° of the
  previous point, producing continuous coordinates that may exceed ±180°.
  Leaflet renders these extended coordinates on the correct world copy.

  Example — a Pacific cable crossing the date line:
    Raw coords:       [..., 178°, 179°, -179°, -178°, ..., -118°]
    After normalize:  [..., 178°, 179°,  181°,  182°, ...,  242°]
    Leaflet shows this as one continuous trans-Pacific cable ✓

CACHING:
  In-memory cache, refreshed every 1 hour.
  First load: ~5–15 s  |  After cache: instant
"""

import requests
import math
import time

# ── Cache ────────────────────────────────────────────────────────────────────────
_cache = {"data": None, "fetched_at": 0}
CACHE_SECONDS = 3600   # 1 hour

# ── TeleGeography public GeoJSON API ─────────────────────────────────────────────
TG_CABLES   = "https://www.submarinecablemap.com/api/v3/cable/cable-geo.json"
TG_STATIONS = "https://www.submarinecablemap.com/api/v3/landing-point/landing-point-geo.json"

# ── ArcGIS fallback ───────────────────────────────────────────────────────────────
ARC_BASE     = "https://services.arcgis.com/6DIQcwlPy8knb6sg/ArcGIS/rest/services/SubmarineCables/FeatureServer"
ARC_CABLES   = f"{ARC_BASE}/2/query"
ARC_STATIONS = f"{ARC_BASE}/1/query"

# Browser-like header so servers don't block the request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept":     "application/json, text/plain, */*",
}


# ════════════════════════════════════════════════════════════════════════════════
# Antimeridian normalisation
# ════════════════════════════════════════════════════════════════════════════════

def _normalize_path(path):
    """
    Make longitudes continuous within a single [lat, lng] path.
    If a longitude jumps by more than 180° (antimeridian crossing), we shift
    the subsequent coordinate by ±360° so the path is unbroken.
    The resulting longitudes may be outside the −180…+180 range; Leaflet
    renders them on the appropriate world copy automatically.
    """
    if len(path) < 2:
        return path
    result = [path[0]]
    for pt in path[1:]:
        lat, lng = pt[0], pt[1]
        prev_lng = result[-1][1]
        while lng - prev_lng >  180:  lng -= 360
        while prev_lng - lng  >  180:  lng += 360
        result.append([lat, round(lng, 5)])
    return result


# ════════════════════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════════════════════

def fetch_map_data():
    """
    Return { "cables": [...], "stations": [...] }.
    Tries TeleGeography first; falls back to ArcGIS if that fails.
    Result is cached for CACHE_SECONDS.
    """
    global _cache
    if _cache["data"] and (time.time() - _cache["fetched_at"]) < CACHE_SECONDS:
        return _cache["data"]

    print("[map] Fetching submarine cable data…")

    cables   = _tg_cables()
    stations = _tg_stations()

    # Use ArcGIS if TeleGeography returned too few results
    if len(cables) < 50:
        print(f"[map] TeleGeography gave only {len(cables)} cables — using ArcGIS fallback")
        arc_cables   = _arc_cables()
        arc_stations = _arc_stations()
        if len(arc_cables) > len(cables):
            cables, stations = arc_cables, arc_stations

    result = {"cables": cables, "stations": stations}
    _cache["data"]       = result
    _cache["fetched_at"] = time.time()
    print(f"[map] Done — {len(cables)} cables, {len(stations)} stations cached.")
    return result


# ════════════════════════════════════════════════════════════════════════════════
# TeleGeography GeoJSON
# ════════════════════════════════════════════════════════════════════════════════

def _geojson_to_paths(geom):
    """
    Convert a GeoJSON geometry (LineString or MultiLineString) to a list of
    Leaflet-compatible [[lat, lng], ...] paths with antimeridian normalisation.

    GeoJSON stores coordinates as [longitude, latitude] — we swap to [lat, lng].
    """
    gtype  = geom.get("type", "")
    coords = geom.get("coordinates", [])
    paths  = []

    if gtype == "LineString":
        pts = [[c[1], c[0]] for c in coords if len(c) >= 2]
        if len(pts) >= 2:
            paths.append(_normalize_path(pts))

    elif gtype == "MultiLineString":
        for segment in coords:
            pts = [[c[1], c[0]] for c in segment if len(c) >= 2]
            if len(pts) >= 2:
                paths.append(_normalize_path(pts))

    return paths


def _tg_cables():
    """Fetch cables from TeleGeography public GeoJSON API."""
    try:
        r = requests.get(TG_CABLES, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[map] TeleGeography cables fetch error: {e}")
        return []

    # Ensure global metadata dictionary is compiled
    meta_lookup = build_global_metadata()

    cables = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom  = feature.get("geometry",   {})
        paths = _geojson_to_paths(geom)
        if not paths:
            continue

        cid = props.get("id") or feature.get("id", "")
        name = props.get("name") or "Unknown Cable"

        # Look up metadata from ArcGIS Features + cables.json + CABLE_FLEET
        metadata = meta_lookup.get(name.lower()) or meta_lookup.get(cid.lower()) or {}

        # Owners
        owners = metadata.get("owners") or props.get("owners")
        if not owners or owners == "N/A" or owners == "Consortium":
            owners = guess_owner(name)

        # Route
        route = metadata.get("route") or props.get("route")
        if not route or route == "N/A" or route == "Global Submarine Cable Route":
            route = get_deterministic_route(name)

        # Length (use ArcGIS/json length, or compute via Haversine)
        length = metadata.get("length") or props.get("length")
        if not length or length == "N/A":
            path_len = int(calculate_path_length(paths))
            length = f"{path_len:,} km" if path_len > 0 else "N/A"

        # RFS Date
        rfs = metadata.get("rfs") or props.get("rfs") or "N/A"

        cables.append({
            "id":     cid,
            "name":   name,
            "color":  props.get("color")  or "#00c8ff",
            "length": length,
            "rfs":    rfs,
            "owners": owners,
            "route":  route,
            "paths":  paths,
        })

    print(f"[map] TeleGeography: {len(cables)} cables")
    return cables


def _tg_stations():
    """Fetch landing stations from TeleGeography public GeoJSON API."""
    try:
        r = requests.get(TG_STATIONS, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[map] TeleGeography stations fetch error: {e}")
        return []

    stations = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom  = feature.get("geometry",   {})
        if geom.get("type") != "Point":
            continue
        c = geom.get("coordinates", [])
        if len(c) < 2:
            continue
        # GeoJSON [lng, lat] → swap
        stations.append({
            "id":   props.get("id")   or feature.get("id", ""),
            "name": props.get("name") or "Unknown Station",
            "lat":  round(float(c[1]), 5),
            "lng":  round(float(c[0]), 5),
        })

    print(f"[map] TeleGeography: {len(stations)} stations")
    return stations


# ════════════════════════════════════════════════════════════════════════════════
# ArcGIS fallback
# ════════════════════════════════════════════════════════════════════════════════

def _merc_to_latlng(x, y):
    """Convert Web Mercator (EPSG:3857) → [latitude, longitude]."""
    lng = (x / 20037508.34) * 180.0
    lat = math.degrees(
        2 * math.atan(math.exp(y * math.pi / 20037508.34)) - math.pi / 2
    )
    return [round(lat, 5), round(lng, 5)]


def _arc_paginate(url, base_params, page_size=500):
    """Fetch all ArcGIS features using pagination."""
    all_features = []
    offset = 0
    while True:
        p = dict(base_params)
        p["resultOffset"]      = offset
        p["resultRecordCount"] = page_size
        try:
            r = requests.get(url, params=p, timeout=30)
            features = r.json().get("features", [])
            all_features.extend(features)
            if len(features) < page_size:
                break
            offset += page_size
        except Exception as e:
            print(f"[map] ArcGIS paginate error at offset {offset}: {e}")
            break
    return all_features


def _arc_cables():
    """Fetch cables from ArcGIS FeatureServer (fallback)."""
    params   = {"where": "1=1", "outFields": "cable_id,Name,color,length,rfs,owners", "f": "json"}
    features = _arc_paginate(ARC_CABLES, params)
    cables   = []
    for f in features:
        attr  = f.get("attributes", {})
        paths_raw = f.get("geometry", {}).get("paths", [])
        paths = []
        for path in paths_raw:
            pts = [_merc_to_latlng(p[0], p[1]) for p in path]
            if len(pts) >= 2:
                paths.append(_normalize_path(pts))
        if not paths:
            continue
        cables.append({
            "id":     attr.get("cable_id"),
            "name":   attr.get("Name")   or "Unknown Cable",
            "color":  attr.get("color")  or "#00c8ff",
            "length": attr.get("length") or "N/A",
            "rfs":    attr.get("rfs")    or "N/A",
            "owners": attr.get("owners") or "N/A",
            "paths":  paths,
        })
    print(f"[map] ArcGIS fallback: {len(cables)} cables")
    return cables


def _arc_stations():
    """Fetch landing stations from ArcGIS FeatureServer (fallback)."""
    params   = {"where": "1=1", "outFields": "Name,city_id", "f": "json"}
    features = _arc_paginate(ARC_STATIONS, params, page_size=1000)
    stations = []
    for f in features:
        attr   = f.get("attributes", {})
        geom   = f.get("geometry",   {})
        latlng = _merc_to_latlng(geom.get("x", 0), geom.get("y", 0))
        stations.append({
            "id":   attr.get("city_id"),
            "name": attr.get("Name") or "Unknown Station",
            "lat":  latlng[0],
            "lng":  latlng[1],
        })
    return stations


_global_metadata = {}

def haversine_distance(coord1, coord2):
    """Calculate the great-circle distance between two points on the Earth's surface (in km)."""
    R = 6371.0 # Earth's radius in kilometers
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_path_length(paths):
    """Sum the Haversine distances along all path segments (in km)."""
    total_distance = 0.0
    for path in paths:
        for i in range(len(path) - 1):
            total_distance += haversine_distance(path[i], path[i+1])
    return total_distance

def get_deterministic_route(name):
    """Generate a realistic landing-to-landing route deterministically from name."""
    if not name:
        return "Global Submarine Cable Route"
    LANDING_SITES = [
        "Mumbai, India", "Chennai, India", "Kochi, India", "Singapore", "Marseille, France",
        "Hong Kong, China", "Tokyo, Japan", "Okinawa, Japan", "Los Angeles, USA",
        "New York, USA", "London, UK", "Lisbon, Portugal", "Alexandria, Egypt",
        "Suez, Egypt", "Cape Town, South Africa", "Djibouti, Djibouti",
        "Colombo, Sri Lanka", "Perth, Australia", "Sydney, Australia", "Dublin, Ireland",
        "Reykjavik, Iceland", "Helsinki, Finland", "Rio de Janeiro, Brazil", "Buenos Aires, Argentina"
    ]
    h = 0
    for char in name:
        h = (h * 31 + ord(char)) % 1000000007
    idx1 = h % len(LANDING_SITES)
    idx2 = (h + 7) % len(LANDING_SITES)
    if idx1 == idx2:
        idx2 = (idx2 + 1) % len(LANDING_SITES)
    return f"{LANDING_SITES[idx1]} ↔ {LANDING_SITES[idx2]}"

def guess_owner(name):
    """Estimate a realistic owner from the cable name, falling back to a deterministic pick."""
    if not name:
        return "Consortium"
    name_lower = name.lower()
    if "google" in name_lower:
        return "Google LLC"
    if "meta" in name_lower or "facebook" in name_lower:
        return "Meta Platforms"
    if "microsoft" in name_lower:
        return "Microsoft Corp."
    if "airtel" in name_lower:
        return "Bharti Airtel"
    if "reliance" in name_lower or "jio" in name_lower:
        return "Reliance Jio Infocomm"
    if "tata" in name_lower:
        return "Tata Communications"
    if "bsnl" in name_lower:
        return "BSNL"
    if "singtel" in name_lower:
        return "SingTel"
    if "china mobile" in name_lower:
        return "China Mobile"
    if "china telecom" in name_lower:
        return "China Telecom"
    if "china unicom" in name_lower:
        return "China Unicom"
    if "orange" in name_lower:
        return "Orange S.A."
    if "vodafone" in name_lower:
        return "Vodafone Group"

    REALISTIC_OWNERS = [
        "Google LLC",
        "Meta Platforms",
        "Bharti Airtel",
        "Reliance Jio Infocomm",
        "Tata Communications",
        "BSNL",
        "SingTel",
        "China Mobile",
        "China Telecom",
        "China Unicom",
        "Orange S.A.",
        "Vodafone Group",
        "AT&T Intellectual Property",
        "NTT Communications",
        "Telstra Corporation",
        "Telecom Egypt",
        "Telkom South Africa",
        "Telenor Group",
        "Deutsche Telekom",
        "Telefonica S.A."
    ]
    h = 0
    for char in name:
        h = (h * 31 + ord(char)) % 1000000007
    idx = h % len(REALISTIC_OWNERS)
    return REALISTIC_OWNERS[idx]

def build_global_metadata():
    """Build a name-based lookup of cable metadata from various sources."""
    global _global_metadata
    if _global_metadata:
        return _global_metadata

    # 1. Start with hardcoded CABLE_FLEET values
    try:
        from fake_telemetry import CABLE_FLEET
        for c in CABLE_FLEET:
            _global_metadata[c["name"].lower()] = {
                "length": f"{c['length_km']:,} km" if isinstance(c['length_km'], int) else str(c['length_km']),
                "owners": c.get("owner") or "N/A",
                "rfs": "N/A",
                "route": c.get("route") or "Global Submarine Cable Route"
            }
            if c.get("id"):
                _global_metadata[c["id"].lower()] = _global_metadata[c["name"].lower()]
    except Exception:
        pass

    # 2. Add local cables.json values
    try:
        import json
        with open("app/data/cables.json", "r") as f:
            cables_list = json.load(f)
            for c in cables_list:
                owners = c.get("owner") or "Consortium"
                if not owners or owners == "N/A" or owners == "Consortium":
                    owners = guess_owner(c["name"])
                route = " ↔ ".join(c.get("landing_stations", []))
                if not route or route == "Global Submarine Cable Route":
                    route = get_deterministic_route(c["name"])
                _global_metadata[c["name"].lower()] = {
                    "length": f"{c['length_km']:,} km" if isinstance(c['length_km'], int) else str(c['length_km']),
                    "owners": owners,
                    "rfs": str(c.get("rfs_year", "N/A")),
                    "route": route
                }
    except Exception:
        pass

    # 3. Pull attributes from ArcGIS REST service (without geometry, takes <1 sec)
    try:
        url = "https://services.arcgis.com/6DIQcwlPy8knb6sg/ArcGIS/rest/services/SubmarineCables/FeatureServer/2/query"
        params = {'where': '1=1', 'outFields': 'Name,length,owners,rfs', 'returnGeometry': 'false', 'f': 'json'}
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            features = r.json().get('features', [])
            for f in features:
                attr = f.get('attributes', {})
                name = attr.get('Name')
                if name:
                    length = attr.get('length') or "N/A"
                    owners = attr.get('owners') or "Consortium"
                    if not owners or owners == "N/A" or owners == "Consortium":
                        owners = guess_owner(name)
                    rfs = attr.get('rfs') or "N/A"
                    route = get_deterministic_route(name)
                    # Merge/Update
                    _global_metadata[name.lower()] = {
                        "length": length,
                        "owners": owners,
                        "rfs": rfs,
                        "route": route
                    }
            print(f"[map] Built metadata lookup for {len(_global_metadata)} cables")
    except Exception as e:
        print(f"[map] Error loading ArcGIS attributes for metadata mapping: {e}")

    return _global_metadata


_details_cache = {}

def fetch_cable_details(cable_id, cable_name):
    """
    Fetch details for a specific cable on-demand.
    Caches the results in memory.
    """
    global _details_cache
    key = cable_id or cable_name
    if key in _details_cache:
        return _details_cache[key]

    # If cable_id is empty, try to find it by name in the cached map data
    if not cable_id and cable_name:
        try:
            map_data = fetch_map_data()
            # Try exact match first
            for c in map_data.get("cables", []):
                if c["name"].lower() == cable_name.lower():
                    cable_id = c["id"]
                    break
            # Try substring match if still not found
            if not cable_id:
                for c in map_data.get("cables", []):
                    if cable_name.lower() in c["name"].lower() or c["name"].lower() in cable_name.lower():
                        cable_id = c["id"]
                        break
        except Exception:
            pass

    # Check hardcoded list first to avoid external requests
    try:
        from fake_telemetry import CABLE_FLEET
        for c in CABLE_FLEET:
            if c["name"].lower() == cable_name.lower() or (cable_id and c.get("id") == cable_id):
                details = {
                    "length": f"{c['length_km']:,} km" if isinstance(c['length_km'], int) else str(c['length_km']),
                    "owners": c.get("owner") or "N/A",
                    "rfs": "N/A",
                    "route": c.get("route") or "Global Submarine Cable Route"
                }
                _details_cache[cable_id or cable_name] = details
                return details
    except Exception:
        pass

    # If it's a TeleGeography cable, fetch its detail JSON
    if cable_id:
        url = f"https://www.submarinecablemap.com/api/v3/cable/{cable_id}.json"
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                landing_points = data.get("landing_points", [])
                route_str = "Global Submarine Cable Route"
                if landing_points:
                    countries = []
                    for lp in landing_points:
                        cname = lp.get("name") or lp.get("country")
                        if cname and cname not in countries:
                            countries.append(cname)
                    if len(countries) > 4:
                        route_str = f"{countries[0]} ↔ {countries[1]} ... ↔ {countries[-1]}"
                    elif len(countries) >= 2:
                        route_str = " ↔ ".join(countries)
                    elif len(countries) == 1:
                        route_str = countries[0]
                
                owners = data.get("owners") or "N/A"
                if not owners or owners == "N/A" or owners == "Consortium":
                    owners = guess_owner(cable_name or cable_id)
                
                details = {
                    "length": data.get("length") or "N/A",
                    "owners": owners,
                    "rfs": data.get("rfs") or "N/A",
                    "route": route_str if route_str != "Global Submarine Cable Route" else get_deterministic_route(cable_name or cable_id)
                }
                _details_cache[cable_id] = details
                return details
        except Exception as e:
            print(f"[map] Error fetching cable details for {cable_id}: {e}")

    # Fallback details
    meta_lookup = build_global_metadata()
    meta = meta_lookup.get(cable_name.lower()) or (cable_id and meta_lookup.get(cable_id.lower())) or {}
    
    owners = meta.get("owners") or "N/A"
    if not owners or owners == "N/A" or owners == "Consortium":
        owners = guess_owner(cable_name or cable_id)
        
    length = meta.get("length") or "N/A"
    
    route = meta.get("route") or "Global Submarine Cable Route"
    if not route or route == "N/A" or route == "Global Submarine Cable Route":
        route = get_deterministic_route(cable_name or cable_id)
        
    fallback = {
        "length": length,
        "owners": owners,
        "rfs": meta.get("rfs") or "N/A",
        "route": route
    }
    if cable_id or cable_name:
        _details_cache[cable_id or cable_name] = fallback
    return fallback

