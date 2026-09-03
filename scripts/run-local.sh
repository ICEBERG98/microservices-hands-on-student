#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

APP_ENV=local PORT=8081 python3 "$ROOT_DIR/services/catalog/app.py" &
PIDS+=("$!")
APP_ENV=local PORT=8082 CATALOG_URL=http://127.0.0.1:8081 DATA_FILE=/tmp/microservices-orders.json \
  python3 "$ROOT_DIR/services/orders/app.py" &
PIDS+=("$!")
APP_ENV=local PORT=8080 CATALOG_URL=http://127.0.0.1:8081 ORDERS_URL=http://127.0.0.1:8082 \
  python3 "$ROOT_DIR/services/storefront/app.py" &
PIDS+=("$!")

echo "Storefront: http://127.0.0.1:8080"
echo "Catalog:    http://127.0.0.1:8081/products"
echo "Orders:     http://127.0.0.1:8082/orders"
wait
