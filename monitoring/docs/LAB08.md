# DevOps Monitoring Stack Documentation

## 1. Architecture Overview

### System Architecture Diagram

The system is built on Prometheus **pull model**: the Python application exposes metrics via the `/metrics` endpoint, from which Prometheus scrapes them every 15 seconds, stores them in TSDB with 15-day retention, and forwards them to Grafana for visualization. Logs are collected through the Promtail → Loki pipeline, and all components run in an isolated Docker network with persistent volumes to ensure data survives restarts.

### Data Flow
1. **Python Application** exposes metrics at `/metrics` endpoint
2. **Prometheus** scrapes metrics every 15s (pull model)
3. **Prometheus** stores data with 15-day retention
4. **Grafana** queries Prometheus for visualization
5. **Loki** collects logs via Promtail
6. **Persistent volumes** ensure data survives restarts

## 2. Application Instrumentation

### Metrics Added

```python
# metrics.py

from prometheus_client import Counter, Histogram, Gauge

# 1. HTTP Request Counter (RED Method - Rate)
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)
"""
Purpose: Track total request volume
Labels: method (GET/POST), endpoint (/api/users), status_code (200/404/500)
Use Case: Rate calculation, error rate monitoring
"""

# 2. Request Duration Histogram (RED Method - Duration)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)
"""
Purpose: Measure response times
Buckets: 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0
Use Case: SLO monitoring, performance analysis
"""

# 3. Active Requests Gauge (RED Method - Errors)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress"
)
"""
Purpose: Track concurrent requests
Use Case: Load monitoring, capacity planning
"""

# 4. Endpoint Popularity Counter
endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'Endpoint calls',
    ['endpoint']
)
"""
Purpose: Track feature usage
Use Case: Business analytics, usage patterns
"""

# 5. System Info Collection Duration
system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'System info collection time in seconds'
)
"""
Purpose: Measure internal operation performance
Use Case: Performance optimization, bottleneck detection
"""
```
### Instrumentation Code (Middleware)
```python
@app.middleware("http")
async def instrument_requests(request: Request, call_next):
    # Track active requests
    http_requests_in_progress.inc()
    
    endpoint = normalize_endpoint(request.url.path)
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response
    finally:
        http_requests_in_progress.dec()
```
Why These Metrics?
RED Method (Rate, Errors, Duration) - Industry standard for request-based services

USE Method (Utilization, Saturation, Errors) - For resource monitoring

Business Metrics - Track feature adoption and performance

## 3. Prometheus Configuration
prometheus.yml
```yaml
global:
  scrape_interval: 15s      # How often to scrape targets
  evaluation_interval: 15s  # How often to evaluate rules
  external_labels:
    monitor: "devops-monitor"
    environment: "production"

scrape_configs:
  # Prometheus itself
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
        labels:
          service: "prometheus"
          component: "monitoring"

  # Python Application
  - job_name: "app"
    scrape_interval: 15s
    metrics_path: /metrics
    static_configs:
      - targets: ["python-app:5000"]
        labels:
          service: "devops-app"
          language: "python"
          tier: "application"

  # Loki
  - job_name: "loki"
    metrics_path: /metrics
    static_configs:
      - targets: ["loki:3100"]
        labels:
          service: "loki"
          component: "logging"

  # Grafana
  - job_name: "grafana"
    metrics_path: /metrics
    static_configs:
      - targets: ["grafana:3000"]
        labels:
          service: "grafana"
          component: "visualization"
```
Retention Configuration
```yaml
# Prometheus command line arguments
--storage.tsdb.retention.time=15d   # Keep data for 15 days
--storage.tsdb.retention.size=10GB  # Max storage size
--storage.tsdb.path=/prometheus      # Storage location
```
## 4. Dashboard Walkthrough
Dashboard Panels
Panel 1: Request Rate by Endpoint
```text
Query: sum(rate(http_requests_total[$__rate_interval])) by (endpoint)
Type: Time Series
Unit: req/s
Purpose: Monitor traffic patterns per endpoint
Threshold: Warning at >100 req/s
```
Panel 2: Error Rate (5xx)
```text
Query: sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (endpoint)
Type: Time Series
Unit: errors/s
Purpose: Track application errors
Threshold: Critical at >1 error/s
```
Panel 3: Request Duration (95th Percentile)
```text
Query: histogram_quantile(0.95, 
         sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
Type: Time Series
Unit: seconds
Purpose: Monitor user-perceived latency
SLO: p95 < 500ms
```
Panel 4: Active Requests
```text
Query: http_requests_in_progress
Type: Gauge/Stat
Unit: requests
Purpose: Track concurrent load
Threshold: Warning at >50 concurrent
```
Panel 5: Status Code Distribution
```text
Query: sum by (status_code) (rate(http_requests_total[5m]))
Type: Pie Chart
Purpose: Visualize success vs error ratio
```
Panel 6: Service Uptime
```text
Query: up{job="app"}
Type: Stat
Purpose: Service health monitoring
Alert: If value < 1 for 1m
```
### Dashboard Screenshots
at file /screenshots/lab08-task3-*

