# From three local services to a Kubernetes application

Today we have a small shop application with three services:

```text
storefront -> catalog
          \-> orders -> catalog
```

The Flask code is already written. We are going to take responsibility for
running it: first on the laptop, then inside a local Kubernetes cluster.

Work in the VS Code terminal. Type the commands rather than pasting the whole
lab at once. After every change, stop and look at what Kubernetes is telling
you.

We will let `kubectl` generate boring first drafts. The generator does not
design the workload for us; it gives us valid metadata and structure that we
then read and improve in VS Code.

## Before we start

Check the tools we will actually use:

```bash
docker version
kind version
kubectl version --client
helm version
```

Docker must be running, not merely installed. If `docker version` cannot reach
the server, start Docker Desktop before going further.

On macOS, the remaining command-line tools can be installed with:

```bash
brew install kind kubectl helm
```

## First, let us see the application

Create a Python environment and install the two application dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Open three VS Code terminals.

Catalog:

```bash
APP_ENV=local PORT=8081 python services/catalog/app.py
```

Orders:

```bash
APP_ENV=local PORT=8082 CATALOG_URL=http://127.0.0.1:8081 DATA_FILE=/tmp/orders.json python services/orders/app.py
```

Storefront:

```bash
APP_ENV=local PORT=8080 CATALOG_URL=http://127.0.0.1:8081 ORDERS_URL=http://127.0.0.1:8082 python services/storefront/app.py
```

Try the complete path from a fourth terminal:

```bash
curl http://127.0.0.1:8080/products
curl -X POST http://127.0.0.1:8080/orders -H 'Content-Type: application/json' -d '{"sku":"keyboard"}'
curl http://127.0.0.1:8080/orders
```

Before moving on, answer one question: when these processes become separate
Pods, can they continue to find each other through `127.0.0.1`?

They cannot. We will need Kubernetes networking and stable service names.

## Give ourselves a cluster

Kind runs Kubernetes nodes as Docker containers. We will use two workers so
that placement and disruption are visible rather than theoretical.

Create `kind-config.yaml` in VS Code:

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
```

Now create the cluster and look at it:

```bash
kind create cluster --name microshop --config kind-config.yaml
kubectl config current-context
kubectl get nodes -o wide
```

The context should be `kind-microshop` and all three nodes should become
`Ready`. Do not continue on the wrong context.

Label the workers so that we can make an intentional placement decision later:

```bash
kubectl label node microshop-worker topology.kubernetes.io/zone=zone-a workload=apps
kubectl label node microshop-worker2 topology.kubernetes.io/zone=zone-b workload=apps
kubectl get nodes -L topology.kubernetes.io/zone,workload
```

## Build an image—and discover the Kind boundary

Start with Catalog only:

```bash
docker build -f services/catalog/Dockerfile -t microshop-catalog:local .
```

The image now exists on the laptop. Kind's nodes are separate Docker
containers, so their container runtime cannot see that image yet:

```bash
kind load docker-image microshop-catalog:local --name microshop
```

This is why the classroom manifests use `imagePullPolicy: Never`: the image is
loaded into the nodes instead of pulled from a registry.

Build and load the other two in the same way:

```bash
docker build -f services/orders/Dockerfile -t microshop-orders:local .
docker build -f services/storefront/Dockerfile -t microshop-storefront:local .
kind load docker-image microshop-orders:local --name microshop
kind load docker-image microshop-storefront:local --name microshop
```

## Get one Pod running before designing the whole system

Ask `kubectl` for a Namespace manifest instead of typing its boilerplate:

```bash
kubectl create namespace microshop --dry-run=client -o yaml > k8s/base/namespace.yaml
```

Open the generated file in VS Code. Notice that the command only produced YAML;
`--dry-run=client` did not change the cluster. Add the file to
`k8s/base/kustomization.yaml`, render it, and apply it:

```bash
kubectl kustomize k8s/base
kubectl apply -k k8s/base
```

Generate the first draft of the Catalog Deployment:

```bash
kubectl create deployment catalog \
  --image=microshop-catalog:local \
  --replicas=1 \
  -n microshop \
  --dry-run=client -o yaml > k8s/base/catalog-deployment.yaml
