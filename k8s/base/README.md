# Kubernetes build order

Create these manifests during the Kubernetes part of the session:

1. `namespace.yaml`
2. `config.yaml`
3. `catalog.yaml` - Deployment and Service
4. `orders.yaml` - PVC, Deployment, and Service
5. `storefront.yaml` - Deployment and Service

Add each filename to `kustomization.yaml`, then render before applying:

```bash
kubectl kustomize k8s/base
```
