#!/usr/bin/env python3
"""Minimal Flask app that loads CSV files from data/csv on startup."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify

APP_ROOT = Path(__file__).resolve().parent
CSV_DIR = APP_ROOT / "data" / "csv"

app = Flask(__name__)


def load_csv_data() -> Dict[str, List[Dict[str, Any]]]:
    """Read all CSV files in data/csv into memory."""
    data: Dict[str, List[Dict[str, Any]]] = {}
    if not CSV_DIR.exists():
        return data

    for csv_path in sorted(CSV_DIR.glob("*.csv")):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = [row for row in reader]
        data[csv_path.name] = rows
    return data


CSV_DATA = load_csv_data()


@app.get("/")
def index() -> Dict[str, Any]:
    """Basic health route."""
    return {
        "message": "Flask CSV app is running",
        "available_files": sorted(CSV_DATA.keys()),
    }


@app.get("/data")
def data() -> Dict[str, List[Dict[str, Any]]]:
    """Return the cached CSV data."""
    return CSV_DATA


if __name__ == "__main__":
    app.run(debug=True)
