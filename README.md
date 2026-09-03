# Build Your Own Microservices - Live Hands-on

In this session we build a small shop system inside VS Code. We start with
three empty Python services, make them communicate locally, containerize them,
and deploy them to Kubernetes.

```text
client -> storefront:8080 -> catalog:8081
                          -> orders:8082 -> catalog:8081
                                      |
                                      v
                                persistent data
```

The services use Flask and `requests`, keeping routes and HTTP calls short and
readable while we focus on service boundaries, configuration, containers,
Kubernetes, and troubleshooting.

## Start in VS Code

```bash
code /Users/kashish/git/microservices-hands-on
```

Open the Command Palette and choose **Tasks: Run Task**. The numbered tasks
follow the workshop flow.

Run **0. Set up Flask environment** once before starting.

## Local URLs

| Service | URL | Responsibility |
|---|---|---|
| Storefront | `http://127.0.0.1:8080` | Client-facing API and orchestration |
| Catalog | `http://127.0.0.1:8081/products` | Product data |
| Orders | `http://127.0.0.1:8082/orders` | Order creation and persistence |

## Fast checks

```bash
curl http://127.0.0.1:8080/products
curl -X POST http://127.0.0.1:8080/orders \
  -H 'Content-Type: application/json' \
  -d '{"sku":"keyboard"}'
curl http://127.0.0.1:8080/orders
```

## Workshop checkpoints

1. Each service starts and exposes a liveness endpoint.
2. Storefront calls Catalog through a configurable URL.
3. Orders validates products through Catalog and persists accepted orders.
4. Docker Compose supplies service discovery by name.
5. Kubernetes supplies Services, probes, resources, configuration, and a PVC.
6. We inject one fault and diagnose it from evidence before changing YAML.

The `solution` branch contains the completed implementation for instructor
recovery. Do not switch to it during the normal build-along.
