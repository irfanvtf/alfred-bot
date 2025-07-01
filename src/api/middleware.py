# src/api/middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import traceback
from typing import Callable

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Centralized error handling middleware for the FastAPI application
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Log successful requests
            process_time = time.time() - start_time
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except HTTPException as e:
            # Handle known HTTP exceptions
            process_time = time.time() - start_time
            logger.warning(
                f"HTTP Exception: {request.method} {request.url.path} "
                f"Status: {e.status_code} "
                f"Detail: {e.detail} "
                f"Time: {process_time:.3f}s"
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "status_code": e.status_code,
                    "message": e.detail,
                    "path": str(request.url.path),
                    "method": request.method,
                    "timestamp": time.time()
                }
            )
            
        except Exception as e:
            # Handle unexpected exceptions
            process_time = time.time() - start_time
            error_id = f"error_{int(time.time())}_{hash(str(e)) % 10000}"
            
            logger.error(
                f"Unexpected Error [{error_id}]: {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Time: {process_time:.3f}s",
                exc_info=True
            )
            
            # Don't expose internal error details in production
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "status_code": 500,
                    "message": "Internal server error occurred",
                    "error_id": error_id,
                    "path": str(request.url.path),
                    "method": request.method,
                    "timestamp": time.time()
                }
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/Response logging middleware
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path} "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Add request timestamp
        request.state.start_time = time.time()
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - request.state.start_time
        logger.info(
            f"Response: {response.status_code} "
            f"Time: {process_time:.3f}s"
        )
        
        # Add response headers
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        response.headers["X-Request-ID"] = getattr(request.state, 'request_id', 'unknown')
        
        return response


def setup_exception_handlers(app):
    """
    Setup global exception handlers for the FastAPI app
    """
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning(f"ValueError: {request.method} {request.url.path} - {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "status_code": 400,
                "message": f"Invalid input: {str(exc)}",
                "path": str(request.url.path),
                "method": request.method
            }
        )
    
    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        logger.warning(f"KeyError: {request.method} {request.url.path} - {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "status_code": 400,
                "message": f"Missing required field: {str(exc)}",
                "path": str(request.url.path),
                "method": request.method
            }
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": True,
                "status_code": 404,
                "message": "Resource not found",
                "path": str(request.url.path),
                "method": request.method
            }
        )
