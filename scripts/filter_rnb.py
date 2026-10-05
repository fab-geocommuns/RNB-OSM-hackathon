#!/usr/bin/env python3
import csv, io, sys
csv.field_size_limit(sys.maxsize)
r = csv.reader(io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline=""), delimiter=";")
w = csv.writer(sys.stdout, delimiter=";", lineterminator="\n")
next(r)
ok = skip = bad = 0
for row in r:
    if len(row) != 7:
        bad += 1
    elif "POLYGON" in row[2][:40]:
        w.writerow((row[0], row[2])); ok += 1
    else:
        skip += 1
print(f"polygones: {ok}  sans polygone: {skip}  lignes mal formees: {bad}", file=sys.stderr)
