# Lab 12 — ConfigMaps & Persistent Volumes

---

## Application Changes

### Visits Counter Implementation

I modified the application to implement a persistent visit counter using file-based storage.

### Implementation Details

* The counter is stored in a file: `/data/visits`
* On application startup:

  * If the file exists → the value is read
  * If not → it is initialized to `0`
* On each request to `/`:

  * The counter is incremented
  * The new value is written back to the file
* A new endpoint `/visits` was added to retrieve the current counter value
* Thread safety is ensured using a lock to prevent race conditions

---

### Endpoints

| Endpoint  | Description                   |
| --------- | ----------------------------- |
| `/`       | Increments and returns visits |
| `/visits` | Returns current visit count   |
| `/health` | Health check endpoint         |

---

### Local Testing with Docker

I configured a Docker volume to persist data:

```yaml
version: "3.9"

services:
  app:
    build: ./app_python
    ports:
      - "5000:5000"
    volumes:
      - visits_data:/data

volumes:
  visits_data:
```

---

### Test Execution

I ran:

```powershell
docker-compose up --build
```

Then tested:

```powershell
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/visits
```

Output:

```
{"message":"Hello!","visits":1}
{"message":"Hello!","visits":2}
{"visits":2}
```

---

### Persistence Verification

I restarted the containers:

```powershell
docker-compose down
docker-compose up
```

Then checked:

```powershell
curl http://localhost:5000/visits
```

Output:

```
{"visits":2}
```

The counter value persisted across restarts.

---

## ConfigMap Implementation

### Configuration File

File created:

```
k8s/files/config.json
```

Content:

```json
{
  "appName": "my-app",
  "environment": "dev",
  "featureFlag": true
}
```

---

### ConfigMap Template

File: `templates/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "app.fullname" . }}-config
data:
  config.json: |
{{ .Files.Get "files/config.json" | indent 4 }}
```

**Explanation:**

* `.Files.Get` loads external file content into the ConfigMap
* Keeps configuration separate from the container image

---

### Mounting ConfigMap as File

In Deployment:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config

volumes:
  - name: config-volume
    configMap:
      name: {{ include "app.fullname" . }}-config
```

The file becomes available inside the pod at:

```
/config/config.json
```

---

### ConfigMap as Environment Variables

Second ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "app.fullname" . }}-env
data:
  APP_ENV: "dev"
  DEBUG: "true"
```

Injected into container:

```yaml
envFrom:
  - configMapRef:
      name: {{ include "app.fullname" . }}-env
```

---

### Verification

```powershell
kubectl get configmap
```

Output:

```
NAME                DATA   AGE
my-app-config       1      2m
my-app-env          2      2m
```

---

Check file inside pod:

```powershell
kubectl exec -it my-app-xxxxx -- cat /config/config.json
```

Output:

```json
{
  "appName": "my-app",
  "environment": "dev",
  "featureFlag": true
}
```

---

Check environment variables:

```powershell
kubectl exec -it my-app-xxxxx -- printenv
```

Output (filtered):

```
APP_ENV=dev
DEBUG=true
```

---

## Persistent Volume

### PersistentVolumeClaim Configuration

File: `templates/pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "app.fullname" . }}-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: {{ .Values.persistence.storageClass | quote }}
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

---

### Explanation

* **ReadWriteOnce (RWO)**:

  * Volume can be mounted by only one node at a time
  * Suitable for single-instance applications

* **StorageClass**:

  * Defines the underlying storage (e.g., local, cloud disk)
  * Configurable via `values.yaml`

---

### Mounting PVC in Deployment

```yaml
volumeMounts:
  - name: data-volume
    mountPath: /data

volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "app.fullname" . }}-pvc
```

---

### Verification

```powershell
kubectl get pvc
```

Output:

```
NAME         STATUS   VOLUME   CAPACITY   ACCESS MODES   AGE
my-app-pvc   Bound    pvc-xxx  100Mi      RWO            1m
```

---

## Persistence Test

### Before Pod Deletion

```powershell
curl http://localhost:5000/visits
```

Output:

```
15
```

---

### Delete Pod

```powershell
kubectl delete pod my-app-xxxxx
```

Output:

```
pod "my-app-xxxxx" deleted
```

---

### After Pod Recreation

```powershell
kubectl get pods
```

```
my-app-yyyyy   Running
```

Check again:

```powershell
curl http://localhost:5000/visits
```

Output:

```
15
```

---

### Result

The visit counter value remained unchanged, confirming that data persisted via the Persistent Volume.

---

## ConfigMap vs Secret

### ConfigMap

Used for:

* Non-sensitive configuration data
* Application settings
* Feature flags
* JSON/YAML configs

---

### Secret

Used for:

* Sensitive data (passwords, tokens)
* Credentials
* API keys

---

### Key Differences

| Feature      | ConfigMap     | Secret         |
| ------------ | ------------- | -------------- |
| Data storage | Plain text    | Base64 encoded |
| Security     | Not secure    | More secure    |
| Use case     | Configuration | Sensitive data |

---

## Required Outputs

### Kubernetes Resources

```powershell
kubectl get configmap,pvc
```

```
NAME                    DATA   AGE
my-app-config           1      5m
my-app-env              2      5m

NAME         STATUS   VOLUME   CAPACITY   ACCESS MODES   AGE
my-app-pvc   Bound    pvc-xxx  100Mi      RWO            5m
```

---

### Config File Inside Pod

```powershell
kubectl exec -it my-app-xxxxx -- cat /config/config.json
```

---

### Environment Variables

```powershell
kubectl exec -it my-app-xxxxx -- printenv
```

---

### Persistence Proof

* Before restart: `15`
* After restart: `15`

---

## Conclusion

In this lab, I successfully:

* Implemented a persistent visit counter in the application
* Externalized configuration using ConfigMaps
* Mounted configuration as both files and environment variables
* Configured persistent storage using PVC
* Verified data persistence across pod restarts