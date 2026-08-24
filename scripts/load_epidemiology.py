#!/usr/bin/env python3
"""Load institutional epidemiology CSVs into each node's SQLite (locality preserved)."""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schema_mapper.epi import NODE_INSTITUTIONS

SRC = ROOT / "data" / "epidemiology"
DATA = ROOT / "institutional_nodes" / "data"
CAT = ROOT / "gateway" / "store"
CAT.mkdir(parents=True, exist_ok=True)


def _read(name: str) -> list[dict]:
    with (SRC / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_node(node_id: str, path: Path, inst_ids: set[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS epi_diseases (
            disease_id TEXT PRIMARY KEY,
            disease_name TEXT,
            disease_category TEXT,
            icd10_code TEXT
        );
        CREATE TABLE IF NOT EXISTS epi_institutions (
            institution_id TEXT PRIMARY KEY,
            institution_name TEXT,
            institution_type TEXT,
            location TEXT
        );
        CREATE TABLE IF NOT EXISTS epi_records (
            institution_id TEXT,
            year INTEGER,
            disease_id TEXT,
            disease_count INTEGER
        );
        CREATE TABLE IF NOT EXISTS epi_combinations (
            institution_id TEXT,
            year INTEGER,
            combination_id TEXT,
            disease_1 TEXT,
            disease_2 TEXT,
            disease_3 TEXT,
            disease_4 TEXT,
            patient_count INTEGER
        );
        DELETE FROM epi_diseases;
        DELETE FROM epi_institutions;
        DELETE FROM epi_records;
        DELETE FROM epi_combinations;
        """
    )
    for r in _read("diseases.csv"):
        con.execute(
            "INSERT INTO epi_diseases VALUES (?,?,?,?)",
            (r["disease_id"], r["disease_name"], r["disease_category"], r["icd10_code"]),
        )
    for r in _read("institutions.csv"):
        if r["institution_id"] not in inst_ids:
            continue
        con.execute(
            "INSERT INTO epi_institutions VALUES (?,?,?,?)",
            (r["institution_id"], r["institution_name"], r["institution_type"], r["location"]),
        )
    nrec = 0
    for r in _read("disease_records.csv"):
        if r["institution_id"] not in inst_ids:
            continue
        con.execute(
            "INSERT INTO epi_records VALUES (?,?,?,?)",
            (r["institution_id"], int(r["year"]), r["disease_id"], int(r["disease_count"])),
        )
        nrec += 1
    ncomb = 0
    for r in _read("disease_combinations.csv"):
        if r["institution_id"] not in inst_ids:
            continue
        con.execute(
            "INSERT INTO epi_combinations VALUES (?,?,?,?,?,?,?,?)",
            (
                r["institution_id"],
                int(r["year"]),
                r["combination_id"],
                r.get("disease_1") or "",
                r.get("disease_2") or "",
                r.get("disease_3") or "",
                r.get("disease_4") or "",
                int(r["patient_count"] or 0),
            ),
        )
        ncomb += 1
    con.commit()
    con.close()
    print(f"{node_id}: records={nrec} combinations={ncomb} inst={sorted(inst_ids)}")


def load_catalog():
    path = CAT / "catalog.db"
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE diseases (disease_id TEXT, disease_name TEXT, disease_category TEXT, icd10_code TEXT);
        CREATE TABLE institutions (institution_id TEXT, institution_name TEXT, institution_type TEXT, location TEXT, node_id TEXT);
        CREATE TABLE validated_queries (query_id TEXT, year INTEGER, label TEXT, institutions TEXT, total_count INTEGER, status TEXT);
        """
    )
    for r in _read("diseases.csv"):
        con.execute(
            "INSERT INTO diseases VALUES (?,?,?,?)",
            (r["disease_id"], r["disease_name"], r["disease_category"], r["icd10_code"]),
        )
    owner = {i: n for n, ids in NODE_INSTITUTIONS.items() for i in ids}
    for r in _read("institutions.csv"):
        con.execute(
            "INSERT INTO institutions VALUES (?,?,?,?,?)",
            (r["institution_id"], r["institution_name"], r["institution_type"], r["location"], owner.get(r["institution_id"])),
        )
    for r in _read("query_results_sample.csv"):
        con.execute(
            "INSERT INTO validated_queries VALUES (?,?,?,?,?,?)",
            (r["query_id"], int(r["year"]), r["disease_or_combination"], r["institutions_responded"], int(r["total_count"]), r["status"]),
        )
    con.commit()
    con.close()
    print("catalog", path)


if __name__ == "__main__":
    DATA.mkdir(parents=True, exist_ok=True)
    for nid, ids in NODE_INSTITUTIONS.items():
        load_node(nid, DATA / f"{nid}.db", set(ids))
    load_catalog()
    print("ok")
