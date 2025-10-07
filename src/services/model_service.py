"""
Abstract model service interface for Jerry AI.

This module defines the abstract interface for AI model services,
allowing for different implementations (local, remote, etc.).
"""

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID


class ModelType(Enum):
    """Types of AI models supported."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"


@dataclass
class ModelConfig:
    """Configuration for a model instance."""

    name: str
    type: ModelType
    model_path: str
    context_length: int = 4096
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    quantization: str = "Q4_K_M"
    gpu_layers: int = 0
    threads: int = 4


@dataclass
class ChatMessage:
    """A message in a chat conversation."""

    role: str  # "user", "assistant", "system"
    content: str
    name: str | None = None


@dataclass
class ChatRequest:
    """Request for chat completion."""

    messages: list[ChatMessage]
    model: str
    temperature: float = 0.7
    max_tokens: int = 512
    stream: bool = False
    stop: list[str] | None = None
    user_id: str | None = None
    conversation_id: UUID | None = None


@dataclass
class ChatResponse:
    """Response from chat completion."""

    id: str
    model: str
    content: str
    role: str = "assistant"
    finish_reason: str = "stop"
    tokens_used: int = 0
    response_time_ms: int = 0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# Alias for compatibility
ModelResponse = ChatResponse


@dataclass
class StreamChunk:
    """A chunk of streaming response."""

    id: str
    model: str
    content: str
    finish_reason: str | None = None
    delta_time_ms: int = 0


@dataclass
class HealthStatus:
    """Health status of a model service."""

    healthy: bool
    model_loaded: bool
    model_name: str
    memory_usage_mb: int
    gpu_usage_percent: int = 0
    uptime_seconds: int = 0
    last_request_time: str | None = None
    error_message: str | None = None


class ModelService(ABC):
    """Abstract base class for AI model services."""

    def __init__(self, config: ModelConfig):
        """Initialize the model service with configuration."""
        self.config = config
        self._is_loaded = False

    @abstractmethod
    async def load_model(self) -> None:
        """Load the AI model into memory."""

    @abstractmethod
    async def unload_model(self) -> None:
        """Unload the AI model from memory."""

    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion response."""

    @abstractmethod
    async def chat_completion_stream(
        self, request: ChatRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming chat completion response."""

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check the health status of the model service."""

    @property
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded."""
        return self._is_loaded

    @property
    def model_name(self) -> str:
        """Get the name of the current model."""
        return self.config.name

    async def __aenter__(self):
        """Async context manager entry."""
        await self.load_model()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.unload_model()


class ModelServiceError(Exception):
    """Base exception for model service errors."""


class ModelNotLoadedError(ModelServiceError):
    """Raised when trying to use a model that isn't loaded."""


class ModelLoadError(ModelServiceError):
    """Raised when model loading fails."""


class InferenceError(ModelServiceError):
    """Raised when model inference fails."""


class ModelServiceRegistry:
    """Registry for managing multiple model services."""

    def __init__(self):
        self._services: dict[str, ModelService] = {}
        self._default_service: str | None = None
        self._fallback_services: list[str] = []

    def register(
        self,
        name: str,
        service: ModelService,
        default: bool = False,
        fallback: bool = False,
    ) -> None:
        """Register a model service."""
        self._services[name] = service
        if default or self._default_service is None:
            self._default_service = name
        if fallback:
            self._fallback_services.append(name)

    def get(self, name: str | None = None) -> ModelService:
        """Get a model service by name, or the default service."""
        if name is None:
            name = self._default_service

        if name is None:
            raise ValueError("No default model service configured")

        if name not in self._services:
            raise ValueError(f"Model service '{name}' not found")

        return self._services[name]

    async def get_healthy_service(self, preferred: str | None = None) -> ModelService:
        """Get a healthy model service, with fallback to other services."""
        # Try preferred service first
        if preferred and preferred in self._services:
            service = self._services[preferred]
            health = await service.health_check()
            if health.healthy and health.model_loaded:
                return service

        # Try default service
        if self._default_service and self._default_service in self._services:
            service = self._services[self._default_service]
            health = await service.health_check()
            if health.healthy and health.model_loaded:
                return service

        # Try fallback services
        for service_name in self._fallback_services:
            if service_name in self._services:
                service = self._services[service_name]
                health = await service.health_check()
                if health.healthy and health.model_loaded:
                    return service

        # Try any remaining services
        for service_name, service in self._services.items():
            if (
                service_name
                not in [preferred, self._default_service] + self._fallback_services
            ):
                health = await service.health_check()
                if health.healthy and health.model_loaded:
                    return service

        raise ModelNotLoadedError("No healthy model services available")

    def list_services(self) -> list[str]:
        """List all registered service names."""
        return list(self._services.keys())

    async def health_check_all(self) -> dict[str, HealthStatus]:
        """Check health of all registered services."""
        health_statuses = {}
        for name, service in self._services.items():
            try:
                health_statuses[name] = await service.health_check()
            except Exception as e:
                health_statuses[name] = HealthStatus(
                    healthy=False,
                    model_loaded=False,
                    model_name=name,
                    memory_usage_mb=0,
                    error_message=str(e),
                )
        return health_statuses

    async def shutdown_all(self) -> None:
        """Shutdown all registered services."""
        for service in self._services.values():
            try:
                await service.unload_model()
            except Exception as e:
                # Log error but continue shutting down other services
                print(f"Error shutting down service: {e}")
