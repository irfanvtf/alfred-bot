# src/utils/logging_config.py
import logging
import logging.config
import sys
from pathlib import Path
from datetime import datetime
import os


def setup_logging(log_level: str = "INFO", log_to_file: bool = True, log_dir: str = "logs"):
    """
    Setup structured logging configuration for the Alfred bot
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to files in addition to console
        log_dir: Directory to store log files
    """
    
    # Create logs directory if it doesn't exist
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Generate log file names with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        app_log_file = log_path / f"alfred_app_{timestamp}.log"
        error_log_file = log_path / f"alfred_errors_{timestamp}.log"
    
    # Define logging format
    log_format = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(asctime)s | %(levelname)s | %(message)s",
                "datefmt": "%H:%M:%S"
            },
            "json": {
                "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s | %(pathname)s:%(lineno)d",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple",
                "stream": sys.stdout
            }
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            # Application loggers
            "src": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "src.services": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "src.api": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            # External library loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "redis": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "chromadb": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handlers if enabled
    if log_to_file:
        log_format["handlers"].update({
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": str(app_log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(error_log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        })
        
        # Add file handlers to loggers
        for logger_name in ["", "src", "src.services", "src.api"]:
            log_format["loggers"][logger_name]["handlers"].extend(["file_app", "file_error"])
    
    # Apply logging configuration
    logging.config.dictConfig(log_format)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File logging: {log_to_file}")
    
    if log_to_file:
        logger.info(f"Log files: {app_log_file}, {error_log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class StructuredLogger:
    """
    Structured logging wrapper for consistent log formatting
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_message = f"{message} | {extra_data}" if extra_data else message
        self.logger.info(log_message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_message = f"{message} | {extra_data}" if extra_data else message
        self.logger.warning(log_message)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_message = f"{message} | {extra_data}" if extra_data else message
        self.logger.error(log_message, exc_info=kwargs.get('exc_info', False))
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_message = f"{message} | {extra_data}" if extra_data else message
        self.logger.debug(log_message)


# Performance logging decorator
def log_performance(func_name: str = None):
    """
    Decorator to log function performance
    
    Args:
        func_name: Custom function name for logging
    """
    def decorator(func):
        import time
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Performance | {name} | duration={duration:.3f}s | status=success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Performance | {name} | duration={duration:.3f}s | status=error | error={str(e)}")
                raise
        
        return wrapper
    return decorator
