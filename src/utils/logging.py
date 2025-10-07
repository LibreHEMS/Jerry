"""
Logging setup and utilities for Jerry AI assistant.

This module provides centralized logging configuration and utilities
for consistent logging across all Jerry components.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from json_log_formatter import JSONFormatter

from .config import LoggingConfig


class CustomJSONFormatter(JSONFormatter):
    """Custom JSON log formatter to add extra fields."""

    def json_record(self, message: str, extra: dict, record: logging.LogRecord) -> dict:
        # Add extra fields from the log record
        extra.update(record.__dict__)
        # Add standard fields
        extra["level"] = record.levelname
        extra["name"] = record.name
        return super().json_record(message, extra, record)


def setup_logging(config: LoggingConfig) -> None:
    """Set up logging configuration for the application."""
    # Create logs directory if it doesn't exist
    if config.file_path:
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter based on config
    if config.json_format:
        formatter = CustomJSONFormatter()
    else:
        formatter = logging.Formatter(config.format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if config.file_path:
        file_handler = logging.handlers.RotatingFileHandler(
            config.file_path,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure specific loggers
    _configure_external_loggers()

    # Log setup completion
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {config.level}")
    if config.file_path:
        logger.info(f"Logging to file: {config.file_path}")


def _configure_external_loggers() -> None:
    """Configure logging levels for external libraries."""
    # Discord.py logging
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.WARNING)

    # HTTP client logging
    http_logger = logging.getLogger("discord.http")
    http_logger.setLevel(logging.WARNING)

    # Gateway logging
    gateway_logger = logging.getLogger("discord.gateway")
    gateway_logger.setLevel(logging.WARNING)

    # LangChain logging
    langchain_logger = logging.getLogger("langchain")
    langchain_logger.setLevel(logging.WARNING)

    # Chroma logging
    chroma_logger = logging.getLogger("chromadb")
    chroma_logger.setLevel(logging.WARNING)

    # SQLAlchemy logging (if used)
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    sqlalchemy_logger.setLevel(logging.WARNING)

    # FastAPI/Uvicorn logging
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)

    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def log_function_call(logger: logging.Logger, func_name: str, **kwargs) -> None:
    """Log a function call with its parameters."""
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


def log_performance(logger: logging.Logger, operation: str, duration_ms: float) -> None:
    """Log performance metrics for an operation."""
    logger.info(f"Performance: {operation} took {duration_ms:.2f}ms")


def log_error_with_context(
    logger: logging.Logger, error: Exception, context: str, **extra_context
) -> None:
    """Log an error with additional context information."""
    context_str = f"Context: {context}"
    if extra_context:
        context_items = ", ".join(f"{k}={v}" for k, v in extra_context.items())
        context_str += f" | {context_items}"

    logger.error(
        f"{context_str} | Error: {type(error).__name__}: {error}", exc_info=True
    )


class ContextLogger:
    """Logger wrapper that automatically includes context in log messages."""

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context

    def _format_message(self, message: str) -> str:
        """Format message with context."""
        if self.context:
            context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"[{context_str}] {message}"
        return message

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message with context."""
        self.logger.debug(self._format_message(message), *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message with context."""
        self.logger.info(self._format_message(message), *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message with context."""
        self.logger.warning(self._format_message(message), *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message with context."""
        self.logger.error(self._format_message(message), *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message with context."""
        self.logger.critical(self._format_message(message), *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception message with context."""
        self.logger.exception(self._format_message(message), *args, **kwargs)


def create_context_logger(name: str, **context) -> ContextLogger:
    """Create a context logger for consistent logging with context."""
    logger = logging.getLogger(name)
    return ContextLogger(logger, **context)


class PerformanceTimer:
    """Context manager for timing operations and logging performance."""

    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        import time

        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        if self.start_time is not None:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            if exc_type is None:
                log_performance(self.logger, self.operation, duration_ms)
            else:
                self.logger.error(
                    f"Performance: {self.operation} failed after {duration_ms:.2f}ms"
                )


def time_operation(logger: logging.Logger, operation: str):
    """Decorator for timing function calls."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceTimer(logger, f"{operation} ({func.__name__})"):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Create module-level logger
logger = get_logger(__name__)
