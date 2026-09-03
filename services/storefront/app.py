#!/usr/bin/env python3
import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:8081")
ORDERS_URL = os.getenv("ORDERS_URL", "http://127.0.0.1:8082")


def call_service(method, url, payload=None):
    try:
        response = requests.request(method, url, json=payload, timeout=2)
        return response.json(), response.status_code
    except requests.RequestException as error:
        return {"error": "dependency unavailable", "detail": str(error)}, 503


@app.get("/")
@app.get("/products")
def products():
    payload, status = call_service("GET", f"{CATALOG_URL}/products")
    return jsonify(service="storefront", **payload), status


@app.get("/orders")
def orders():
    payload, status = call_service("GET", f"{ORDERS_URL}/orders")
    return jsonify(payload), status


@app.post("/orders")
def create_order():
    payload, status = call_service("POST", f"{ORDERS_URL}/orders", request.get_json(silent=True) or {})
    return jsonify(payload), status


@app.get("/health/startup")
@app.get("/health/live")
def health():
    return jsonify(status="ok", service="storefront")


@app.get("/health/ready")
def readiness():
    _, catalog_status = call_service("GET", f"{CATALOG_URL}/health/ready")
    _, orders_status = call_service("GET", f"{ORDERS_URL}/health/ready")
    ready = catalog_status == 200 and orders_status == 200
    return jsonify(status="ready" if ready else "dependency unavailable"), 200 if ready else 503


@app.get("/config")
def config():
    return jsonify(service="storefront", environment=os.getenv("APP_ENV", "development"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
