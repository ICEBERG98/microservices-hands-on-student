# Operate Your Own Microservices - Session 6 Hands-on

In this session we operate a small shop system inside VS Code. The Flask
services are already complete; the live work is Kubernetes production
configuration, Helm, and evidence-led troubleshooting.

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

Open [LAB_GUIDE.md](LAB_GUIDE.md) beside the integrated terminal. Students type
each command and create each Kubernetes file themselves; there are deliberately
no setup wrappers or task shortcuts.

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

1. Tour the working service boundaries and dependencies.
2. Add Kubernetes configuration, probes, resources, and persistent storage.
3. Prove scheduling decisions and disruption behavior.
4. Trace Services through selectors, ports, and EndpointSlices.
5. Verify Ingress/TLS, RBAC, and NetworkPolicy boundaries.
6. Render and operate the system through Helm.
7. Diagnose one fault from evidence before changing YAML.

Use [LAB_CHECKLIST.md](LAB_CHECKLIST.md) during the exercise. The `solution`
branch contains completed Kubernetes resources for instructor recovery.
