#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from institutional_nodes.generate_data import generate_all
import argparse

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--patients", type=int, default=10000)
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()
    print(generate_all(a.patients, a.seed))
