#!/usr/bin/env python3
"""Génère rnb_to_osm/data/cities.json (nom, code INSEE, bbox WKT) depuis geo.api.gouv.fr."""
import json, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "rnb_to_osm" / "data" / "cities.json"
API = "https://geo.api.gouv.fr"
def get(path):
    with urllib.request.urlopen(API + path, timeout=60) as r:
        return json.load(r)
def ring(bb):
    if isinstance(bb, dict):
        return bb["coordinates"][0]
    w, s, e, n = bb
    return [[w, s], [e, s], [e, n], [w, n], [w, s]]
out = []
for d in get("/departements?fields=code"):
    for c in get(f"/departements/{d['code']}/communes?fields=nom,code,bbox&format=json"):
        if c.get("bbox"):
            wkt = "POLYGON((" + ",".join(f"{x} {y}" for x, y in ring(c["bbox"])) + "))"
            out.append({"name": c["nom"], "code_insee": c["code"], "shape": wkt})
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    json.dump(out, f, ensure_ascii=False)
print(len(out), "communes")
