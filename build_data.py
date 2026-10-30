"""Build the compact browser dataset from a BMTC-compatible GTFS feed.

Usage: python build_data.py /path/to/gtfs-folder
The output is always written to this project's data/app_data.json, regardless
of the current working directory.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
GTFS_DIR = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else ROOT / "gtfs"
OUT     = ROOT / "data" / "app_data.json"
OUT_JS  = ROOT / "data" / "app_data.js"   # script-tag version for file:// access
REQUIRED = ["routes.txt", "stops.txt", "trips.txt", "stop_times.txt", "fare_attributes.txt", "fare_rules.txt"]
missing = [name for name in REQUIRED if not (GTFS_DIR / name).is_file()]
if missing:
    raise SystemExit(f"GTFS folder: {GTFS_DIR}\nMissing required file(s): {', '.join(missing)}")

def read_csv(name: str, **kwargs):
    path = GTFS_DIR / name
    if not path.is_file():
        if kwargs.pop("optional", False):
            return pd.DataFrame()
        raise FileNotFoundError(path)
    return pd.read_csv(path, dtype=str, keep_default_na=False, **kwargs)

routes = read_csv("routes.txt")
stops = read_csv("stops.txt")
trips = read_csv("trips.txt")
stop_times = read_csv("stop_times.txt", usecols=["trip_id", "departure_time", "stop_id", "stop_sequence"])
fares = read_csv("fare_attributes.txt")
fare_rules = read_csv("fare_rules.txt")
translations = read_csv("translations.txt", optional=True)

for table, columns, name in [
    (routes, ["route_id"], "routes.txt"),
    (stops, ["stop_id", "stop_name", "stop_lat", "stop_lon"], "stops.txt"),
    (trips, ["trip_id", "route_id"], "trips.txt"),
    (stop_times, ["trip_id", "departure_time", "stop_id", "stop_sequence"], "stop_times.txt"),
    (fares, ["fare_id", "price"], "fare_attributes.txt"),
    (fare_rules, ["fare_id", "origin_id", "destination_id"], "fare_rules.txt"),
]:
    absent = [c for c in columns if c not in table.columns]
    if absent:
        raise SystemExit(f"{name} is missing required column(s): {', '.join(absent)}")

stop_times["seq"] = pd.to_numeric(stop_times["stop_sequence"], errors="coerce")
stop_times = stop_times.dropna(subset=["seq"])
stop_times["seq"] = stop_times["seq"].astype(int)

def seconds(value: str) -> int:
    try:
        h, m, s = value.split(":")
        return int(h) * 3600 + int(m) * 60 + int(s)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid GTFS departure_time: {value!r}; expected HH:MM:SS")

stop_times["t"] = stop_times["departure_time"].map(seconds)
stop_times = stop_times.sort_values(["trip_id", "seq"])
trip_route = trips.drop_duplicates("trip_id").set_index("trip_id")
route_names = routes.set_index("route_id")["route_short_name"].to_dict() if "route_short_name" in routes else {}
route_long_names = routes.set_index("route_id")["route_long_name"].to_dict() if "route_long_name" in routes else {}
patterns = {}
for trip_id, group in stop_times.groupby("trip_id", sort=False):
    if trip_id not in trip_route.index or len(group) < 2:
        continue
    trip = trip_route.loc[trip_id]
    route_id = trip["route_id"]
    direction = trip.get("direction_id", "0")
    stop_ids = group["stop_id"].tolist()
    start = int(group["t"].iloc[0])
    key = (route_id, direction, tuple(stop_ids))
    if key not in patterns:
        patterns[key] = {
            "r": route_id,
            "n": route_names.get(route_id, route_id),
            "l": route_long_names.get(route_id, ""),
            "s": stop_ids,
            "o": [int(t) - start for t in group["t"]],
            "d": [],
        }
    patterns[key]["d"].append(start)

pattern_list = list(patterns.values())
for pattern in pattern_list:
    pattern["d"].sort()
used_stop_ids = {stop_id for pattern in pattern_list for stop_id in pattern["s"]}
stop_data = {}
for row in stops.itertuples(index=False):
    stop_id = getattr(row, "stop_id")
    if stop_id not in used_stop_ids:
        continue
    try:
        lat, lon = round(float(row.stop_lat), 5), round(float(row.stop_lon), 5)
    except (ValueError, TypeError):
        continue
    stop_data[stop_id] = [row.stop_name, getattr(row, "stop_desc", ""), lat, lon, getattr(row, "zone_id", "")]

price_by_id = {}
for row in fares.itertuples(index=False):
    try:
        price_by_id[row.fare_id] = float(row.price)
    except (ValueError, TypeError):
        continue
fare_data = {}
for row in fare_rules.itertuples(index=False):
    if row.fare_id not in price_by_id:
        continue
    route_id = getattr(row, "route_id", "") or "*"
    fare_data.setdefault(route_id, {})[f"{row.origin_id}|{row.destination_id}"] = price_by_id[row.fare_id]

kannada = {}
if not translations.empty and {"table_name", "language", "record_id", "translation"}.issubset(translations.columns):
    selected = translations[(translations.table_name == "stops") & (translations.language == "kn")]
    kannada = dict(zip(selected.record_id, selected.translation))

payload = {"patterns": pattern_list, "stops": stop_data, "fares": fare_data, "kn": kannada}
OUT.parent.mkdir(parents=True, exist_ok=True)

# 1. JSON file (used by fetch() when served via http://)
with OUT.open("w", encoding="utf-8") as file:
    json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
print(f"Built {OUT}")

# 2. JS file (used by <script src> so the app works via file:// without a server)
with OUT_JS.open("w", encoding="utf-8") as file:
    file.write("/* Auto-generated by build_data.py — do not edit */\n")
    file.write("window.APP_DATA=")
    json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
    file.write(";")
print(f"Built {OUT_JS}")
print(f"{len(pattern_list):,} route patterns · {len(stop_data):,} stops · {OUT.stat().st_size / 1024:.0f} KB")