```

Open it before applying it. The generator does not know our listener, local
image policy, or health model. Add:

- image `microshop-catalog:local`;
- `imagePullPolicy: Never`;
- container port `8081` named `http`;
- one replica;
- Pod label `app: catalog`.

Apply it and watch what happens:

```bash
kubectl apply -k k8s/base
kubectl get pods -n microshop -w
```

When the Pod is Running, inspect the object rather than immediately moving on:

```bash
kubectl describe pod -n microshop -l app=catalog
kubectl logs -n microshop -l app=catalog
```

At this point we have a process, but no stable way for another Pod to find it.

## Give Catalog a stable name

Generate a ClusterIP Service named `catalog`:

```bash
kubectl create service clusterip catalog \
  --tcp=8081:8081 \
  -n microshop \
  --dry-run=client -o yaml > k8s/base/catalog-service.yaml
```

Open it and compare its selector with the generated Deployment labels. Change
the `targetPort` to the named container port after adding that port to the
Deployment.

```bash
kubectl apply -k k8s/base
kubectl get service,endpointslice -n microshop
kubectl get pods -n microshop --show-labels
```

The EndpointSlice is the useful proof here. If it has an address, the selector,
readiness state, and Service relationship are working together.

Now deliberately apply the broken Service:

```bash
kubectl apply -f k8s/failures/bad-service-selector.yaml
kubectl get service,endpointslice -n microshop
```

Do not open the answer file. Compare the Service selector with the Pod labels,
form a hypothesis, repair `k8s/base/catalog.yaml`, and reapply the base.

## Add Orders; configuration becomes necessary

Orders needs to know where Catalog lives. Hardcoding an address in the image
would tie configuration to the artifact, so generate a ConfigMap first draft:

```bash
kubectl create configmap microshop-config \
  -n microshop \
  --from-literal=APP_ENV=kubernetes \
  --from-literal=CATALOG_URL=http://catalog:8081 \
  --from-literal=ORDERS_URL=http://orders:8082 \
  --from-literal=DATA_FILE=/data/orders.json \
  --dry-run=client -o yaml > k8s/base/config.yaml
```

Open the generated YAML. Its data should be:

```text
APP_ENV=kubernetes
CATALOG_URL=http://catalog:8081
ORDERS_URL=http://orders:8082
DATA_FILE=/data/orders.json
```

Generate the Orders Deployment and Service using the same two `kubectl create`
patterns, changing the name, image, and ports. Then edit the Deployment to load
the ConfigMap with `envFrom`.

```bash
kubectl apply -k k8s/base
kubectl get pods,service,endpointslice -n microshop
kubectl logs -n microshop -l app=orders
```

Generate Storefront in the same way on container port `8080`. Once all three
Services have endpoints, temporarily forward Storefront to the laptop:

```bash
kubectl port-forward -n microshop service/storefront 8080:80
```

Repeat the three `curl` requests from the beginning. We now have the same user
flow, but each responsibility runs in a separate Pod and uses Kubernetes DNS.

## Now ask whether Running is good enough

So far Kubernetes only knows whether each process exists. Add the probes using
the endpoints already present in the application:

```text
startup:   /health/startup
readiness: /health/ready
liveness:  /health/live
```

Use the named `http` port. Apply the change and compare these signals:

```bash
kubectl get pods -n microshop
kubectl describe pod -n microshop -l app=storefront
kubectl get endpointslice -n microshop
```

Discuss the difference visible in the system:

- startup protects initialization;
- readiness controls Service membership;
- liveness can restart an unhealthy container.

Add CPU and memory requests and limits only after the workloads are healthy.
Then inspect what the scheduler now knows:

```bash
kubectl describe node microshop-worker
kubectl get pods -n microshop -o custom-columns=NAME:.metadata.name,CPU:.spec.containers[0].resources.requests.cpu,MEMORY:.spec.containers[0].resources.requests.memory
```

## Let Orders lose data once

Create an order, note the response, and then delete the Orders Pod:

```bash
kubectl delete pod -n microshop -l app=orders
kubectl rollout status deployment/orders -n microshop
```

Fetch the orders again. The replacement Pod has a new container filesystem, so
the order is gone. That failure gives us the reason for persistent storage.

Create a PVC, mount it at `/data`, and repeat the same experiment:

```bash
kubectl get pvc -n microshop
kubectl get pv
```

Create an order, replace the Pod again, and prove that the order remains. The
evidence is the before-and-after API response, not merely a Bound PVC.

## Make replicas and placement visible

Scale Catalog and Storefront to two replicas. Use the worker labels from
earlier to keep application Pods on nodes labelled `workload=apps`.

```bash
kubectl get pods -n microshop -o wide
```

Before fixing it, try an impossible node selector on one Deployment. Observe
the Pending Pod:

```bash
kubectl describe pod -n microshop <pending-pod-name>
kubectl get events -n microshop --sort-by=.lastTimestamp
```

The scheduling Event should lead to the repair. Do not delete and recreate the
Pod until you understand why no node is eligible.

Add a PodDisruptionBudget to one two-replica workload. Discuss what it protects
during voluntary disruption and why it cannot protect against every failure.

## Expose only the edge service

Catalog and Orders should remain internal. Storefront is the entry point.

Install the ingress controller with Helm:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace --set controller.service.type=NodePort --set controller.service.nodePorts.http=30080 --set controller.service.nodePorts.https=30443 --wait
```

