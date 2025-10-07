"""
Health check utilities for Jerry services.

This module provides standardized health check endpoints and utilities
for monitoring service health and status.
"""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from ..utils.metrics import get_metrics_collector

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceCheck(BaseModel):
    """Individual service check result."""

    name: str
    status: HealthStatus
    message: str | None = None
    duration_ms: float | None = None
    last_success: datetime | None = None
    error_count: int = 0


class HealthResponse(BaseModel):
    """Health check response model."""

    service: str
    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    version: str = "1.0.0"
    checks: list[ServiceCheck] = []
    metrics: dict[str, Any] | None = None


class HealthChecker:
    """Health check service for Jerry services."""

    def __init__(self, service_name: str, version: str = "1.0.0"):
        """Initialize health checker.

        Args:
            service_name: Name of the service
            version: Version of the service
        """
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()
        self.checks = {}
        self.metrics = get_metrics_collector(service_name)

        logger.info(f"Initialized health checker for {service_name}")

    def add_check(self, name: str, check_func: callable, critical: bool = True):
        """Add a health check.

        Args:
            name: Name of the check
            check_func: Function to execute for the check
            critical: Whether this check is critical for service health
        """
        self.checks[name] = {
            "func": check_func,
            "critical": critical,
            "last_success": None,
            "error_count": 0,
        }

        logger.debug(f"Added health check: {name} (critical: {critical})")

    async def run_check(self, name: str) -> ServiceCheck:
        """Run a single health check.

        Args:
            name: Name of the check to run

        Returns:
            ServiceCheck result
        """
        if name not in self.checks:
            return ServiceCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check '{name}' not found",
            )

        check_info = self.checks[name]
        start_time = time.time()

        try:
            # Run the check function
            if asyncio.iscoroutinefunction(check_info["func"]):
                result = await check_info["func"]()
            else:
                result = check_info["func"]()

            duration_ms = (time.time() - start_time) * 1000

            # Parse result
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = None
            elif isinstance(result, tuple):
                success, message = result
                status = HealthStatus.HEALTHY if success else HealthStatus.UNHEALTHY
            elif isinstance(result, dict):
                status = result.get("status", HealthStatus.HEALTHY)
                message = result.get("message")
            else:
                status = HealthStatus.HEALTHY
                message = str(result)

            # Update check info
            if status == HealthStatus.HEALTHY:
                check_info["last_success"] = datetime.now()
                check_info["error_count"] = 0
            else:
                check_info["error_count"] += 1

            return ServiceCheck(
                name=name,
                status=status,
                message=message,
                duration_ms=duration_ms,
                last_success=check_info["last_success"],
                error_count=check_info["error_count"],
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            check_info["error_count"] += 1

            logger.error(f"Health check '{name}' failed: {e}")

            return ServiceCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                duration_ms=duration_ms,
                last_success=check_info["last_success"],
                error_count=check_info["error_count"],
            )

    async def get_health(self, include_metrics: bool = False) -> HealthResponse:
        """Get overall service health.

        Args:
            include_metrics: Whether to include metrics in response

        Returns:
            HealthResponse with overall status
        """
        # Run all checks
        check_results = []
        for check_name in self.checks:
            result = await self.run_check(check_name)
            check_results.append(result)

        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        critical_failures = 0
        non_critical_failures = 0

        for check_result in check_results:
            check_info = self.checks[check_result.name]
            is_critical = check_info["critical"]

            if check_result.status == HealthStatus.UNHEALTHY:
                if is_critical:
                    critical_failures += 1
                else:
                    non_critical_failures += 1
            elif check_result.status == HealthStatus.DEGRADED:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED

        # Set overall status based on failures
        if critical_failures > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif non_critical_failures > 0 and overall_status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

        # Calculate uptime
        uptime_seconds = time.time() - self.start_time

        # Get metrics if requested
        metrics_data = None
        if include_metrics:
            try:
                metrics_data = self.metrics.get_all_metrics()
            except Exception as e:
                logger.warning(f"Failed to get metrics: {e}")
                metrics_data = {"error": "Failed to retrieve metrics"}

        return HealthResponse(
            service=self.service_name,
            status=overall_status,
            timestamp=datetime.now(),
            uptime_seconds=uptime_seconds,
            version=self.version,
            checks=check_results,
            metrics=metrics_data,
        )


def setup_health_checks(app: FastAPI, health_checker: HealthChecker):
    """Setup health check endpoints for a FastAPI app.

    Args:
        app: FastAPI application
        health_checker: HealthChecker instance
    """

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Basic health check endpoint."""
        health = await health_checker.get_health(include_metrics=False)

        # Set HTTP status code based on health
        if health.status == HealthStatus.DEGRADED:
            pass  # Still consider 200 for degraded
        elif health.status == HealthStatus.UNHEALTHY:
            pass

        return health

    @app.get("/health/detailed", response_model=HealthResponse, tags=["Health"])
    async def detailed_health_check():
        """Detailed health check with metrics."""
        health = await health_checker.get_health(include_metrics=True)

        if health.status == HealthStatus.UNHEALTHY:
            pass

        return health

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Kubernetes-style readiness check."""
        health = await health_checker.get_health(include_metrics=False)

        if health.status == HealthStatus.UNHEALTHY:
            return {"ready": False, "status": health.status}

        return {"ready": True, "status": health.status}

    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Kubernetes-style liveness check."""
        # Simple check that the service is running
        return {
            "alive": True,
            "service": health_checker.service_name,
            "uptime": time.time() - health_checker.start_time,
        }


# Standard health check functions
async def check_database_connection():
    """Check database connectivity."""
    try:
        # This would check your actual database
        # For now, return a mock check
        return True, "Database connection OK"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


async def check_external_service(service_url: str, timeout: int = 5):
    """Check external service connectivity.

    Args:
        service_url: URL of the service to check
        timeout: Request timeout in seconds
    """
    try:
        import aiohttp

        async with (
            aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session,
            session.get(service_url) as response,
        ):
            if response.status < 400:
                return True, f"Service {service_url} is accessible"
            return False, f"Service {service_url} returned status {response.status}"

    except Exception as e:
        return False, f"Failed to connect to {service_url}: {str(e)}"


def check_memory_usage(max_memory_mb: int = 1024):
    """Check memory usage.

    Args:
        max_memory_mb: Maximum allowed memory usage in MB
    """
    try:
        import os

        import psutil

        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        if memory_mb > max_memory_mb:
            return (
                False,
                f"Memory usage {memory_mb:.1f}MB exceeds limit {max_memory_mb}MB",
            )

        return True, f"Memory usage {memory_mb:.1f}MB is within limits"

    except Exception as e:
        return False, f"Failed to check memory usage: {str(e)}"


def check_disk_space(min_free_gb: float = 1.0):
    """Check available disk space.

    Args:
        min_free_gb: Minimum required free space in GB
    """
    try:
        import psutil

        disk_usage = psutil.disk_usage("/")
        free_gb = disk_usage.free / 1024 / 1024 / 1024

        if free_gb < min_free_gb:
            return (
                False,
                f"Free disk space {free_gb:.1f}GB is below limit {min_free_gb}GB",
            )

        return True, f"Free disk space {free_gb:.1f}GB is sufficient"

    except Exception as e:
        return False, f"Failed to check disk space: {str(e)}"
