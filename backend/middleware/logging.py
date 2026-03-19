import time
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
logger = logging.getLogger("spoken_social")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        status_code = 500
        error_message = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            duration_ms = round((time.time() - start) * 1000, 2)
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "method": request.method,
                "path": str(request.url.path),
                "query": str(request.url.query) if request.url.query else None,
                "status": status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            }

            if error_message:
                log_entry["error"] = error_message

            # Skip /metrics endpoint to avoid log noise
            if not log_entry["path"].endswith("/metrics"):
                logger.info(json.dumps(log_entry))
        return response
