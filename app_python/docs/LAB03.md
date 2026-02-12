# Lab 3: Unit Testing for FastAPI Application
## Testing Framework Selection

1. Chosen Framework: pytest
Justification:
- pytest was selected over unittest due to:
- Minimal boilerplate (simple assert statements)
- Native support for fixtures and dependency injection
- Excellent integration with FastAPI via TestClient
- Powerful ecosystem (pytest-cov, monkeypatch, parametrization)
- Industry-standard for modern Python projects

This aligns with production-grade testing practices and CI/CD pipelines.

2. Test Structure
```bash
app_python/
└── tests/
    ├── conftest.py         # Shared test fixtures
    ├── test_root.py       # Tests for GET /
    ├── test_health.py     # Tests for GET /health
    └── test_errors.py     # Error handling tests (404, 500)
```
- conftest.py defines a reusable FastAPI TestClient fixture.
- Each endpoint has a dedicated test file for isolation and clarity.
- Tests validate both successful responses and error cases.

3. Tested Endpoints & Coverage
### GET /

Validated:
- HTTP status code = 200
- Presence of required top-level fields:
    - service, system, runtime, request, endpoints
- Correct service metadata values
- System info field types (hostname, platform, cpu_count, etc.)
- Runtime timestamps format and timezone
- Request metadata (method, path, user-agent, client_ip)
- Endpoints list structure

### GET /health

Validated:
- HTTP status code = 200
- Health status = "healthy"
- Timestamp format (UTC, ISO8601)
- Service name and version correctness
- Uptime field presence and type
### Error Handling
- 404 Not Found:
  - Custom error response structure
  - Correct path returned
- 500 Internal Server Error:
  - Simulated failure via monkeypatch
  - Verified error response and HTTPException behavior


4. How to Run Tests Locally
Install dependencies:
```bash
pip install -r requirements-dev.txt
```

Run all tests:
```bash
pytest -v
```

Run with coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

Run a single test file:
```bash
pytest tests/test_root.py -v
```

Terminal Output (All Tests Passing)
test_root.py:
```bash
tests/test_root.py::test_root_status_code PASSED
tests/test_root.py::test_root_json_structure PASSED
tests/test_root.py::test_root_service_fields PASSED
tests/test_root.py::test_root_system_fields PASSED
tests/test_root.py::test_root_runtime_fields PASSED
tests/test_root.py::test_root_request_metadata PASSED
tests/test_root.py::test_root_endpoints_list PASSED

test_health.py:
tests/test_health.py::test_health_status_code PASSED
tests/test_health.py::test_health_response_structure PASSED

test_errors.py:
tests/test_errors.py::test_internal_server_error PASSED
tests/test_errors.py::test_404_handler PASSED

Final Summary:
============================== 11 passed in 0.17s ==============================
```

