"""Authentication middleware for FastAPI application."""

import logging
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import decode_token

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""

    def __init__(self, app, exclude_paths: list[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/",
            "/api/v1/auth/login",
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request and validate JWT token."""
        path = request.url.path

        # Skip authentication for excluded paths
        if path in self.exclude_paths or request.method == "OPTIONS":
            return await call_next(request)

        # Extract Authorization header
        authorization = request.headers.get("Authorization") or request.headers.get("authorization")

        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"}
            )

        # Extract token from "Bearer <token>"
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"}
            )

        # Validate token
        try:
            payload = decode_token(token)
            request.state.user = payload
            request.state.token = token
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Authentication failed: {str(e)}"}
            )

        return await call_next(request)

