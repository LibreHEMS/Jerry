"""
Prometheus metrics collection for Jerry AI assistant.

This module provides comprehensive metrics collection for monitoring
Jerry's performance, usage, and health across all services.
"""

import functools
import logging
import time
from collections.abc import Callable

try:
    from prometheus_client import CollectorRegistry
    from prometheus_client import Counter
    from prometheus_client import Enum
    from prometheus_client import Gauge
    from prometheus_client import Histogram
    from prometheus_client import Info
    from prometheus_client import generate_latest
    from prometheus_client import start_http_server

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Define dummy classes for type hints when prometheus is not available
    class CollectorRegistry:
        pass

    class Counter:
        pass

    class Gauge:
        pass

    class Histogram:
        pass

    class Enum:
        pass

    class Info:
        pass

    def generate_latest(registry):
        return b""

    def start_http_server(port):
        pass


logger = logging.getLogger(__name__)


class MetricsCollector:
    """Centralized metrics collection for Jerry AI assistant."""

    def __init__(self, service_name: str, registry=None):
        """Initialize metrics collector.

        Args:
            service_name: Name of the service (bot, model, rag, agent)
            registry: Optional custom registry
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available, metrics will be no-ops")
            self._enabled = False
            return

        self._enabled = True
        self.service_name = service_name
        self.registry = registry or CollectorRegistry()

        # Initialize core metrics
        self._init_core_metrics()
        self._init_service_specific_metrics()

        logger.info(f"Initialized metrics collector for service: {service_name}")

    def _init_core_metrics(self) -> None:
        """Initialize core metrics used by all services."""
        if not self._enabled:
            return

        # Service info
        self.service_info = Info(
            "jerry_service", "Service information", registry=self.registry
        )
        self.service_info.info({"service": self.service_name, "version": "1.0.0"})

        # Request metrics
        self.request_total = Counter(
            "jerry_requests_total",
            "Total number of requests",
            ["service", "endpoint", "method", "status"],
            registry=self.registry,
        )

        self.request_duration = Histogram(
            "jerry_request_duration_seconds",
            "Request duration in seconds",
            ["service", "endpoint", "method"],
            registry=self.registry,
        )

        # Error metrics
        self.errors_total = Counter(
            "jerry_errors_total",
            "Total number of errors",
            ["service", "error_type"],
            registry=self.registry,
        )

        # Resource metrics
        self.memory_usage = Gauge(
            "jerry_memory_usage_bytes",
            "Memory usage in bytes",
            ["service"],
            registry=self.registry,
        )

        self.cpu_usage = Gauge(
            "jerry_cpu_usage_percent",
            "CPU usage percentage",
            ["service"],
            registry=self.registry,
        )

        # Active connections/sessions
        self.active_connections = Gauge(
            "jerry_active_connections",
            "Number of active connections/sessions",
            ["service"],
            registry=self.registry,
        )

    def _init_service_specific_metrics(self) -> None:
        """Initialize service-specific metrics."""
        if not self._enabled:
            return

        if self.service_name == "bot":
            self._init_bot_metrics()
        elif self.service_name == "model":
            self._init_model_metrics()
        elif self.service_name == "rag":
            self._init_rag_metrics()
        elif self.service_name == "agent":
            self._init_agent_metrics()

    def _init_bot_metrics(self) -> None:
        """Initialize Discord bot specific metrics."""
        # Discord events
        self.discord_events_total = Counter(
            "jerry_discord_events_total",
            "Total Discord events processed",
            ["event_type"],
            registry=self.registry,
        )

        # Messages
        self.messages_sent = Counter(
            "jerry_messages_sent_total",
            "Total messages sent",
            ["channel_type"],
            registry=self.registry,
        )

        self.messages_received = Counter(
            "jerry_messages_received_total",
            "Total messages received",
            ["channel_type"],
            registry=self.registry,
        )

        # Commands
        self.commands_executed = Counter(
            "jerry_commands_executed_total",
            "Total commands executed",
            ["command_name", "status"],
            registry=self.registry,
        )

        # Guilds and users
        self.guild_count = Gauge(
            "jerry_guilds_total", "Number of Discord guilds", registry=self.registry
        )

        self.user_count = Gauge(
            "jerry_users_total", "Number of Discord users", registry=self.registry
        )

    def _init_model_metrics(self) -> None:
        """Initialize model service specific metrics."""
        # Inference metrics
        self.inference_requests = Counter(
            "jerry_inference_requests_total",
            "Total inference requests",
            ["model_name", "status"],
            registry=self.registry,
        )

        self.inference_duration = Histogram(
            "jerry_inference_duration_seconds",
            "Inference duration in seconds",
            ["model_name"],
            registry=self.registry,
        )

        self.tokens_generated = Counter(
            "jerry_tokens_generated_total",
            "Total tokens generated",
            ["model_name"],
            registry=self.registry,
        )

        # Model status
        self.model_status = Enum(
            "jerry_model_status",
            "Model service status",
            ["model_name"],
            states=["loading", "ready", "error", "unavailable"],
            registry=self.registry,
        )

        # Model resource usage
        self.model_memory_usage = Gauge(
            "jerry_model_memory_usage_bytes",
            "Model memory usage in bytes",
            ["model_name"],
            registry=self.registry,
        )

        self.context_length_used = Histogram(
            "jerry_context_length_used",
            "Context length used in tokens",
            ["model_name"],
            registry=self.registry,
        )

    def _init_rag_metrics(self) -> None:
        """Initialize RAG service specific metrics."""
        # Search metrics
        self.rag_searches = Counter(
            "jerry_rag_searches_total",
            "Total RAG searches performed",
            ["status"],
            registry=self.registry,
        )

        self.rag_search_duration = Histogram(
            "jerry_rag_search_duration_seconds",
            "RAG search duration in seconds",
            registry=self.registry,
        )

        self.chunks_retrieved = Histogram(
            "jerry_chunks_retrieved",
            "Number of chunks retrieved per search",
            registry=self.registry,
        )

        # Knowledge base metrics
        self.knowledge_base_size = Gauge(
            "jerry_knowledge_base_chunks_total",
            "Total chunks in knowledge base",
            registry=self.registry,
        )

        self.embeddings_generated = Counter(
            "jerry_embeddings_generated_total",
            "Total embeddings generated",
            registry=self.registry,
        )

        # Vector store metrics
        self.vector_store_operations = Counter(
            "jerry_vector_store_operations_total",
            "Vector store operations",
            ["operation"],
            registry=self.registry,
        )

    def _init_agent_metrics(self) -> None:
        """Initialize agent service specific metrics."""
        # Conversation metrics
        self.conversations_started = Counter(
            "jerry_conversations_started_total",
            "Total conversations started",
            registry=self.registry,
        )

        self.conversations_active = Gauge(
            "jerry_conversations_active",
            "Number of active conversations",
            registry=self.registry,
        )

        self.conversation_duration = Histogram(
            "jerry_conversation_duration_seconds",
            "Conversation duration in seconds",
            registry=self.registry,
        )

        # Agent actions
        self.agent_actions = Counter(
            "jerry_agent_actions_total",
            "Agent actions performed",
            ["action_type", "tool_name"],
            registry=self.registry,
        )

        self.tool_execution_duration = Histogram(
            "jerry_tool_execution_duration_seconds",
            "Tool execution duration in seconds",
            ["tool_name"],
            registry=self.registry,
        )

        # Response metrics
        self.response_quality_score = Histogram(
            "jerry_response_quality_score",
            "Response quality score (0-1)",
            registry=self.registry,
        )

    # Core metric recording methods
    def record_request(
        self,
        endpoint: str,
        method: str = "POST",
        status_code: int = 200,
        duration: float | None = None,
    ) -> None:
        """Record a request metric.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            duration: Request duration in seconds
        """
        if not self._enabled:
            return

        status = "success" if 200 <= status_code < 400 else "error"

        self.request_total.labels(
            service=self.service_name, endpoint=endpoint, method=method, status=status
        ).inc()

        if duration is not None:
            self.request_duration.labels(
                service=self.service_name, endpoint=endpoint, method=method
            ).observe(duration)

    def record_error(self, error_type: str) -> None:
        """Record an error metric.

        Args:
            error_type: Type of error (e.g., 'timeout', 'validation', 'model_error')
        """
        if not self._enabled:
            return

        self.errors_total.labels(service=self.service_name, error_type=error_type).inc()

    def update_resource_usage(
        self, memory_bytes: int | None = None, cpu_percent: float | None = None
    ) -> None:
        """Update resource usage metrics.

        Args:
            memory_bytes: Memory usage in bytes
            cpu_percent: CPU usage percentage
        """
        if not self._enabled:
            return

        if memory_bytes is not None:
            self.memory_usage.labels(service=self.service_name).set(memory_bytes)

        if cpu_percent is not None:
            self.cpu_usage.labels(service=self.service_name).set(cpu_percent)

    def set_active_connections(self, count: int) -> None:
        """Set the number of active connections.

        Args:
            count: Number of active connections
        """
        if not self._enabled:
            return

        self.active_connections.labels(service=self.service_name).set(count)

    # Service-specific recording methods
    def record_discord_event(self, event_type: str) -> None:
        """Record Discord event (bot service only)."""
        if not self._enabled or self.service_name != "bot":
            return

        self.discord_events_total.labels(event_type=event_type).inc()

    def record_message(self, direction: str, channel_type: str = "text") -> None:
        """Record message sent/received (bot service only).

        Args:
            direction: 'sent' or 'received'
            channel_type: Type of channel ('text', 'dm', 'voice')
        """
        if not self._enabled or self.service_name != "bot":
            return

        if direction == "sent":
            self.messages_sent.labels(channel_type=channel_type).inc()
        elif direction == "received":
            self.messages_received.labels(channel_type=channel_type).inc()

    def record_command(self, command_name: str, success: bool = True) -> None:
        """Record command execution (bot service only).

        Args:
            command_name: Name of the command
            success: Whether the command succeeded
        """
        if not self._enabled or self.service_name != "bot":
            return

        status = "success" if success else "error"
        self.commands_executed.labels(command_name=command_name, status=status).inc()

    def record_inference(
        self,
        model_name: str,
        duration: float,
        tokens_generated: int,
        success: bool = True,
    ) -> None:
        """Record model inference (model service only).

        Args:
            model_name: Name of the model
            duration: Inference duration in seconds
            tokens_generated: Number of tokens generated
            success: Whether inference succeeded
        """
        if not self._enabled or self.service_name != "model":
            return

        status = "success" if success else "error"

        self.inference_requests.labels(model_name=model_name, status=status).inc()

        if success:
            self.inference_duration.labels(model_name=model_name).observe(duration)
            self.tokens_generated.labels(model_name=model_name).inc(tokens_generated)

    def set_model_status(self, model_name: str, status: str) -> None:
        """Set model status (model service only).

        Args:
            model_name: Name of the model
            status: Status ('loading', 'ready', 'error', 'unavailable')
        """
        if not self._enabled or self.service_name != "model":
            return

        self.model_status.labels(model_name=model_name).state(status)

    def record_rag_search(
        self, duration: float, chunks_found: int, success: bool = True
    ) -> None:
        """Record RAG search (rag service only).

        Args:
            duration: Search duration in seconds
            chunks_found: Number of chunks found
            success: Whether search succeeded
        """
        if not self._enabled or self.service_name != "rag":
            return

        status = "success" if success else "error"

        self.rag_searches.labels(status=status).inc()

        if success:
            self.rag_search_duration.observe(duration)
            self.chunks_retrieved.observe(chunks_found)

    def set_knowledge_base_size(self, size: int) -> None:
        """Set knowledge base size (rag service only).

        Args:
            size: Number of chunks in knowledge base
        """
        if not self._enabled or self.service_name != "rag":
            return

        self.knowledge_base_size.set(size)

    def record_agent_action(
        self, action_type: str, tool_name: str, duration: float
    ) -> None:
        """Record agent action (agent service only).

        Args:
            action_type: Type of action ('tool_call', 'reasoning', 'response')
            tool_name: Name of the tool used
            duration: Action duration in seconds
        """
        if not self._enabled or self.service_name != "agent":
            return

        self.agent_actions.labels(action_type=action_type, tool_name=tool_name).inc()
        self.tool_execution_duration.labels(tool_name=tool_name).observe(duration)

    def record_conversation_start(self) -> None:
        """Record conversation start (agent service only)."""
        if not self._enabled or self.service_name != "agent":
            return

        self.conversations_started.inc()

    def set_active_conversations(self, count: int) -> None:
        """Set active conversation count (agent service only).

        Args:
            count: Number of active conversations
        """
        if not self._enabled or self.service_name != "agent":
            return

        self.conversations_active.set(count)

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format.

        Returns:
            Metrics data in Prometheus text format
        """
        if not self._enabled:
            return "# Metrics not available\n"

        return generate_latest(self.registry).decode("utf-8")

    def start_http_server(self, port: int = 9090) -> None:
        """Start HTTP server for metrics endpoint.

        Args:
            port: Port to listen on
        """
        if not self._enabled:
            logger.warning("Cannot start metrics server: Prometheus not available")
            return

        start_http_server(port, registry=self.registry)
        logger.info(f"Started metrics server on port {port}")


