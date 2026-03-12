# LAB07 — Logging and Monitoring with Loki, Promtail, and Grafana

## 1. Architecture

In this lab, I deployed a logging stack consisting of **Loki, Promtail, Grafana**, and my Python application.

- **Promtail** collects logs from Docker containers using label discovery (`app`).
- **Loki** stores logs in TSDB with a 7-day retention period.
- **Grafana** visualizes logs and provides dashboards.
- My **Python app** emits structured JSON logs.

**Diagram:**
```
[Python App] ---> [Promtail] ---> [Loki] ---> [Grafana]
[Other Apps] ---^
```

Ports:

- Loki: 3100
- Promtail: 9080
- Grafana: 3000

**Screenshots:**  
`monitoring/docs/screenshots/loki.png`
`monitoring/docs/screenshots/grafana.png`
`monitoring/docs/screenshots/promtail.png`

---

## 2. Setup Guide

**Deployment steps:**

1. Clone the repository and navigate to the monitoring folder:

```cmd
cd monitoring
```
Start the stack:
```cmd
docker compose up -d
```

Check the status of services:
```cmd
docker compose ps
```

Verify Loki readiness:
```cmd
curl http://localhost:3100/ready
```
Verify Promtail targets:
```cmd
curl http://localhost:9080/targets
```
Open Grafana in your browser:

http://localhost:3000

Log in with admin credentials from .env.

## 3. Configuration

Loki (loki/config.yml)
- Storage: TSDB on filesystem
- Schema: v13
- Retention: 7 days

```cmd
storage_config:
  boltdb:
    directory: /loki/index
schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 168h
```
Promtail (promtail/config.yml)
- Docker service discovery
- Relabeling to extract container labels:
```amd
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: npipe:////./pipe/docker_engine
        refresh_interval: 10s
    relabel_configs:
      - source_labels: [__meta_docker_container_label_app]
        target_label: app
```
Explanation:
- Promtail automatically discovers all containers with the app label.
- Relabeling ensures each log line has an app label for filtering in Grafana.

## 4. Application Logging

I implemented structured JSON logging in my Python app:
```cmd
logger.info({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "level": "INFO",
    "message": "HTTP request",
    "method": request.method,
    "path": request.url.path,
    "status_code": 200,
    "client_ip": client_ip
})
```
- Logs include timestamp, level, HTTP method, path, status code, and client IP.
- ERROR logs are generated through the global exception handler:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
```
## 5. Dashboard

### Grafana Panels:

1. Logs Table
   - Query: {app=~"devops-.*"}
   - Displays recent logs from all applications.
   - Screenshot: monitoring/docs/screenshots/logs_table.png

2. Request Rate
    - Query: sum by (app) (rate({app=~"devops-.*"}[1m]))
    - Shows the number of logs per second per app.
    - Screenshot: monitoring/docs/screenshots/request_rate.png

3. Error Logs

    - Query: {app=~"devops-.*"} | json | level="ERROR"

    - Displays only logs with level ERROR.

    - Screenshot: monitoring/docs/screenshots/error_logs.png

4. Log Level Distribution

    - Query: sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))

   - Shows distribution of logs by level (INFO, ERROR, etc.).

   - Screenshot: monitoring/docs/screenshots/log_level_distribution.png

## 6. Production Config

Resource limits for all services:
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```
Grafana Security:

- Anonymous login disabled: GF_AUTH_ANONYMOUS_ENABLED=false

- Admin credentials stored in .env (not committed)

Log Retention:

- Loki stores logs for 7 days.

Healthchecks:

- Loki: http://localhost:3100/ready

- Grafana: http://localhost:3000/api/health

- Promtail: http://localhost:9080/targets

- Python-app: http://localhost:5000/health

## 7. Testing

Generating logs:
```cmd
for /L %i in (1,1,20) do curl http://localhost:8000/
for /L %i in (1,1,20) do curl http://localhost:8000/health
for /L %i in (1,1,5) do curl http://localhost:8000/error-test
```
Verifying services:
```cmd
docker compose ps
curl http://localhost:3100/ready
curl http://localhost:9080/targets
```
Example LogQL queries:
```text
{app="devops-python"}           # All Python app logs
{app="devops-python"} |= "ERROR" # Only error logs
{app="devops-python"} | json | method="GET" # Filter JSON logs by HTTP method
```
## 8. Challenges

1. Windows vs Unix socket — Promtail required npipe:////./pipe/docker_engine for Docker discovery.

2. Error logs initially empty — needed a dedicated /error-test endpoint to trigger real exceptions.

3. Production readiness — added resource limits, healthchecks, and Grafana security via .env.

Note: All screenshots are stored in monitoring/docs/screenshots/.