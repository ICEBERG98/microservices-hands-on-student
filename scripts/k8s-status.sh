#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-microshop}"
kubectl get deployment,pod,service,pvc -n "$NAMESPACE" -o wide
kubectl get endpointslice -n "$NAMESPACE"
kubectl get events -n "$NAMESPACE" --sort-by=.lastTimestamp | tail -n 20
