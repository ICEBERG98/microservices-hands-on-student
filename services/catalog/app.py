#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PRODUCTS = {
    "keyboard": {"sku": "keyboard", "name": "Mechanical Keyboard", "price": 79},
    "mouse": {"sku": "mouse", "name": "Wireless Mouse", "price": 39},
    "monitor": {"sku": "monitor", "name": "27-inch Monitor", "price": 249},
}


class Handler(BaseHTTPRequestHandler):
    server_version = "catalog/1.0"

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/health/startup", "/health/ready", "/health/live"):
            return self.send_json(200, {"status": "ok", "service": "catalog"})
        if self.path == "/config":
            return self.send_json(200, {"service": "catalog", "environment": os.getenv("APP_ENV", "development")})
        if self.path == "/products":
            return self.send_json(200, {"products": list(PRODUCTS.values())})
        if self.path.startswith("/products/"):
            sku = self.path.removeprefix("/products/")
            product = PRODUCTS.get(sku)
            return self.send_json(200 if product else 404, product or {"error": "unknown sku"})
        return self.send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(json.dumps({"service": "catalog", "message": fmt % args}), flush=True)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8081"))
    print(json.dumps({"service": "catalog", "event": "started", "port": port}), flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
