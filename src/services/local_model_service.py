"""
Local model service implementation using llama.cpp for Jerry AI.

This module provides a local AI model service implementation that uses
llama.cpp for efficient local inference with GGUF format models.
"""

import asyncio
import os
import time
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import psutil

try:
    from llama_cpp import Llama
    from llama_cpp.llama_types import ChatCompletionRequestMessage

    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

    # Type stubs for when llama.cpp is not available
    class Llama:
        pass

    class ChatCompletionRequestMessage:
        pass


from ..utils.config import ModelConfig as ConfigModelConfig
from ..utils.logging import PerformanceTimer
from ..utils.logging import get_logger
from .model_service import ChatRequest
from .model_service import ChatResponse
from .model_service import HealthStatus
from .model_service import InferenceError
from .model_service import ModelConfig
from .model_service import ModelLoadError
from .model_service import ModelNotLoadedError
from .model_service import ModelService
from .model_service import StreamChunk

logger = get_logger(__name__)


class LocalModelService(ModelService):
    """Local model service implementation using llama.cpp."""

    def __init__(self, config: ConfigModelConfig):
        """Initialize the local model service."""
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Install it with: pip install llama-cpp-python"
            )

        # Convert config to ModelConfig
        model_config = ModelConfig(
            name=config.model_name,
            type="chat",
            model_path=self._resolve_model_path(config.model_name, config.quantization),
            context_length=config.context_length,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            quantization=config.quantization,
        )

        super().__init__(model_config)

        self.service_config = config
        self._llama: Llama | None = None
        self._load_time: float | None = None
        self._request_count = 0
        self._last_request_time: str | None = None

    async def load_model(self) -> None:
        """Load the llama.cpp model."""
        if self._is_loaded:
            logger.warning(f"Model {self.config.name} is already loaded")
            return

        logger.info(f"Loading model: {self.config.name}")
        logger.info(f"Model path: {self.config.model_path}")

        # Check if model file exists
        if not Path(self.config.model_path).exists():
            raise ModelLoadError(f"Model file not found: {self.config.model_path}")

        try:
            with PerformanceTimer(logger, f"Model loading ({self.config.name})"):
                # Run model loading in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self._llama = await loop.run_in_executor(None, self._load_llama_model)

            self._is_loaded = True
            self._load_time = time.time()
            logger.info(f"Model {self.config.name} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model {self.config.name}: {e}", exc_info=True)
            raise ModelLoadError(f"Failed to load model: {e}")

    def _load_llama_model(self) -> "Llama":
        """Load the llama model (runs in thread pool)."""
        return Llama(
            model_path=self.config.model_path,
            n_ctx=self.config.context_length,
            n_threads=getattr(self.config, "threads", 4),
            n_gpu_layers=getattr(self.config, "gpu_layers", 0),
            verbose=False,  # Set to True for debugging
        )

    async def unload_model(self) -> None:
        """Unload the model from memory."""
        if not self._is_loaded:
            logger.warning(f"Model {self.config.name} is not loaded")
            return

        logger.info(f"Unloading model: {self.config.name}")

        try:
            # Clean up llama instance
            if self._llama:
                # llama.cpp doesn't have explicit cleanup, just delete reference
                self._llama = None

            self._is_loaded = False
            self._load_time = None
            logger.info(f"Model {self.config.name} unloaded successfully")

        except Exception as e:
            logger.error(
                f"Error unloading model {self.config.name}: {e}", exc_info=True
            )

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion response."""
        if not self._is_loaded or not self._llama:
            raise ModelNotLoadedError(f"Model {self.config.name} is not loaded")

        self._request_count += 1
        self._last_request_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        start_time = time.time()

        try:
            with PerformanceTimer(logger, "Chat completion"):
                # Convert messages to llama.cpp format
                messages = [
                    ChatCompletionRequestMessage(
                        role=msg["role"], content=msg["content"]
                    )
                    for msg in request.messages
                ]

                # Run inference in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, self._generate_completion, messages, request
                )

            response_time_ms = int((time.time() - start_time) * 1000)

            # Extract response content
            content = response["choices"][0]["message"]["content"]
            finish_reason = response["choices"][0]["finish_reason"]

            return ChatResponse(
                id=str(uuid4()),
                model=self.config.name,
                content=content,
                role="assistant",
                finish_reason=finish_reason,
                tokens_used=response.get("usage", {}).get("completion_tokens", 0),
                response_time_ms=response_time_ms,
                metadata={
                    "total_tokens": response.get("usage", {}).get("total_tokens", 0),
                    "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                },
            )

        except Exception as e:
            logger.error(f"Chat completion failed: {e}", exc_info=True)
            raise InferenceError(f"Chat completion failed: {e}")

    def _generate_completion(
        self, messages: list["ChatCompletionRequestMessage"], request: ChatRequest
    ) -> dict:
        """Generate completion (runs in thread pool)."""
        return self._llama.create_chat_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stop=request.stop,
        )

    async def chat_completion_stream(
        self, request: ChatRequest
    ) -> AsyncIterator[StreamChunk]:
        """Generate a streaming chat completion response."""
        if not self._is_loaded or not self._llama:
            raise ModelNotLoadedError(f"Model {self.config.name} is not loaded")

        self._request_count += 1
        self._last_request_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        try:
            # Convert messages to llama.cpp format
            messages = [
                ChatCompletionRequestMessage(role=msg["role"], content=msg["content"])
                for msg in request.messages
            ]

            # Generate streaming response
            chunk_id = str(uuid4())

            # Run streaming in thread pool with queue for communication
            queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            # Start streaming task
            task = loop.run_in_executor(
                None, self._generate_streaming, messages, request, queue
            )

            try:
                while True:
                    # Get chunk from queue
                    chunk_data = await queue.get()

                    if chunk_data is None:  # End of stream
                        break

                    if isinstance(chunk_data, Exception):  # Error occurred
                        raise chunk_data

                    yield StreamChunk(
                        id=chunk_id,
                        model=self.config.name,
                        content=chunk_data["delta"],
                        finish_reason=chunk_data.get("finish_reason"),
                        delta_time_ms=chunk_data.get("delta_time_ms", 0),
                    )

            finally:
                # Ensure the task completes
                await task

        except Exception as e:
            logger.error(f"Streaming chat completion failed: {e}", exc_info=True)
            raise InferenceError(f"Streaming completion failed: {e}")

    def _generate_streaming(
        self,
        messages: list["ChatCompletionRequestMessage"],
        request: ChatRequest,
        queue: asyncio.Queue,
    ) -> None:
        """Generate streaming completion (runs in thread pool)."""
        try:
            stream = self._llama.create_chat_completion(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stop=request.stop,
                stream=True,
            )

            last_time = time.time()

            for chunk in stream:
                current_time = time.time()
                delta_time_ms = int((current_time - last_time) * 1000)
                last_time = current_time

                choice = chunk["choices"][0]
                delta = choice.get("delta", {})
                content = delta.get("content", "")

                # Put chunk in queue
                asyncio.run_coroutine_threadsafe(
                    queue.put(
                        {
                            "delta": content,
                            "finish_reason": choice.get("finish_reason"),
                            "delta_time_ms": delta_time_ms,
                        }
                    ),
                    asyncio.get_event_loop(),
                )

            # Signal end of stream
            asyncio.run_coroutine_threadsafe(queue.put(None), asyncio.get_event_loop())

        except Exception as e:
            # Signal error
            asyncio.run_coroutine_threadsafe(queue.put(e), asyncio.get_event_loop())

    async def health_check(self) -> HealthStatus:
        """Check the health status of the local model service."""
        try:
            # Get memory usage
            process = psutil.Process()
            memory_usage_mb = int(process.memory_info().rss / 1024 / 1024)

            # Calculate uptime
            uptime_seconds = (
                int(time.time() - self._load_time) if self._load_time else 0
            )

            return HealthStatus(
                healthy=self._is_loaded and self._llama is not None,
                model_loaded=self._is_loaded,
                model_name=self.config.name,
                memory_usage_mb=memory_usage_mb,
                uptime_seconds=uptime_seconds,
                last_request_time=self._last_request_time,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return HealthStatus(
                healthy=False,
                model_loaded=False,
                model_name=self.config.name,
                memory_usage_mb=0,
                uptime_seconds=0,
                error_message=str(e),
            )

    def _resolve_model_path(self, model_name: str, quantization: str) -> str:
        """Resolve the full path to the model file."""
        # Standard model file naming convention
        model_filename = f"{model_name}-{quantization.lower()}.gguf"

        # Check several common locations
        possible_paths = [
            Path("./models") / model_filename,
            Path("./data/models") / model_filename,
            Path(f"./models/{model_name}") / model_filename,
            Path.home() / ".cache/jerry/models" / model_filename,
            Path(f"/tmp/jerry/models/{model_filename}"),
        ]

        # Check environment variable
        model_dir = os.getenv("JERRY_MODEL_DIR")
        if model_dir:
            possible_paths.insert(0, Path(model_dir) / model_filename)

        # Find existing file
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found model at: {path}")
                return str(path)

        # If not found, return the first path (will fail at load time with clear error)
        default_path = possible_paths[0]
        logger.warning(
            "Model file not found. Expected locations:\n"
            + "\n".join(f"  - {path}" for path in possible_paths)
            + f"\nUsing: {default_path}"
        )

        return str(default_path)


def create_local_model_service(config: ConfigModelConfig) -> LocalModelService:
    """Create a local model service instance."""
    return LocalModelService(config)
