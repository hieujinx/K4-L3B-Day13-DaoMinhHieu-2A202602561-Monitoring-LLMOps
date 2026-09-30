from __future__ import annotations

import time
import re
import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()
        requested_id = request.headers.get("x-request-id", "")
        correlation_id = (
            requested_id
            if re.fullmatch(r"req-[0-9a-fA-F]{8}", requested_id)
            else f"req-{secrets.token_hex(4)}"
        )
        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = (
                f"{(time.perf_counter() - start) * 1000:.2f}"
            )
            return response
        finally:
            clear_contextvars()
