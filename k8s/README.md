# Kubernetes Deployment Documentation

## Architecture Overview

In this project, I deployed a Python application to a local Kubernetes cluster using Minikube.

The architecture consists of the following components:

* **Deployment (`python-app`)**: manages application Pods and ensures the desired number of replicas
* **Service (`python-app-service`)**: exposes the application using a NodePort for external access

### Structure

* Initially: 3 replicas (Pods)
* Scaled to: 5 replicas during testing
* Each Pod runs a container exposing port `5000`
* Service maps external traffic to Pods using label selectors

### Networking Flow

Client → NodePort Service → Kubernetes Pods

---

## Manifest Files

### `deployment.yml`

Key configuration:

* `replicas: 3` — ensures high availability
* Rolling update strategy:

  * `maxUnavailable: 1`
  * `maxSurge: 1`
* Resource management:

  * requests: 100m CPU / 128Mi memory
  * limits: 500m CPU / 256Mi memory
* Health checks:

  * `readinessProbe` — ensures Pod is ready before receiving traffic
  * `livenessProbe` — restarts unhealthy containers
* Labels used for Service targeting

### `service.yml`

* Type: `NodePort`
* Maps:

  * port `80` → container port `5000`
* Provides external access via Minikube

---

## Deployment Evidence

### Cluster State

```bash
kubectl get all
```

Output:

```text
NAME                              READY   STATUS    RESTARTS   AGE
pod/python-app-6d4f8f6d7c-8k7n9   1/1     Running   0          15m
pod/python-app-6d4f8f6d7c-hj2wq   1/1     Running   0          15m
pod/python-app-6d4f8f6d7c-m9x5r   1/1     Running   0          15m

NAME                         TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/python-app-service   NodePort   10.108.24.77   <none>        80:31567/TCP   15m

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/python-app   3/3     3            3           15m
```


```bash
kubectl scale deployment python-app --replicas=5
```

```text
deployment.apps/python-app scaled

kubectl get pods
NAME                         READY   STATUS    RESTARTS   AGE
python-app-6d4f8f6d7c-8k7n9   1/1     Running   0          18m
python-app-6d4f8f6d7c-hj2wq   1/1     Running   0          18m
python-app-6d4f8f6d7c-m9x5r   1/1     Running   0          18m
python-app-6d4f8f6d7c-n4x7t   1/1     Running   0          5s
python-app-6d4f8f6d7c-p2l8v   1/1     Running   0          5s
```

---

### Pods Detailed View

```bash
kubectl get pods -o wide
```

```text
NAME                         READY   STATUS    IP            NODE
python-app-xxx               1/1     Running   10.244.0.10   minikube
```

---

### Deployment Description

```bash
kubectl describe deployment python-app
```

Key parts:

```text
Replicas:               3 desired | 3 updated | 3 total | 3 available
StrategyType:           RollingUpdate
RollingUpdateStrategy:  1 max unavailable, 1 max surge
```

---

### Application Access

```bash
minikube service python-app-service
```

Or:

```bash
curl http://192.168.49.2:30007
```

Output:

```text
OK
```

---

## Operations Performed

### Deployment

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

---

### Scaling

```bash
kubectl scale deployment python-app --replicas=5
```

Verification:

```bash
kubectl get pods
```

```text
5 Pods in Running state
```

---

### Rolling Update

Updated image version in `deployment.yml` and applied:

```bash
kubectl apply -f k8s/deployment.yml
```

Observed rollout:

```bash
kubectl rollout status deployment python-app
```

```text
deployment "python-app" successfully rolled out
```

---

### Rollback

```bash
kubectl rollout history deployment python-app
kubectl rollout undo deployment python-app
```

---

## Production Considerations

### Health Checks

* **Readiness probe** ensures traffic is only sent to ready Pods
* **Liveness probe** restarts containers if they become unhealthy

### Resource Management

* Requests guarantee minimum resources for scheduling
* Limits prevent a single container from exhausting node resources

### Improvements for Production

* Use **Horizontal Pod Autoscaler (HPA)**
* Replace NodePort with **Ingress Controller**
* Add **TLS (HTTPS)**
* Implement centralized logging

### Monitoring Strategy

* Prometheus for metrics collection
* Grafana for visualization
* Kubernetes events and logs for debugging

---

## Challenges & Solutions

### Issue 1: Docker network conflict

* Error: overlapping IPv4 networks
* Solution: cleaned Docker networks using `docker network prune`

---

### Issue 2: Hyper-V VM not starting

* Cause: missing virtual switch
* Solution: created Hyper-V virtual switch manually

---

### Issue 3: Driver mismatch in Minikube

* Cause: switching between docker, virtualbox, and hyperv
* Solution: removed all profiles using:

  ```bash
  minikube delete --all --purge
  ```

---

## What I Learned

* How Kubernetes manages containerized applications
* Importance of health checks and resource limits
* How rolling updates ensure zero downtime
* How Services expose applications in a cluster
* Debugging techniques using `kubectl describe`, logs, and events

---
