#!/usr/bin/env python3
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:8081")
DATA_FILE = Path(os.getenv("DATA_FILE", "/tmp/microservices-orders.json"))


def load_orders():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def save_orders(orders):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(orders, indent=2))


def product_exists(sku):
    try:
        with urllib.request.urlopen(f"{CATALOG_URL}/products/{sku}", timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = "orders/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/health/startup", "/health/live"):
            return self.send_json(200, {"status": "ok", "service": "orders"})
        if self.path == "/health/ready":
            return self.send_json(200 if product_exists("keyboard") else 503, {"status": "ready" if product_exists("keyboard") else "catalog unavailable"})
        if self.path == "/config":
            return self.send_json(200, {"service": "orders", "environment": os.getenv("APP_ENV", "development"), "catalog_url": CATALOG_URL})
        if self.path == "/orders":
            return self.send_json(200, {"orders": load_orders()})
        return self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/orders":
            return self.send_json(404, {"error": "not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self.send_json(400, {"error": "invalid JSON"})
        sku = payload.get("sku")
        if not sku or not product_exists(sku):
            return self.send_json(400, {"error": "unknown or missing sku"})
        orders = load_orders()
        order = {"id": len(orders) + 1, "sku": sku, "status": "accepted"}
        orders.append(order)
        save_orders(orders)
        return self.send_json(201, order)

    def log_message(self, fmt, *args):
        print(json.dumps({"service": "orders", "message": fmt % args}), flush=True)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8082"))
    print(json.dumps({"service": "orders", "event": "started", "port": port}), flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
