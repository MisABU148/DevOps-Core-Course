# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Overview

In this lab, I implemented secure secret management in Kubernetes using both native Kubernetes Secrets and HashiCorp Vault integration. The main goal was to eliminate hardcoded sensitive data and ensure secure delivery of secrets to the application.

---

# Kubernetes Secrets Fundamentals

## Creating a Secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=supersecret
```

## Viewing the Secret

```bash
kubectl get secret app-credentials -o yaml
```

Output:

```yaml
data:
  username: YWRtaW4=
  password: c3VwZXJzZWNyZXQ=
```

## Decoding

```bash
echo YWRtaW4= | base64 --decode
# admin

echo c3VwZXJzZWNyZXQ= | base64 --decode
# supersecret
```

## Encoding vs Encryption

* Base64 is **encoding**, not encryption
* Data can be easily decoded
* It does not provide real security

## Security

* By default, Kubernetes Secrets are **NOT encrypted in etcd**
* It is necessary to enable **Encryption at Rest**

### etcd encryption

This is a mechanism for encrypting data stored in etcd. It is enabled via EncryptionConfiguration.

---

# Helm-Managed Secrets

## values.yaml

```yaml
secrets:
  username: "admin"
  password: "changeme"

resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "250m"
    memory: "256Mi"
```

## templates/secrets.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "app.fullname" . }}-secret
type: Opaque
data:
  username: {{ .Values.secrets.username | b64enc }}
  password: {{ .Values.secrets.password | b64enc }}
```

## Deployment (snippet)

```yaml
envFrom:
  - secretRef:
      name: {{ include "app.fullname" . }}-secret

resources:
  {{- toYaml .Values.resources | nindent 12 }}
```

## Verification

```bash
kubectl exec -it <pod> -- printenv | grep USERNAME
```

Secrets are available as environment variables but are not visible in `kubectl describe pod`.

## Requests vs Limits

* requests — guaranteed resources
* limits — maximum allowed resources

---

# HashiCorp Vault Integration

## Installing Vault

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault --set "server.dev.enabled=true"
```

```bash
kubectl get pods
```

All pods are in Running state.

## Vault Configuration

```bash
kubectl exec -it vault-0 -- sh

vault secrets enable -path=secret kv-v2
vault kv put secret/app username=admin password=supersecret
```

## Kubernetes Auth

```bash
vault auth enable kubernetes
```

### Policy

```hcl
path "secret/data/app" {
  capabilities = ["read"]
}
```

### Role

```bash
vault write auth/kubernetes/role/app-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=default \
  ttl=1h
```

## Vault Agent Injection

### Annotations in Deployment

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "app-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/app"
```

## Verification

```bash
kubectl exec -it <pod> -- ls /vault/secrets
```

Secrets are successfully mounted inside the container.

## Sidecar Pattern

Vault Agent runs as a sidecar container:

* retrieves secrets
* updates them
* stores them in a shared volume

---

# Documentation

## Comparison: Kubernetes Secrets vs Vault

| Criterion  | K8s Secrets | Vault      |
| ---------- | ----------- | ---------- |
| Encryption | optional    | built-in   |
| Rotation   | manual      | automatic  |
| Security   | basic       | high       |
| Use case   | simple apps | production |

## When to Use

* Kubernetes Secrets — for simple applications
* Vault — for production and sensitive data

## Recommendations

* Always enable encryption at rest
* Never store secrets in Git
* Use Vault for production

---

# Bonus — Vault Agent Templates

## Template Annotation

```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/app" -}}
  USERNAME={{ .Data.data.username }}
  PASSWORD={{ .Data.data.password }}
  {{- end }}
```

## Result

File inside the container:

```env
USERNAME=admin
PASSWORD=supersecret
```

## Dynamic Rotation

Vault Agent automatically updates secrets when they change.

## agent-inject-command

Allows executing a command after a secret update (e.g., restarting the application).

## _helpers.tpl

```yaml
{{- define "app.env" -}}
- name: USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "app.fullname" . }}-secret
      key: username
{{- end }}
```

## DRY

Using include helps avoid code duplication.

---

# Summary

I implemented:

* Kubernetes Secrets
* Helm integration
* HashiCorp Vault
* Vault Agent Injection
* Template rendering
