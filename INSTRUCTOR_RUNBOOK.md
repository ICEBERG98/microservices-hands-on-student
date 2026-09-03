# Instructor runbook - 120-minute VS Code build-along

## Teaching promise

Say: **"Let us create our own set of microservices."** Then create the code in
front of the class. The default branch contains only the starting skeleton.
Use the `solution` branch solely as a recovery reference.

## Before students arrive

- Open the repository folder in VS Code.
- Keep one editor group for code and one integrated terminal visible.
- Confirm Python 3 and `curl` work, then run `./scripts/setup.sh`.
- If using containers or Kubernetes, connect to the classroom host first.
- Keep the Git branch on `main` and the working tree clean.

## 0-10 minutes - draw the boundary

Draw only this architecture in `README.md`:

```text
client -> storefront -> catalog
                   \-> orders -> catalog
```

Ask: Why not place all three responsibilities in one process? Land independent
change, failure isolation, and ownership—while acknowledging the networking and
operational cost introduced by microservices.

## 10-30 minutes - create Catalog

Create `services/catalog/app.py` with Flask:

- `app = Flask(__name__)`;
- `@app.get("/products")`;
- `@app.get("/products/<sku>")`;
- `@app.get("/health/live")`.

Run it in the integrated terminal and prove it with `curl`. Commit checkpoint:

```bash
git add . && git commit -m "build catalog service"
```

## 30-50 minutes - create Orders

Create `services/orders/app.py`. Read `CATALOG_URL` from the environment, call
Catalog before accepting an order, and store accepted orders in a JSON file.
Discuss synchronous dependency failure and timeouts. Commit checkpoint:

```bash
git add . && git commit -m "build orders service"
```

## 50-65 minutes - create Storefront

Create `services/storefront/app.py`. Add `GET /products`, `POST /orders`, and
`GET /orders` as thin calls to the two internal services. Show a failed call by
stopping Catalog, then restore it. Commit checkpoint:

```bash
git add . && git commit -m "connect storefront to internal services"
```

## 65-80 minutes - containerize

Write one Dockerfile together, then let students adapt it twice. Add
`compose.yaml`; replace loopback dependency URLs with Compose service names.
Ask why `localhost` inside Storefront is not Catalog. Run the smoke test.

## 80-105 minutes - move to Kubernetes

Create resources in this order:

1. Namespace and ConfigMap;
2. Catalog Deployment and Service;
3. Orders Deployment, Service, and PVC;
4. Storefront Deployment and Service;
5. startup, readiness, and liveness probes;
6. requests and limits.

Render before applying:

```bash
kubectl kustomize k8s/base
```

After deploying, trace the request path through Service selectors and
EndpointSlices. Avoid adding Ingress/TLS until the internal path is healthy.

## 105-117 minutes - evidence-led incident

Inject exactly one fault:

```bash
kubectl apply -f k8s/failures/bad-service-selector.yaml
```

Use this narration and record each answer in `INCIDENT_NOTES.md`:

```text
symptom -> hypothesis -> evidence -> narrow -> change -> verify
```

Strong evidence: the Service exists, DNS resolves, but its EndpointSlice has no
addresses because the selector does not match Pod labels. Restore with:

```bash
kubectl apply -f k8s/base/catalog.yaml
```

## 117-120 minutes - close

Ask students to name the new operational costs: discovery, timeouts, partial
failure, distributed logs, version compatibility, and more deployment units.
End with: microservices are an organizational and operational tradeoff, not a
default measure of architectural maturity.

## Recovery commands

Inspect the completed file without changing branches:

```bash
git show solution:services/catalog/app.py
```

Restore one completed file only when necessary:

```bash
git show solution:services/catalog/app.py > /tmp/catalog-app.py
```

Copy from the temporary file manually so students can still follow the change.
