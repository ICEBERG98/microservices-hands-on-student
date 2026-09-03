# Session 6 instructor runbook - production Kubernetes hands-on

## The framing

Open with: **"Let us create our own set of microservices—but our real job today
is to operate them correctly."**

The Flask code is already complete. Spend no more than ten minutes touring it.
Students write Kubernetes and Helm configuration, predict behavior, inspect
evidence, and repair faults. That is the assessed learning.

```text
client -> storefront -> catalog
                   \-> orders -> catalog
                          |
                          v
                         PVC
```

## Alignment with completed classes

| Today | Prior classroom material | Student action |
|---|---|---|
| Probes, resources, storage | Production workload foundations | Configure and prove behavior |
| Placement and disruption | Session 3 | Predict scheduling and safe disruption |
| Services and EndpointSlices | Session 4 | Trace traffic and repair selectors/ports |
| Ingress and TLS | Session 4 | Expose Storefront and verify identity/trust |
| ServiceAccount and RBAC | Session 4 | Allow one action while denying a broader one |
| Rendering, values, releases | Session 5 | Render, predict, install, inspect, upgrade |
| Troubleshooting | Sessions 2-5 | Use evidence before changing configuration |

## Before class

1. Open `microservices-hands-on.code-workspace` on branch `main`.
2. Keep `LAB_GUIDE.md` open beside the VS Code integrated terminal.
3. Confirm Docker Desktop is running and Kind, kubectl, and Helm are installed.
4. Ensure the room network can download the Kind node, application, and
   ingress-controller images; pre-pull them on the instructor machine.
5. Students type the environment, cluster, image, and Kubernetes commands.
6. Keep `solution` only as an instructor recovery branch.

## 0-10 minutes - establish the system, not the implementation

Show one Flask route and one `requests` call. Demonstrate `/products` and
`POST /orders`, then stop. Ask students to identify:

- the three deployable units;
- two synchronous dependencies;
- the state that must survive an Orders Pod replacement;
- the externally exposed service;
- what can fail independently.

Do not write application code during this segment.

## 10-30 minutes - production workload controls

Create the Catalog Deployment together, then have students adapt the pattern.
Add and discuss:

- ConfigMap-driven `APP_ENV`, `CATALOG_URL`, and `ORDERS_URL`;
- startup, readiness, and liveness probes with distinct endpoints;
- CPU and memory requests/limits;
- Orders PVC mounted at `/data`.

Required evidence:

```text
rendered fields -> Pod Ready condition -> EndpointSlice membership
write order -> replace Orders Pod -> read the same order
```

## 30-45 minutes - placement and disruption

Ask students to predict before each change:

- What do requests influence?
- What happens with an impossible node selector?
- Why does anti-affinity behave differently on one and three nodes?
- What can a PodDisruptionBudget protect, and what can it not protect?

Use `kubectl describe pod` and sorted Events as the primary evidence. Do not
solve Pending by deleting Pods repeatedly.

## 45-65 minutes - Service discovery and traffic

Create ClusterIP Services for all three workloads. Trace:

```text
Service DNS -> Service port -> targetPort -> Ready Pod IP
```

Inspect labels, selectors, named ports, and EndpointSlices. Inject the supplied
bad Catalog selector only after the healthy path has been proven.

Expected reasoning:

```text
DNS succeeds + Service exists + no EndpointSlice addresses
-> inspect selector and Pod labels
```

## 65-82 minutes - Ingress and TLS

Expose only Storefront. Configure the assigned hostname, path, backend Service,
TLS host, and Secret reference. Prove the complete path with certificate
verification enabled.

Do not accept `curl -k` as final evidence. Keep private keys out of terminals,
screenshots, Git, and `/config` responses.

## 82-97 minutes - workload identity and authorization

Use the smallest supplied RBAC scenario:

- the assigned ServiceAccount can perform one required read;
- a higher-risk action remains denied.

Do not add NetworkPolicy to the default Kind exercise. Its basic network does
not enforce policy, and installing another CNI would distract from the concepts
you are prepared to teach. Revisit the supplied policy later in the configured
course environment.

## 97-110 minutes - Helm workflow

Package or adapt the working manifests using the chart scaffold. Preserve the
Session 5 rhythm:

```text
render -> predict -> mutate -> prove
```

Run lint/template before install. After install, inspect both Helm release
state and Kubernetes objects. Change one value, upgrade, inspect history, then
explain what rollback can and cannot reverse.

## 110-120 minutes - evidence-led incident

Use one fault only. Students must record:

```text
symptom -> hypothesis -> evidence -> narrow -> change -> verify
```

Minimum evidence should include one condition/Event/log/EndpointSlice or
authorization result—not merely a final screenshot of Running Pods. Repeat the
original failing action and one negative test after the repair.

## What to cut if time slips

Cut application explanation first, then the Helm rollback demonstration. Keep:

1. probes/resources/storage;
2. Service/EndpointSlice diagnosis;
3. one RBAC security boundary;
4. one complete evidence-led repair.

## Recovery

The known-good implementation is on `solution`. Inspect a file without changing
the classroom branch:

```bash
git show solution:k8s/base/catalog.yaml
git show solution:services/storefront/app.py
```