Generate an Ingress first draft and inspect the rule it creates:

```bash
kubectl create ingress microshop \
  -n microshop \
  --class=nginx \
  --rule='microshop.local/*=storefront:80' \
  --dry-run=client -o yaml > k8s/base/ingress.yaml
```

Add it to `kustomization.yaml`. First prove ordinary HTTP through
`http://microshop.local:8080` using `curl --resolve`.

Then create a short-lived certificate:

```bash
mkdir -p generated
openssl req -x509 -nodes -newkey rsa:2048 -days 7 -keyout generated/microshop.key -out generated/microshop.crt -subj '/CN=microshop.local' -addext 'subjectAltName=DNS:microshop.local'
kubectl create secret tls microshop-tls -n microshop --cert=generated/microshop.crt --key=generated/microshop.key
```

Add the TLS host and Secret reference to the Ingress. Verify identity and trust
without `-k`:

```bash
curl --resolve microshop.local:8443:127.0.0.1 --cacert generated/microshop.crt https://microshop.local:8443/products
```

## Add one narrow permission

Generate a ServiceAccount, namespaced Role, and RoleBinding as separate YAML
files:

```bash
kubectl create serviceaccount storefront \
  -n microshop \
  --dry-run=client -o yaml > k8s/base/serviceaccount.yaml

kubectl create role storefront-config-reader \
  -n microshop \
  --verb=get,list \
  --resource=configmaps \
  --dry-run=client -o yaml > k8s/base/role.yaml

kubectl create rolebinding storefront-config-reader \
  -n microshop \
  --role=storefront-config-reader \
  --serviceaccount=microshop:storefront \
  --dry-run=client -o yaml > k8s/base/rolebinding.yaml
```

Add them to `kustomization.yaml` and run Storefront under that ServiceAccount.

Prove both sides of least privilege:

```bash
kubectl auth can-i get configmaps -n microshop --as=system:serviceaccount:microshop:storefront
kubectl auth can-i delete secrets -n microshop --as=system:serviceaccount:microshop:storefront
```

The first result should be yes and the second no. Do not use `cluster-admin` to
make the first check pass.

NetworkPolicy is not part of the default Kind path today. Kind's basic network
does not enforce it by itself, and adding another network provider would turn
this into a networking-tool installation class. We will practise the supplied
policy on the course environment where enforcement is already configured.

## Only now does Helm solve a problem we actually have

We have three Deployments, three Services, shared configuration, and repeated
labels, probes, resources, and environment differences. That repetition is the
reason to introduce the chart under `chart/microshop/`.

In a fresh project, `helm create microshop` can generate a conventional chart.
This repository already contains the smaller `chart/microshop/` scaffold so we
do not spend class deleting unrelated example templates.

Move one proven resource into a template at a time. Keep the structure in the
template and move only genuine environment differences into `values.yaml`.

After each template:

```bash
helm lint chart/microshop
helm template microshop chart/microshop -n microshop
```

Before installation, read the rendered YAML. Predict which objects will change.
Then install or upgrade and inspect both Helm and Kubernetes:

```bash
helm upgrade --install microshop chart/microshop -n microshop
helm get values microshop -n microshop --all
helm get manifest microshop -n microshop
helm history microshop -n microshop
kubectl get deployment,pod,service,endpointslice -n microshop
```

Change one value, render again, predict the result, and perform an upgrade. This
is the Session 5 rhythm in a system the class has now built and diagnosed:

```text
render -> predict -> mutate -> prove
```

## Close with one incident

Choose one failure from the work above: empty endpoints, Pending placement,
failed readiness, lost data, wrong Ingress backend, or denied authorization.

Write the investigation in `INCIDENT_NOTES.md`:

```text
symptom -> hypothesis -> evidence -> narrow -> change -> verify
```

The final state is not enough. Keep the Event, log, condition, EndpointSlice,
authorization result, or request output that explains why the repair was right.

## When the session is over

Check the target before removing it:

```bash
kind get clusters
kind delete cluster --name microshop
```