## 5. PromQL Examples
Query 1: Request Rate by Endpoint
```promql
# Show requests per second for each endpoint
sum(rate(http_requests_total[5m])) by (endpoint)
```
Explanation: Calculates per-second rate averaged over 5 minutes, grouped by endpoint. Essential for traffic analysis.

Query 2: 95th Percentile Latency
```promql
# Calculate p95 latency for each endpoint
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
```
Explanation: Shows the latency below which 95% of requests fall. Critical for SLO monitoring.

Query 3: Error Percentage
```promql
# Calculate error rate percentage
(sum(rate(http_requests_total{status_code=~"5.."}[5m])) 
 / sum(rate(http_requests_total[5m]))) * 100
```
Explanation: Computes the percentage of 5xx errors relative to total requests.

Query 4: Top 5 Slowest Endpoints
```promql
# Find endpoints with highest average latency
topk(5, 
  rate(http_request_duration_seconds_sum[5m]) 
  / rate(http_request_duration_seconds_count[5m])
)
```
Explanation: Identifies performance bottlenecks by showing endpoints with highest average response time.

Query 5: Daily Request Growth
```promql
# Compare today's requests with yesterday
sum(increase(http_requests_total[24h])) 
  / sum(increase(http_requests_total[24h] offset 24h))
```
Explanation: Shows day-over-day traffic growth for capacity planning.

## 6. Production Setup
Docker Compose Configuration
```yaml
# Resource Limits & Health Checks
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "wget --spider http://localhost:9090/-/healthy"]
      interval: 10s
      timeout: 5s
      retries: 5

  python-app:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  grafana:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  loki:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3100/ready"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  prometheus-data:
  loki_data:
  grafana_data:
```
Production Benefits
Feature	Implementation	Benefit
Health Checks	Every 10s	Automatic recovery, high availability
Resource Limits	CPU/Memory caps	Prevent resource starvation
Data Retention	15d / 10GB	Disk space management
Persistent Volumes	Docker volumes	Data survival on restart
Network Isolation	Dedicated network	Security, service discovery
## 7. Testing Results
Health Check Status
```bash
$ docker compose ps
NAME            STATUS
prometheus      Up (healthy)
loki            Up (healthy)
grafana         Up (healthy)
devops-python   Up (healthy)
promtail        Up (healthy)
```
✅ All services healthy

Resource Usage
```bash
$ docker stats --no-stream
CONTAINER      CPU %     MEM USAGE / LIMIT
prometheus     0.00%     62.54MiB / 1GiB
loki           0.72%     36.03MiB / 1GiB
grafana        3.99%     85.94MiB / 512MiB
devops-python  0.17%     40.23MiB / 256MiB
promtail       3.37%     15.37MiB / 512MiB
```
✅ Resource limits correctly applied

Retention Verification
```bash
$ docker exec prometheus cat /proc/1/cmdline
/bin/prometheus --storage.tsdb.retention.time=15d --storage.tsdb.retention.size=10GB
```
✅ Retention policies active

Persistence Test
```bash
# Before restart
$ docker volume ls | findstr monitoring
monitoring_grafana_data
monitoring_loki_data
monitoring_prometheus-data

# After restart
$ docker compose down && docker compose up -d
$ docker volume ls | findstr monitoring
# All volumes still exist!
```
✅ Data persistence confirmed

## 8. Challenges & Solutions
Challenge 1: Metrics Endpoint 404
Problem: Prometheus couldn't scrape /metrics endpoint
Solution: Added metrics endpoint to FastAPI app

```python
@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```
Challenge 2: Status Code Labels Missing
Problem: Error rate queries failed without status_code labels
Solution: Updated middleware to include status_code

```python
http_requests_total.labels(
    method=request.method,
    endpoint=endpoint,
    status_code=response.status_code  # Added
).inc()
```
Challenge 3: Container Networking
Problem: Prometheus couldn't resolve python-app:5000
Solution: Ensured all services on same network with correct service names

```yaml
networks:
  monitoring:
    driver: bridge
 ```   
Challenge 4: Uvicorn Binding to Localhost
Problem: App only listened on 127.0.0.1 inside container
Solution: Fixed Dockerfile CMD to bind to 0.0.0.0

```dockerfile
CMD uvicorn app:app --host 0.0.0.0 --port 5000
Challenge 5: Prometheus Retention Configuration
```
Problem: Retention flags not being passed correctly
Solution: Added flags to command in docker-compose.yml

```
yaml
command:
  - '--storage.tsdb.retention.time=15d'
  - '--storage.tsdb.retention.size=10GB'
```
## 9. Conclusion
The monitoring stack successfully implements:

✅ Complete metrics collection with RED method

✅ Prometheus scraping with 15s intervals

✅ Grafana dashboards with 6+ panels

✅ Production-ready health checks and limits

✅ Data persistence and retention policies

✅ Comprehensive error handling