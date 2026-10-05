#!/usr/bin/env python3
"""Lit l'export CSV RNB sur stdin, écrit rnb_id;shape (polygones uniquement) sur stdout.

Les colonnes sont repérées par leur nom dans l'en-tête : l'ajout de colonnes
dans l'export (ex. validated_by) ne casse pas le filtre.
"""
import csv, io, sys

csv.field_size_limit(sys.maxsize)
r = csv.reader(io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline=""), delimiter=";")
w = csv.writer(sys.stdout, delimiter=";", lineterminator="\n")
header = next(r)
i_id, i_shape = header.index("rnb_id"), header.index("shape")
n = len(header)
print(f"colonnes: {header}", file=sys.stderr)
ok = skip = bad = 0
for row in r:
    if len(row) != n:
        bad += 1
    elif "POLYGON" in row[i_shape][:40]:
        w.writerow((row[i_id], row[i_shape])); ok += 1
    else:
        skip += 1
    if bad > 1000 and ok == 0:
        sys.exit(f"Arrêt : {bad} lignes mal formées et aucun polygone, format inattendu")
print(f"polygones: {ok}  sans polygone: {skip}  lignes mal formees: {bad}", file=sys.stderr)
