# Local Kind lab - commands students perform themselves

Use the VS Code integrated terminal throughout. Do not copy a final repository
or run a setup wrapper. At every stage, explain what the command changes and
what evidence will prove it worked.

## 1. Verify the local tools

```bash
docker version
kind version
kubectl version --client
helm version
```

If a command is missing on macOS, install Docker Desktop first, start it, then:

```bash
brew install kind kubectl helm
```

Checkpoint: `docker info` succeeds. Kind creates Kubernetes nodes as Docker
containers, so a CLI without a running Docker engine is not sufficient.

## 2. Run the application before Kubernetes

Create the Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Open three VS Code terminals and run one command in each:

```bash
APP_ENV=local PORT=8081 python services/catalog/app.py
```

```bash
APP_ENV=local PORT=8082 CATALOG_URL=http://127.0.0.1:8081 DATA_FILE=/tmp/orders.json python services/orders/app.py
```

```bash
APP_ENV=local PORT=8080 CATALOG_URL=http://127.0.0.1:8081 ORDERS_URL=http://127.0.0.1:8082 python services/storefront/app.py
```

In a fourth terminal:

```bash
curl http://127.0.0.1:8080/products
curl -X POST http://127.0.0.1:8080/orders -H 'Content-Type: application/json' -d '{"sku":"keyboard"}'
curl http://127.0.0.1:8080/orders
```

Checkpoint: students can draw the request path and identify which value must
change when the services no longer share the host network.

## 3. Create a multi-node Kind cluster

In VS Code, create `kind-config.yaml`:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8080
      - containerPort: 30443
        hostPort: 8443
  - role: worker
  - role: worker
networking:
  disableDefaultCNI: true
  podSubnet: 192.168.0.0/16
```

Create the cluster. Its nodes will initially be `NotReady` because we
deliberately disabled Kind's simple default networking implementation:

```bash
kind create cluster --name microshop --config kind-config.yaml
kubectl config current-context
kubectl cluster-info
kubectl get nodes -o wide
```

Install Calico so the cluster has both Pod networking and NetworkPolicy
enforcement:

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.32.2/manifests/v1_crd_projectcalico_org.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.32.2/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.32.2/manifests/custom-resources.yaml
kubectl wait --for=condition=Ready nodes --all --timeout=5m
```

Add labels for the placement exercise:

```bash
kubectl label node microshop-worker topology.kubernetes.io/zone=zone-a workload=apps
kubectl label node microshop-worker2 topology.kubernetes.io/zone=zone-b workload=apps
kubectl get nodes -L topology.kubernetes.io/zone,workload
```

Checkpoint: current context is `kind-microshop`, all three nodes are Ready, and
Calico Pods are running. Without a policy-enforcing CNI, later NetworkPolicy
tests would be misleading.

## 4. Build and load the three images

```bash
docker build -f services/catalog/Dockerfile -t microshop-catalog:local .
docker build -f services/orders/Dockerfile -t microshop-orders:local .
docker build -f services/storefront/Dockerfile -t microshop-storefront:local .

kind load docker-image microshop-catalog:local --name microshop
kind load docker-image microshop-orders:local --name microshop
kind load docker-image microshop-storefront:local --name microshop
```

Ask: why use `imagePullPolicy: Never` for these local images? What would change
if a registry were used?

## 5. Write the Kubernetes resources

Create the files under `k8s/base/` and add each to `kustomization.yaml`.

### Namespace and configuration

Create namespace `microshop` and a ConfigMap containing:

```text
APP_ENV=kubernetes
CATALOG_URL=http://catalog:8081
ORDERS_URL=http://orders:8082
DATA_FILE=/data/orders.json
```

Keep a sample sensitive value in a Secret, but never decode or display it in
submitted evidence.

### Deployments

Create Catalog first, then adapt the pattern for Orders and Storefront. Each
Deployment must include:

- matching selector and Pod labels;
- named container port;
- ConfigMap/Secret references;
- startup, readiness, and liveness probes using the supplied endpoints;
- CPU/memory requests and limits;
- `imagePullPolicy: Never`;
- a ServiceAccount;
- placement across the two labelled workers where practical.

Render before applying:

```bash
kubectl kustomize k8s/base
kubectl apply --dry-run=client -k k8s/base
kubectl apply -k k8s/base
kubectl get pods -n microshop -o wide
kubectl get events -n microshop --sort-by=.lastTimestamp
```

### Persistent Orders data

Create a PVC and mount it at `/data` in Orders. Create an order, delete the
Orders Pod, wait for its replacement, and prove the order still exists.

## 6. Create and diagnose Services

Create ClusterIP Services named `catalog`, `orders`, and `storefront`.

```bash
kubectl get service,endpointslice -n microshop
kubectl describe service catalog -n microshop
kubectl get pods -n microshop --show-labels
```

Inject the supplied bad selector only after the healthy route works:

```bash
kubectl apply -f k8s/failures/bad-service-selector.yaml
```

Diagnose it from DNS, selectors, Pod labels, readiness, ports, and
EndpointSlices. Repair the generating manifest—not the live object alone.

## 7. Add scheduling and disruption controls

Try one impossible node selector and observe the `PodScheduled` condition and
`FailedScheduling` Event. Then repair it using the labels created earlier.

Add a PodDisruptionBudget to a two-replica workload. Explain why a PDB affects
voluntary eviction but does not guarantee availability during every failure.

## 8. Install Ingress and configure TLS

Install the controller by typing the Helm commands:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace --set controller.service.type=NodePort --set controller.service.nodePorts.http=30080 --set controller.service.nodePorts.https=30443 --wait
```

Create a short-lived local certificate and Kubernetes TLS Secret. Keep the key
under ignored `generated/`:

```bash
mkdir -p generated
openssl req -x509 -nodes -newkey rsa:2048 -days 7 -keyout generated/microshop.key -out generated/microshop.crt -subj '/CN=microshop.local' -addext 'subjectAltName=DNS:microshop.local'
kubectl create secret tls microshop-tls -n microshop --cert=generated/microshop.crt --key=generated/microshop.key
```

Write an Ingress that exposes only Storefront. Verify without `-k`:

```bash
curl --resolve microshop.local:8443:127.0.0.1 --cacert generated/microshop.crt https://microshop.local:8443/products
```

## 9. Add RBAC and NetworkPolicy

Create one Role/RoleBinding that permits the assigned ServiceAccount to read
ConfigMaps in `microshop`. Prove a read is allowed and Secret deletion denied:

```bash
kubectl auth can-i get configmaps -n microshop --as=system:serviceaccount:microshop:storefront
kubectl auth can-i delete secrets -n microshop --as=system:serviceaccount:microshop:storefront
```

Apply a default-deny policy, allow DNS, then allow only the required service
flows. Test an approved caller and an unrelated diagnostic Pod before and after.

## 10. Move the proven resources into Helm

Use `chart/microshop/` only after the plain resources work:

```bash
helm lint chart/microshop
helm template microshop chart/microshop -n microshop
helm upgrade --install microshop chart/microshop -n microshop --create-namespace
helm get values microshop -n microshop --all
helm get manifest microshop -n microshop
helm history microshop -n microshop
```

Change one environment value, predict the rendered change, upgrade, and inspect
the new revision.

## 11. Finish with evidence, not green status

For the assigned failure, complete `INCIDENT_NOTES.md`:

```text
symptom -> hypothesis -> evidence -> narrow -> change -> verify
```

Repeat the original failing request and one negative test after the repair.

## Cleanup after class

Confirm the exact target before deletion:

```bash
kind get clusters
kind delete cluster --name microshop
```
