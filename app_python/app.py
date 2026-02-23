import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = FastAPI(
    title="DevOps Info Service",
    description="Service information and system monitoring API",
    version="1.0.0"
)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist',
            'path': request.url.path
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            'error': 'Validation Error',
            'message': 'Invalid request parameters',
            'details': exc.errors()
        }
    )

start_time = datetime.now()

hostname = socket.gethostname()
platform_name = platform.system()
platform_version = platform.release()
architecture = platform.machine()
cpu_count = os.cpu_count() or 0
python_version = platform.python_version()


def get_uptime() -> Dict[str, str]:
    """Calculate service uptime"""
    try:
        delta = datetime.now() - start_time
        seconds = int(delta.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        return {
            'seconds': seconds,
            'human': f"{hours} hour{'s' if hours != 1 else ''}, "
                     f"{minutes} minute{'s' if minutes != 1 else ''}"
        }
    except Exception as e:
        logger.error(f"Error calculating uptime: {e}")
        return {'seconds': 0, 'human': 'unknown'}


@app.get("/", response_class=JSONResponse)
async def get_service_info(request: Request):
    """
    Main endpoint - returns comprehensive service and system information
    """
    try:
        # Получаем информацию о запросе
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get('user-agent', 'unknown')

        uptime = get_uptime()

        response = {
            "service": {
                "name": "devops-info-service",
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "FastAPI"
            },
            "system": {
                "hostname": hostname,
                "platform": platform_name,
                "platform_version": platform_version,
                "architecture": architecture,
                "cpu_count": cpu_count,
                "python_version": python_version
            },
            "runtime": {
                "uptime_seconds": uptime['seconds'],
                "uptime_human": uptime['human'],
                "current_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "timezone": "UTC"
            },
            "request": {
                "client_ip": client_ip,
                "user_agent": user_agent,
                "method": request.method,
                "path": request.url.path
            },
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Health check"},
                {"path": "/docs", "method": "GET", "description": "Swagger documentation"},
                {"path": "/redoc", "method": "GET", "description": "ReDoc documentation"}
            ]
        }

        logger.info(f"GET / request from {client_ip}")
        return response

    except Exception as e:
        logger.error(f"Error in main endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Health check endpoint for monitoring and Kubernetes probes
    """
    try:
        uptime = get_uptime()

        response = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "uptime_seconds": uptime['seconds'],
            "service": "devops-info-service",
            "version": "1.0.0"
        }

        logger.debug("Health check executed")
        return response

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")

    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )