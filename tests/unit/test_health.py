"""
Unit tests for health checking module.
"""

import pytest

from src.utils.health import HealthChecker
from src.utils.health import HealthStatus
from src.utils.health import ServiceCheck


class TestHealthChecker:
    """Test health checking functionality."""

    def test_health_checker_creation(self):
        """Test creating a health checker."""
        checker = HealthChecker("test-service", "1.0.0")
        assert checker.service_name == "test-service"
        assert checker.version == "1.0.0"
        assert len(checker.checks) == 0

    def test_add_health_check(self):
        """Test adding health checks."""
        checker = HealthChecker("test-service")

        def test_check():
            return True, "Test check passed"

        checker.add_check("test-check", test_check)
        assert "test-check" in checker.checks
        assert checker.checks["test-check"]["func"] == test_check
        assert checker.checks["test-check"]["critical"] is True

    def test_add_non_critical_check(self):
        """Test adding non-critical health checks."""
        checker = HealthChecker("test-service")

        def test_check():
            return True, "Test check passed"

        checker.add_check("test-check", test_check, critical=False)
        assert checker.checks["test-check"]["critical"] is False

    @pytest.mark.asyncio
    async def test_run_successful_check(self):
        """Test running a successful health check."""
        checker = HealthChecker("test-service")

        def successful_check():
            return True, "Check passed"

        checker.add_check("success-check", successful_check)

        result = await checker.run_check("success-check")
        assert result.name == "success-check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Check passed"
        assert result.duration_ms is not None

    @pytest.mark.asyncio
    async def test_run_failing_check(self):
        """Test running a failing health check."""
        checker = HealthChecker("test-service")

        def failing_check():
            return False, "Check failed"

        checker.add_check("fail-check", failing_check)

        result = await checker.run_check("fail-check")
        assert result.name == "fail-check"
        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "Check failed"

    @pytest.mark.asyncio
    async def test_run_exception_check(self):
        """Test running a check that raises an exception."""
        checker = HealthChecker("test-service")

        def exception_check():
            raise Exception("Test exception")

        checker.add_check("exception-check", exception_check)

        result = await checker.run_check("exception-check")
        assert result.name == "exception-check"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Test exception" in result.message

    @pytest.mark.asyncio
    async def test_get_overall_health_all_healthy(self):
        """Test getting overall health when all checks pass."""
        checker = HealthChecker("test-service")

        def healthy_check1():
            return True, "Check 1 passed"

        def healthy_check2():
            return True, "Check 2 passed"

        checker.add_check("check1", healthy_check1)
        checker.add_check("check2", healthy_check2)

        health = await checker.get_health()
        assert health.status == HealthStatus.HEALTHY
        assert len(health.checks) == 2

    @pytest.mark.asyncio
    async def test_get_overall_health_with_failure(self):
        """Test getting overall health when a critical check fails."""
        checker = HealthChecker("test-service")

        def healthy_check():
            return True, "Check passed"

        def failing_check():
            return False, "Check failed"

        checker.add_check("healthy", healthy_check)
        checker.add_check("failing", failing_check, critical=True)

        health = await checker.get_health()
        assert health.status == HealthStatus.UNHEALTHY
        assert len(health.checks) == 2

    @pytest.mark.asyncio
    async def test_get_overall_health_with_non_critical_failure(self):
        """Test getting overall health when only non-critical checks fail."""
        checker = HealthChecker("test-service")

        def healthy_check():
            return True, "Check passed"

        def failing_check():
            return False, "Check failed"

        checker.add_check("healthy", healthy_check, critical=True)
        checker.add_check("failing", failing_check, critical=False)

        health = await checker.get_health()
        assert health.status == HealthStatus.DEGRADED
        assert len(health.checks) == 2


class TestServiceCheck:
    """Test ServiceCheck model."""

    def test_service_check_creation(self):
        """Test creating a service check result."""
        check = ServiceCheck(
            name="test-check",
            status=HealthStatus.HEALTHY,
            message="All good",
        )

        assert check.name == "test-check"
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "All good"
        assert check.error_count == 0
