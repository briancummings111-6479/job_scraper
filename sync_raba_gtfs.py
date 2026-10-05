"""
sync_raba_gtfs.py

Synchronizes and extracts the latest General Transit Feed Specification (GTFS)
from the Redding Area Bus Authority (RABA):
https://gtfs.remix.com/redding_area_bus_authority.zip

Compiles:
- 12 RABA routes with colors, PDF schedule URLs, and stops
- 270 physical stops with lat/long and servicing routes
- Weekday/Saturday/Sunday service hour envelopes

Outputs:
- src/data/raba_transit.json (WRTP-CMS)
- ../job_scraper/raba_transit.json (job_scraper)
"""

import os
import io
import csv
import json
import zipfile
import urllib.request
from datetime import datetime

RABA_GTFS_URL = "https://gtfs.remix.com/redding_area_bus_authority.zip"

def fetch_and_parse_gtfs():
    print(f"[RABA GTFS] Downloading archive from {RABA_GTFS_URL}...")
    req = urllib.request.Request(
        RABA_GTFS_URL,
        headers={"User-Agent": "WRTP-Transit-Sync/1.0"}
    )
    with urllib.request.urlopen(req) as resp:
        zip_bytes = resp.read()

    print(f"[RABA GTFS] Downloaded {len(zip_bytes):,} bytes. Extracting feed tables...")
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))

    def read_csv(filename):
        if filename not in zf.namelist():
            return []
        data = zf.read(filename).decode("utf-8-sig", errors="ignore")
        return list(csv.DictReader(data.splitlines()))

    routes_raw = read_csv("routes.txt")
    stops_raw = read_csv("stops.txt")
    trips_raw = read_csv("trips.txt")
    stop_times_raw = read_csv("stop_times.txt")
    calendar_raw = read_csv("calendar.txt")

    print(f"[RABA GTFS] Raw entries: {len(routes_raw)} routes, {len(stops_raw)} stops, {len(trips_raw)} trips, {len(stop_times_raw)} stop times.")

    # 1. Map trip_id to route_id and service_id
    trip_route = {}
    trip_service = {}
    for t in trips_raw:
        tid = t.get("trip_id")
        rid = t.get("route_id")
        sid = t.get("service_id", "")
        if tid and rid:
            trip_route[tid] = rid
            trip_service[tid] = sid

    # 2. Map route_id to clean metadata
    routes_map = {}
    for r in routes_raw:
        rid = r.get("route_id")
        short_name = r.get("route_short_name", "")
        long_name = r.get("route_long_name", "") or f"Route {short_name}"
        color = r.get("route_color", "2EAB8A")
        if not color.startswith("#"):
            color = f"#{color}"
        text_color = r.get("route_text_color", "FFFFFF")
        if not text_color.startswith("#"):
            text_color = f"#{text_color}"
        url = r.get("route_url", "")

        display_name = f"Route {short_name}" if not short_name.lower().startswith("route") else short_name

        routes_map[rid] = {
            "route_id": rid,
            "short_name": short_name,
            "long_name": long_name,
            "display_name": display_name,
            "color": color,
            "text_color": text_color,
            "url": url,
            "stops_count": 0
        }

    # 3. Associate stops with routes & calculate times
    stop_routes_set = {}
    earliest_by_service = {}
    latest_by_service = {}

    for st in stop_times_raw:
        sid = st.get("stop_id")
        tid = st.get("trip_id")
        arr_time = st.get("arrival_time", "").strip()
        rid = trip_route.get(tid)

        if sid and rid and rid in routes_map:
            display_name = routes_map[rid]["display_name"]
            if sid not in stop_routes_set:
                stop_routes_set[sid] = set()
            stop_routes_set[sid].add(display_name)

        # Service hour calculation
        srv = trip_service.get(tid, "").lower()
        day_cat = "weekday"
        if "sa" in srv:
            day_cat = "saturday"
        elif "su" in srv:
            day_cat = "sunday"

        if arr_time and len(arr_time) >= 5:
            # GTFS times can be 24:xx or 25:xx for late night
            if day_cat not in earliest_by_service or arr_time < earliest_by_service[day_cat]:
                earliest_by_service[day_cat] = arr_time
            if day_cat not in latest_by_service or arr_time > latest_by_service[day_cat]:
                latest_by_service[day_cat] = arr_time

    # 4. Build compiled stops array
    compiled_stops = []
    for s in stops_raw:
        sid = s.get("stop_id")
        name = s.get("stop_name", "").strip()
        code = s.get("stop_code", "").strip()
        desc = s.get("stop_desc", "").strip()
        try:
            lat = float(s.get("stop_lat", 0))
            lon = float(s.get("stop_lon", 0))
        except (ValueError, TypeError):
            continue

        if lat == 0 or lon == 0:
            continue

        servicing_routes = sorted(list(stop_routes_set.get(sid, [])))

        # Increment routes count
        for r_name in servicing_routes:
            for r_obj in routes_map.values():
                if r_obj["display_name"] == r_name:
                    r_obj["stops_count"] += 1

        compiled_stops.append({
            "stop_id": sid,
            "stop_code": code,
            "name": name,
            "description": desc,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "routes": servicing_routes
        })

    # Sort stops by name
    compiled_stops.sort(key=lambda x: x["name"])

    # Compiled routes list
    compiled_routes = sorted(list(routes_map.values()), key=lambda x: x["display_name"])

    # Service hours schedule summary
    service_hours = {
        "weekday": {
            "name": "Monday - Friday",
            "active": True,
            "earliest_departure": earliest_by_service.get("weekday", "06:15:00")[:5],
            "latest_arrival": latest_by_service.get("weekday", "19:35:00")[:5],
            "description": "Standard fixed routes operate ~6:15 AM to 7:35 PM"
        },
        "saturday": {
            "name": "Saturday",
            "active": True,
            "earliest_departure": earliest_by_service.get("saturday", "08:30:00")[:5],
            "latest_arrival": latest_by_service.get("saturday", "18:40:00")[:5],
            "description": "Reduced Saturday routes operate ~8:30 AM to 6:40 PM"
        },
        "sunday": {
            "name": "Sunday",
            "active": False,
            "earliest_departure": "N/A",
            "latest_arrival": "N/A",
            "description": "No fixed-route transit service (Sunday Runabout demand-response only)"
        }
    }

    payload = {
        "agency": "Redding Area Bus Authority (RABA)",
        "feed_url": RABA_GTFS_URL,
        "last_synced": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_stops": len(compiled_stops),
        "total_routes": len(compiled_routes),
        "service_hours": service_hours,
        "routes": compiled_routes,
        "stops": compiled_stops
    }

    return payload

def main():
    payload = fetch_and_parse_gtfs()

    # Destination 1: WRTP-CMS
    cms_dir = os.path.join(os.path.dirname(__file__), "..", "src", "data")
    os.makedirs(cms_dir, exist_ok=True)
    cms_target = os.path.join(cms_dir, "raba_transit.json")
    with open(cms_target, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[SUCCESS] Saved {payload['total_stops']} stops and {payload['total_routes']} routes to {cms_target}")

    # Destination 2: job_scraper
    scraper_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "job_scraper"))
    if os.path.exists(scraper_dir):
        scraper_target = os.path.join(scraper_dir, "raba_transit.json")
        with open(scraper_target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"[SUCCESS] Saved copy to {scraper_target}")

if __name__ == "__main__":
    main()
