#!/usr/bin/env python3
import json
import os
from pathlib import Path
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:8081")
DATA_FILE = Path(os.getenv("DATA_FILE", "/tmp/microservices-orders.json"))


def load_orders():
    try:
        return json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else []
    except (json.JSONDecodeError, OSError):
        return []


def product_exists(sku):
    try:
        return requests.get(f"{CATALOG_URL}/products/{sku}", timeout=2).status_code == 200
    except requests.RequestException:
        return False


@app.get("/orders")
def list_orders():
    return jsonify(orders=load_orders())


@app.post("/orders")
def create_order():
    sku = (request.get_json(silent=True) or {}).get("sku")
    if not sku or not product_exists(sku):
        return jsonify(error="unknown or missing sku"), 400
    orders = load_orders()
    order = {"id": len(orders) + 1, "sku": sku, "status": "accepted"}
    orders.append(order)
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(orders, indent=2))
    return jsonify(order), 201


@app.get("/health/startup")
@app.get("/health/live")
def health():
    return jsonify(status="ok", service="orders")


@app.get("/health/ready")
def readiness():
    ready = product_exists("keyboard")
    return jsonify(status="ready" if ready else "catalog unavailable"), 200 if ready else 503


@app.get("/config")
def config():
    return jsonify(service="orders", environment=os.getenv("APP_ENV", "development"), catalog_url=CATALOG_URL)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8082")))
