#!/usr/bin/env bash
set -euo pipefail

curl --fail --silent http://127.0.0.1:8080/health/ready >/dev/null
curl --fail --silent http://127.0.0.1:8080/products | grep -q 'keyboard'
curl --fail --silent -X POST http://127.0.0.1:8080/orders \
  -H 'Content-Type: application/json' \
  -d '{"sku":"keyboard"}' | grep -q 'accepted'
curl --fail --silent http://127.0.0.1:8080/orders | grep -q 'keyboard'
echo "Smoke test passed: dependencies, order creation, and persistence path work."