def timer_metric(metric_collector: MetricsCollector, metric_name: str, **labels):
    """Decorator to time function execution and record metrics.

    Args:
        metric_collector: MetricsCollector instance
        metric_name: Name of the metric to record
        **labels: Additional labels for the metric
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record successful execution
                if hasattr(metric_collector, metric_name):
                    metric = getattr(metric_collector, metric_name)
                    if hasattr(metric, "labels"):
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Record error
                metric_collector.record_error(type(e).__name__)

                raise

        return wrapper

    return decorator


def counter_metric(metric_collector: MetricsCollector, metric_name: str, **labels):
    """Decorator to count function calls.

    Args:
        metric_collector: MetricsCollector instance
        metric_name: Name of the metric to increment
        **labels: Additional labels for the metric
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # Record successful call
                if hasattr(metric_collector, metric_name):
                    metric = getattr(metric_collector, metric_name)
                    if hasattr(metric, "labels"):
                        metric.labels(**labels).inc()
                    else:
                        metric.inc()

                return result

            except Exception as e:
                # Record error
                metric_collector.record_error(type(e).__name__)
                raise

        return wrapper

    return decorator


# Global metrics collector instances
_metrics_collectors: dict[str, MetricsCollector] = {}


def get_metrics_collector(service_name: str) -> MetricsCollector:
    """Get or create metrics collector for service.

    Args:
        service_name: Name of the service

    Returns:
        MetricsCollector instance
    """
    if service_name not in _metrics_collectors:
        _metrics_collectors[service_name] = MetricsCollector(service_name)

    return _metrics_collectors[service_name]


class MockMetricsCollector:
    """Mock metrics collector for testing or when Prometheus is not available."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        logger.debug(f"Using mock metrics collector for {service_name}")

    def __getattr__(self, name: str) -> Callable:
        """Return no-op callable for any metric method."""

        def no_op(*args, **kwargs):
            pass

        return no_op

    def get_metrics(self) -> str:
        return "# Mock metrics - Prometheus not available\n"
