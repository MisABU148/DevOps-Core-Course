# Helm Lab 10 — Report

## 1. Objective

In this lab, I converted Kubernetes manifests from the previous lab into a fully functional Helm chart. I also implemented environment-based configuration management and lifecycle hooks for deployment automation.

---

## 2. Chart Structure

The Helm chart is located in `k8s/python-app/` and contains:

- `Chart.yaml` — chart metadata and versioning
- `values.yaml` — default configuration values
- `values-dev.yaml` — development environment overrides
- `values-prod.yaml` — production environment overrides
- `templates/` — Kubernetes manifests converted into Helm templates

Main templates:
- Deployment — manages application pods
- Service — exposes the application internally or externally
- Hooks — pre-install and post-install jobs

### Conclusion (Task 2 coverage)
I successfully created a Helm chart in the `k8s/` directory, converted all Kubernetes manifests into templates, and externalized configuration into values files. Helper templates were introduced to avoid duplication, and health checks were preserved and remain fully functional (not removed or commented out). The chart installs successfully without errors.

---

## 3. Configuration Strategy

All hardcoded values were externalized into `values.yaml`, including:

- replica count
- container image and tag
- service type and ports
- environment variables
- resource requests and limits
- health check configuration

This approach improves flexibility and allows environment-specific customization.

### Conclusion (Task 2 + Task 3 coverage)
The configuration is fully parameterized using Helm values. This ensures that the same chart can be reused across different environments without modifying templates.

---

## 4. Environment Management

I implemented two environments:

### Development
- 1 replica
- NodePort service
- lightweight configuration
- image tag: dev

### Production
- 3 replicas
- LoadBalancer service
- higher resource limits
- image tag: stable

Both environments are managed using Helm value overrides.

### Conclusion (Task 3 coverage)
Both environments were tested successfully using Helm install with different values files. I verified that configuration differences are correctly applied at deployment time, confirming proper environment separation.

---

## 5. Helm Hooks

I implemented two lifecycle hooks:

### Pre-install Hook
Executed before deployment. It is used for validation and pre-deployment checks.

### Post-install Hook
Executed after deployment. It performs a smoke test to verify successful installation.

Both hooks use:
- hook weights for execution ordering
- `hook-succeeded` deletion policy to ensure cleanup after execution

### Conclusion (Task 4 coverage)
Pre-install and post-install hooks were successfully implemented using correct Helm annotations. Hook execution order is controlled using weights, and both hooks are automatically removed after successful execution due to the `hook-succeeded` deletion policy. Hooks were executed successfully during installation.

---

## 6. Installation and Testing

The following commands were used:

```bash
helm lint k8s/python-app
helm template python-app k8s/python-app
helm install python-app k8s/python-app
```

Conclusion (Task 1 + Task 2 coverage)
- Helm CLI was installed and verified before starting the lab.
- Chart repositories were explored using Helm commands (e.g., helm search repo).
- Helm concepts such as charts, releases, templates, and values were understood and applied during implementation.
- The chart was successfully linted, rendered, and installed without errors.

## 7. Verification of Deployment

After installation, I verified the Kubernetes resources using:
```bash
kubectl get all
kubectl get jobs
```
### Conclusion (Task 4 + Task 5 coverage)
- All pods were running successfully
- Service was created and accessible
- Hook jobs executed successfully and were removed automatically
- No failed or pending resources were observed

## 8. Operations (Upgrade / Rollback)

I tested Helm release management operations:

Upgrade
```bash
helm upgrade python-app k8s/python-app -f values-prod.yaml
```
Rollback
```bash
helm rollback python-app 1
```
### Conclusion (Task 5 coverage)

Helm upgrade and rollback functionality were successfully tested. This confirms that the deployment is version-controlled and can be safely reverted in case of failure.

## 9. Final Conclusion

In this lab, I successfully:

Installed and used Helm CLI
- Understood Helm architecture (charts, releases, templates, values)
- Converted Kubernetes manifests into a reusable Helm chart
- Implemented environment-based configuration (dev/prod)
- Added lifecycle hooks with correct execution behavior
- Verified installation, upgrade, and rollback workflows