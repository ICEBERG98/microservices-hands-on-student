# Student lab checklist

## Rule for every change

```text
render -> predict -> apply -> observe -> verify
```

## Workload

- [ ] Runtime configuration comes from a ConfigMap; secrets are never printed.
- [ ] Startup, readiness, and liveness probes serve different purposes.
- [ ] Requests and limits are visible and defensible.
- [ ] Orders data survives replacement of the Orders Pod.

## Scheduling and disruption

- [ ] Pod placement is explained using conditions and Events.
- [ ] A placement constraint is deliberate and achievable.
- [ ] Disruption settings match the replica count and cluster topology.

## Traffic

- [ ] Every Service selector matches the intended Pod labels.
- [ ] Service port, `targetPort`, and listener port align.
- [ ] EndpointSlices contain only Ready backends.
- [ ] The HTTPS hostname reaches Storefront with trust verification enabled.

## Security

- [ ] Workloads use the intended ServiceAccount.
- [ ] The required API action is allowed and a broader action is denied.
- [ ] The approved network path succeeds and an unrelated client is blocked.

## Helm

- [ ] The chart lints and renders before installation.
- [ ] Environment differences are values, not copied templates.
- [ ] Release history shows the install and upgrade.

## Incident record

- [ ] Symptom
- [ ] Hypothesis
- [ ] Evidence
- [ ] What was ruled in or out
- [ ] Smallest repair
- [ ] Original test repeated
- [ ] Negative test repeated
