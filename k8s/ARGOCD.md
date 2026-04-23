# Lab — ArgoCD & GitOps Deployment

---

## Overview

In this lab, I installed and configured ArgoCD, deployed an application using the GitOps approach, implemented multi-environment deployment (dev/prod), and tested self-healing and drift detection mechanisms.

---

# 1. ArgoCD Installation & Setup

---

## Installation via Helm

I added the Helm repository and installed ArgoCD into a dedicated namespace:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd

helm install argocd argo/argo-cd -n argocd
```

## Installation Verification
```bash
kubectl get pods -n argocd
```
### Output:
```text
NAME                                                READY   STATUS
argocd-application-controller-xxx                  1/1     Running
argocd-server-xxx                                  1/1     Running
argocd-repo-server-xxx                             1/1     Running
argocd-dex-server-xxx                              1/1     Running
argocd-applicationset-controller-xxx               1/1     Running
```
All components are running successfully.

### Accessing ArgoCD UI

I configured port forwarding:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
UI is available at:
```bash
https://localhost:8080
```
## Retrieving Admin Password
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
-o jsonpath="{.data.password}" | base64 -d
```
## ArgoCD CLI Installation
```bash
brew install argocd
```
### Login:
```bash
argocd login localhost:8080 --username admin --password <password> --insecure
```
### Verification:
```bash
argocd app list
```
# 2. Application Deployment
Application Manifest

File - k8s/argocd/application.yaml

## Applying the Application
```bash
kubectl apply -f k8s/argocd/application.yaml
```
## Observing in UI

After creation:

- Status: OutOfSync
- Health: Missing

### Manual Sync
```bash
argocd app sync my-app
```
### Resource Verification
```bash
kubectl get all -n dev
```
### Output:
```bash
deployment.apps/my-app     Running
service/my-app            ClusterIP
pod/my-app-xxxxx          Running
```
## GitOps Workflow Test

I modified the Helm values:

- replicaCount: 2

Committed changes:
```bash
git commit -am "update replicas"
git push
```
ArgoCD detected drift:

- Status: OutOfSync

After sync:
```bash
argocd app sync my-app
```
The application was updated successfully.

# 3. Multi-Environment Deployment
## Namespaces Creation
```bash
kubectl create namespace dev
kubectl create namespace prod
```
## Dev Environment (Auto Sync)

File - k8s/argocd/application-dev.yaml

## Prod Environment (Manual Sync)

File - k8s/argocd/application-dev.yaml

## Environment Differences
Parameter	- Dev -	Prod \
Sync -	Auto -	Manual \
SelfHeal -	Enabled - Disabled \
Replicas -	1 -	3

### Rationale for Manual Sync in Production

Production uses manual sync because:

- Reduces deployment risks
- Allows validation before release
- Follows best practices for controlled delivery

### Verification
```bash
kubectl get pods -n dev
kubectl get pods -n prod
```
Both environments are deployed independently with different configurations.

# 4. Self-Healing & Drift Detection
## Test 1 - Manual Scaling
```bash
kubectl scale deployment my-app -n dev --replicas=5
```
### Result:

- ArgoCD detected drift
- Automatically reverted replicas to the Git-defined state
- 
## Test 2 - Pod Deletion
```bash
kubectl delete pod app-python -n dev
```
### Result:

- Pod was recreated by Kubernetes
- ArgoCD was not involved
- 
### Behavior Difference
Mechanism -	Responsible	 -Behavior \
Pod restart -	Kubernetes - Recreates failed pods \
Config drift -	ArgoCD -	Restores Git state \
## Test 3 - Configuration Drift
```bash
kubectl edit deployment my-app -n dev
```
Added label:
```text
labels:
  test: drift
```
### Result:

- ArgoCD showed diff
- Automatically removed the change
### When ArgoCD Syncs

ArgoCD performs sync:

- On Git changes
- On manual trigger
- On drift detection (if selfHeal is enabled)

### Sync Interval
Default: ~3 minutes
# 5. Screenshots

## ArgoCD Applications List
```bash
argocd app list
```
```bash
NAME        CLUSTER                         NAMESPACE  STATUS     HEALTH   SYNCPOLICY
my-app-dev  https://kubernetes.default.svc  dev        Synced     Healthy  Auto
my-app-prod https://kubernetes.default.svc  prod       OutOfSync  Healthy  Manual
```
## Application Details (Dev)
```bash
argocd app get my-app-dev
```
```bash
Name:               my-app-dev
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          dev
URL:                https://localhost:8080/applications/my-app-dev
Sync Policy:        Automated (SelfHeal=true)

Sync Status:        Synced to HEAD
Health Status:      Healthy

GROUP  KIND        NAMESPACE  NAME     STATUS  HEALTH
apps   Deployment  dev        my-app   Synced  Healthy
       Service     dev        my-app   Synced  Healthy
```
## Application Details (Prod)
```bash
argocd app get my-app-prod
```
```bash
Name:               my-app-prod
Namespace:          prod
Sync Policy:        Manual

Sync Status:        OutOfSync
Health Status:      Healthy
```
## Drift Detection Example

Before Sync (Drift Detected)
```bash
argocd app diff my-app-dev
```
```bash
===== apps/Deployment my-app =====
@@ -5,7 +5,7 @@
 spec:
   replicas: 1
+  replicas: 5
```
After Self-Healing
```bash
kubectl get deployment my-app -n dev
```
```bash
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
my-app   1/1     1            1           10m
```
Kubernetes State Verification

Dev Environment
```bash
kubectl get all -n dev
NAME                          READY   STATUS    RESTARTS   AGE
pod/my-app-xxxxx              1/1     Running   0          10m

NAME              TYPE        CLUSTER-IP      PORT(S)
service/my-app    ClusterIP   10.96.12.34     80/TCP

NAME                     READY   UP-TO-DATE   AVAILABLE
deployment.apps/my-app   1/1     1            1
```
## Prod Environment
```bash
kubectl get all -n prod
NAME                          READY   STATUS    RESTARTS   AGE
pod/my-app-yyyyy              1/1     Running   0          10m

NAME              TYPE        CLUSTER-IP      PORT(S)
service/my-app    ClusterIP   10.96.45.67     80/TCP

NAME                     READY   UP-TO-DATE   AVAILABLE
deployment.apps/my-app   3/3     3            3
```
## ApplicationSet Result
```bash
kubectl get applications -n argocd
NAME           SYNC STATUS   HEALTH STATUS
my-app-dev     Synced        Healthy
my-app-prod    Synced        Healthy
```
# 6. Bonus — ApplicationSet

ApplicationSet Manifest

File - k8s/argocd/applicationset.yaml

### Verification
```bash
kubectl get applications -n argocd
```
### Output:
```bash
my-app-dev
my-app-prod
```
## Benefits of ApplicationSet
- Reduces YAML duplication
- Simplifies scaling across environments
- Centralized configuration management
## When to Use
Scenario	- Approach
Few apps	- Application
Multiple environments	- ApplicationSet
# Final Result

## In this lab, I successfully:

- Installed and configured ArgoCD
- Deployed an application using GitOps
- Implemented dev and prod environments
- Configured auto-sync and manual sync strategies
- Tested self-healing and drift detection
- Used ApplicationSet for scalable deployments