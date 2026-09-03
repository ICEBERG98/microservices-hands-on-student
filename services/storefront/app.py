#!/usr/bin/env python3
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:8081")
ORDERS_URL = os.getenv("ORDERS_URL", "http://127.0.0.1:8082")


def fetch_json(url, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())
    except (urllib.error.URLError, TimeoutError) as error:
        return 503, {"error": "dependency unavailable", "detail": str(error.reason if hasattr(error, "reason") else error)}


class Handler(BaseHTTPRequestHandler):
    server_version = "storefront/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/health/startup", "/health/live"):
            return self.send_json(200, {"status": "ok", "service": "storefront"})
        if self.path == "/health/ready":
            catalog_status, _ = fetch_json(f"{CATALOG_URL}/health/ready")
            orders_status, _ = fetch_json(f"{ORDERS_URL}/health/ready")
            ready = catalog_status == 200 and orders_status == 200
            return self.send_json(200 if ready else 503, {"status": "ready" if ready else "dependency unavailable"})
        if self.path == "/config":
            return self.send_json(200, {"service": "storefront", "environment": os.getenv("APP_ENV", "development")})
        if self.path == "/" or self.path == "/products":
            status, payload = fetch_json(f"{CATALOG_URL}/products")
            return self.send_json(status, {"service": "storefront", **payload})
        if self.path == "/orders":
            status, payload = fetch_json(f"{ORDERS_URL}/orders")
            return self.send_json(status, payload)
        return self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/orders":
            return self.send_json(404, {"error": "not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self.send_json(400, {"error": "invalid JSON"})
        status, response = fetch_json(f"{ORDERS_URL}/orders", method="POST", payload=payload)
        return self.send_json(status, response)

    def log_message(self, fmt, *args):
        print(json.dumps({"service": "storefront", "message": fmt % args}), flush=True)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(json.dumps({"service": "storefront", "event": "started", "port": port}), flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
