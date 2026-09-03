#!/usr/bin/env python3
import os
from flask import Flask, jsonify

app = Flask(__name__)
PRODUCTS = {
    "keyboard": {"sku": "keyboard", "name": "Mechanical Keyboard", "price": 79},
    "mouse": {"sku": "mouse", "name": "Wireless Mouse", "price": 39},
    "monitor": {"sku": "monitor", "name": "27-inch Monitor", "price": 249},
}


@app.get("/products")
def list_products():
    return jsonify(products=list(PRODUCTS.values()))


@app.get("/products/<sku>")
def get_product(sku):
    product = PRODUCTS.get(sku)
    return (jsonify(product), 200) if product else (jsonify(error="unknown sku"), 404)


@app.get("/health/startup")
@app.get("/health/ready")
@app.get("/health/live")
def health():
    return jsonify(status="ok", service="catalog")


@app.get("/config")
def config():
    return jsonify(service="catalog", environment=os.getenv("APP_ENV", "development"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8081")))
