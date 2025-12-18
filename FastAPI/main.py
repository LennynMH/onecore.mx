"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import LoggerMixin, setup_logging
from app.core.middleware import (
    general_exception_handler,
    http_exception_handler,
    request_logging_middleware,
    validation_exception_handler,
    AuthMiddleware,
)
from app.interfaces.api.routers import create_api_router
from app.interfaces.api.controllers.health_controller import router as health_router


class ApplicationManager(LoggerMixin):
    """Manager for FastAPI application with logging capabilities."""
    
    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        # Setup logging first
        setup_logging()
        
        self.log_info("Starting application initialization")
        
        # Modern lifespan handler
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            self.log_info(
                "Application started successfully",
                app_name=settings.app_name,
                version=settings.app_version,
                environment=settings.environment,
                debug=settings.debug
            )
            
            yield
            
            # Shutdown
            self.log_info("Application shutting down")

        app = FastAPI(
            title=settings.app_name,
            version=settings.app_version,
            debug=settings.debug,
            description="OneCore API - FastAPI application with JWT authentication, file upload, and SQL Server integration",
            docs_url="/docs" if settings.debug else None,
            redoc_url="/redoc" if settings.debug else None,
            lifespan=lifespan
        )
        
        # Store settings in app state
        app.state.settings = settings
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Accept"],
            expose_headers=[],
        )

        # Add authentication middleware
        app.add_middleware(
            AuthMiddleware,
            exclude_paths=["/docs", "/redoc", "/openapi.json", "/health", "/", "/api/v1/auth/login"]
        )
        
        # Add custom middleware
        app.middleware("http")(request_logging_middleware)
        
        # Include API routers
        api_router = create_api_router()
        app.include_router(api_router)
        
        # Include health controller
        app.include_router(health_router)
        
        # Add exception handlers
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        app.add_exception_handler(Exception, general_exception_handler)

        @app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": f"Welcome to {settings.app_name}",
                "version": settings.app_version,
                "environment": settings.environment,
                "docs": "/docs" if settings.debug else "Not available in production",
                "status": "running"
            }
        
        self.log_info("Application configuration completed")
        return app


# Create the application instance
app_manager = ApplicationManager()
app = app_manager.create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )

