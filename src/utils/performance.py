"""
Performance optimization enhancements for Jerry services.

This module provides performance optimizations including caching,
connection pooling, and monitoring integrations.
"""

import asyncio
import hashlib
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any
from typing import TypeVar

from ..utils.cache import get_memory_cache
from ..utils.cache import get_semantic_cache
from ..utils.metrics import get_metrics_collector

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PerformanceOptimizer:
    """Performance optimization utilities for services."""

    def __init__(self, service_name: str):
        """Initialize performance optimizer.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.semantic_cache = get_semantic_cache()
        self.memory_cache = get_memory_cache()
        self.metrics = get_metrics_collector(service_name)

        logger.info(f"Initialized performance optimizer for {service_name}")

    def cached_response(
        self,
        cache_key_func: Callable | None = None,
        ttl_seconds: int = 3600,
        use_semantic: bool = True,
    ):
        """Decorator for caching service responses.

        Args:
            cache_key_func: Function to generate cache key
            ttl_seconds: Time to live for cache entries
            use_semantic: Whether to use semantic cache
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)

                # Try cache first
                start_time = time.time()

                if use_semantic and hasattr(args[0], "query"):
                    # Use semantic cache for query-based functions
                    cached_response = self.semantic_cache.get(
                        query=args[0].query,
                        context=kwargs.get("context"),
                        model_used=kwargs.get("model", self.service_name),
                    )
                    if cached_response:
                        cache_time = time.time() - start_time
                        self.metrics.record_request(
                            endpoint=func.__name__,
                            method="CACHE_HIT",
                            duration=cache_time,
                        )
                        logger.debug(f"Semantic cache hit for {func.__name__}")
                        return cached_response
                else:
                    # Use memory cache for other data
                    cached_response = self.memory_cache.get(cache_key)
                    if cached_response is not None:
                        cache_time = time.time() - start_time
                        self.metrics.record_request(
                            endpoint=func.__name__,
                            method="CACHE_HIT",
                            duration=cache_time,
                        )
                        logger.debug(f"Memory cache hit for {func.__name__}")
                        return cached_response

                # Cache miss - execute function
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Store in cache
                    if (
                        use_semantic
                        and hasattr(args[0], "query")
                        and isinstance(result, str)
                    ):
                        self.semantic_cache.put(
                            query=args[0].query,
                            response=result,
                            context=kwargs.get("context"),
                            model_used=kwargs.get("model", self.service_name),
                            ttl_seconds=ttl_seconds,
                        )
                    else:
                        self.memory_cache.put(cache_key, result, ttl_seconds)

                    # Record metrics
                    self.metrics.record_request(
                        endpoint=func.__name__,
                        method="CACHE_MISS",
                        duration=execution_time,
                    )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    self.metrics.record_request(
                        endpoint=func.__name__,
                        method="ERROR",
                        status_code=500,
                        duration=execution_time,
                    )
                    self.metrics.record_error(type(e).__name__)
                    raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Similar logic for sync functions
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)

                start_time = time.time()

                # Try cache
                cached_response = self.memory_cache.get(cache_key)
                if cached_response is not None:
                    cache_time = time.time() - start_time
                    self.metrics.record_request(
                        endpoint=func.__name__, method="CACHE_HIT", duration=cache_time
                    )
                    return cached_response

                # Execute function
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Cache result
                    self.memory_cache.put(cache_key, result, ttl_seconds)

                    # Record metrics
                    self.metrics.record_request(
                        endpoint=func.__name__,
                        method="CACHE_MISS",
                        duration=execution_time,
                    )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    self.metrics.record_request(
                        endpoint=func.__name__,
                        method="ERROR",
                        status_code=500,
                        duration=execution_time,
                    )
                    self.metrics.record_error(type(e).__name__)
                    raise

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments.

        Args:
            func_name: Name of the function
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Cache key string
        """
        # Create deterministic key from function name and arguments
        key_data = {
            "function": func_name,
            "args": str(args),
            "kwargs": sorted(kwargs.items()),
        }

        key_string = str(key_data)
        return hashlib.md5(key_string.encode()).hexdigest()

    def timed_execution(self, operation_name: str):
        """Decorator to time function execution.

        Args:
            operation_name: Name of the operation for metrics
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time

                    # Record timing metrics
                    self.metrics.record_request(
                        endpoint=operation_name, method="EXECUTE", duration=duration
                    )

                    logger.debug(f"{operation_name} completed in {duration:.3f}s")
                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    self.metrics.record_request(
                        endpoint=operation_name,
                        method="ERROR",
                        status_code=500,
                        duration=duration,
                    )
                    self.metrics.record_error(type(e).__name__)
                    raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    # Record timing metrics
                    self.metrics.record_request(
                        endpoint=operation_name, method="EXECUTE", duration=duration
                    )

                    logger.debug(f"{operation_name} completed in {duration:.3f}s")
                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    self.metrics.record_request(
                        endpoint=operation_name,
                        method="ERROR",
                        status_code=500,
                        duration=duration,
                    )
                    self.metrics.record_error(type(e).__name__)
                    raise

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    def batch_processor(self, batch_size: int = 10, max_wait_time: float = 1.0):
        """Decorator for batch processing of requests.

        Args:
            batch_size: Maximum batch size
            max_wait_time: Maximum wait time for batch collection
        """

        def decorator(func: Callable) -> Callable:
            pending_requests = []
            last_batch_time = time.time()

            @wraps(func)
            async def wrapper(request: Any) -> Any:
                nonlocal pending_requests, last_batch_time

                # Add request to pending batch
                future = asyncio.Future()
                pending_requests.append((request, future))

                # Check if we should process batch
                should_process = (
                    len(pending_requests) >= batch_size
                    or time.time() - last_batch_time >= max_wait_time
                )

                if should_process:
                    # Process current batch
                    current_batch = pending_requests
                    pending_requests = []
                    last_batch_time = time.time()

                    # Extract requests and futures
                    requests = [req for req, _ in current_batch]
                    futures = [fut for _, fut in current_batch]

                    try:
                        # Process batch
                        results = await func(requests)

                        # Set results for futures
                        for future, result in zip(futures, results, strict=False):
                            future.set_result(result)

                    except Exception as e:
                        # Set exception for all futures
                        for future in futures:
                            future.set_exception(e)

                # Wait for result
                return await future

            return wrapper

        return decorator


class ConnectionPool:
    """Simple connection pool for HTTP clients."""

    def __init__(self, max_connections: int = 10):
        """Initialize connection pool.

        Args:
            max_connections: Maximum number of connections
        """
        self.max_connections = max_connections
        self.available_connections = []
        self.in_use_connections = set()
        self.semaphore = asyncio.Semaphore(max_connections)

    async def get_connection(self):
        """Get a connection from the pool."""
        await self.semaphore.acquire()

        if self.available_connections:
            connection = self.available_connections.pop()
        else:
            # Create new connection (implement based on your HTTP client)
            connection = self._create_connection()

        self.in_use_connections.add(connection)
        return connection

    async def return_connection(self, connection):
        """Return a connection to the pool."""
        if connection in self.in_use_connections:
            self.in_use_connections.remove(connection)

            if len(self.available_connections) < self.max_connections:
                self.available_connections.append(connection)
            else:
                # Close excess connection
                await self._close_connection(connection)

            self.semaphore.release()

    def _create_connection(self):
        """Create a new connection."""
        # Implement based on your HTTP client library
        import aiohttp

        return aiohttp.ClientSession()

    async def _close_connection(self, connection):
        """Close a connection."""
        if hasattr(connection, "close"):
            await connection.close()


class ResponseCache:
    """Optimized response caching for specific services."""

    def __init__(self, service_name: str):
        """Initialize response cache.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.semantic_cache = get_semantic_cache()
        self.memory_cache = get_memory_cache()

    async def get_cached_inference(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str | None:
        """Get cached model inference result.

        Args:
            prompt: Input prompt
            model_name: Name of the model
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Cached response if found
        """
        # Use semantic cache for similar prompts
        context = {
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        return self.semantic_cache.get(
            query=prompt, context=context, model_used=model_name
        )

    async def cache_inference_result(
        self,
        prompt: str,
        response: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
        ttl_seconds: int = 3600,
    ) -> bool:
        """Cache model inference result.

        Args:
            prompt: Input prompt
            response: Model response
            model_name: Name of the model
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            ttl_seconds: Time to live for cache entry

        Returns:
            True if cached successfully
        """
        context = {
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        return self.semantic_cache.put(
            query=prompt,
            response=response,
            context=context,
            model_used=model_name,
            ttl_seconds=ttl_seconds,
        )

    async def get_cached_rag_result(
        self, query: str, top_k: int = 5, similarity_threshold: float = 0.7
    ) -> list[dict] | None:
        """Get cached RAG search result.

        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Similarity threshold

        Returns:
            Cached search results if found
        """
        cache_key = f"rag:{query}:{top_k}:{similarity_threshold}"
        return self.memory_cache.get(cache_key)

    async def cache_rag_result(
        self,
        query: str,
        results: list[dict],
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        ttl_seconds: int = 1800,
    ) -> None:
        """Cache RAG search result.

        Args:
            query: Search query
            results: Search results
            top_k: Number of results returned
            similarity_threshold: Similarity threshold used
            ttl_seconds: Time to live for cache entry
        """
        cache_key = f"rag:{query}:{top_k}:{similarity_threshold}"
        self.memory_cache.put(cache_key, results, ttl_seconds)


# Service-specific optimizations
def optimize_model_service():
    """Apply optimizations to model service."""
    from .model_service import LocalModelService

    optimizer = PerformanceOptimizer("model")

    # Patch model service methods
    if hasattr(LocalModelService, "generate_response"):
        original_generate = LocalModelService.generate_response

        @optimizer.cached_response(use_semantic=True, ttl_seconds=3600)
        @optimizer.timed_execution("model_generation")
        async def optimized_generate(self, request):
            return await original_generate(self, request)

        LocalModelService.generate_response = optimized_generate
        logger.info("Applied performance optimizations to model service")


def optimize_rag_service():
    """Apply optimizations to RAG service."""
    from ..rag.retriever import RAGRetriever

    optimizer = PerformanceOptimizer("rag")

    # Patch RAG retriever methods
    if hasattr(RAGRetriever, "search"):
        original_search = RAGRetriever.search

        @optimizer.cached_response(ttl_seconds=1800)
        @optimizer.timed_execution("rag_search")
        def optimized_search(
            self, query, top_k=None, metadata_filter=None, similarity_threshold=None
        ):
            return original_search(
                self, query, top_k, metadata_filter, similarity_threshold
            )

        RAGRetriever.search = optimized_search
        logger.info("Applied performance optimizations to RAG service")


def optimize_agent_service():
    """Apply optimizations to agent service."""
    from .agent_service import JerryAgent

    optimizer = PerformanceOptimizer("agent")

    # Patch agent methods
    if hasattr(JerryAgent, "process_message"):
        original_process = JerryAgent.process_message

        @optimizer.timed_execution("agent_processing")
        async def optimized_process(self, message, conversation=None):
            return await original_process(self, message, conversation)

        JerryAgent.process_message = optimized_process
        logger.info("Applied performance optimizations to agent service")


def apply_all_optimizations():
    """Apply performance optimizations to all services."""
    try:
        optimize_model_service()
    except Exception as e:
        logger.warning(f"Failed to optimize model service: {e}")

    try:
        optimize_rag_service()
    except Exception as e:
        logger.warning(f"Failed to optimize RAG service: {e}")

    try:
        optimize_agent_service()
    except Exception as e:
        logger.warning(f"Failed to optimize agent service: {e}")

    logger.info("Applied performance optimizations to all available services")


# Initialize optimizations when module is imported
if __name__ != "__main__":
    apply_all_optimizations()
