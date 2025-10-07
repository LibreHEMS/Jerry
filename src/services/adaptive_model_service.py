"""
CPU-only local model service implementation for Jerry AI.

This module provides a lightweight model service that can work
without GPU dependencies or complex compilation requirements.
"""

from collections.abc import AsyncIterator

import httpx

from ..services.model_service import ChatRequest
from ..services.model_service import ChatResponse
from ..services.model_service import ModelConfig
from ..services.model_service import ModelService
from ..services.model_service import ModelType
from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class OpenAICompatibleModelService(ModelService):
    """OpenAI-compatible model service for external APIs."""

    def __init__(self, config: Config):
        """Initialize the OpenAI-compatible model service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.api_key = config.openai_api_key
        self.base_url = config.openai_base_url or "https://api.openai.com/v1"
        self.model_name = config.openai_model or "gpt-4"

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Generate a response using OpenAI-compatible API.
        
        Args:
            request: Chat completion request
            
        Returns:
            Model response
        """
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 512,
            "stream": False
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            return ChatResponse(
                id=data.get("id", "openai-response"),
                content=content,
                model=self.model_name,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                finish_reason=data["choices"][0].get("finish_reason", "stop")
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling model API: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def generate_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """Generate streaming response using OpenAI-compatible API.
        
        Args:
            request: Chat completion request
            
        Yields:
            Response chunks
        """
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 512,
            "stream": True
        }

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            logger.error(f"HTTP error in streaming: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            raise

    async def is_healthy(self) -> bool:
        """Check if the model service is healthy.
        
        Returns:
            True if service is healthy
        """
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False

    async def get_available_models(self) -> list[ModelConfig]:
        """Get list of available models.
        
        Returns:
            List of available model configurations
        """
        try:
            response = await self.client.get(f"{self.base_url}/models")
            if response.status_code == 200:
                data = response.json()
                models = []
                for model_data in data.get("data", []):
                    models.append(ModelConfig(
                        name=model_data["id"],
                        type=ModelType.CHAT,
                        model_path="",  # Not applicable for API models
                        context_length=4096,  # Default, can be overridden
                    ))
                return models
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")

        return []


class NoOpModelService(ModelService):
    """No-operation model service for development/testing."""

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        """Generate a mock response.
        
        Args:
            request: Chat completion request
            
        Returns:
            Mock model response
        """
        user_message = request.messages[-1].content if request.messages else "Hello"

        mock_response = (
            f"G'day mate! I'm Jerry, your renewable energy advisor. "
            f"You asked about: '{user_message}'. "
            f"I'd love to help with your energy questions, but I'm currently running "
            f"in development mode without a proper model backend. "
            f"For real advice, please configure a model service!"
        )

        return ChatResponse(
            id="mock-response",
            content=mock_response,
            model="mock-jerry",
            tokens_used=60,
            finish_reason="stop"
        )

    async def generate_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """Generate mock streaming response.
        
        Args:
            request: Chat completion request
            
        Yields:
            Mock response chunks
        """
        response = await self.generate_response(request)
        words = response.content.split()

        for word in words:
            yield word + " "

    async def is_healthy(self) -> bool:
        """Mock service is always healthy.
        
        Returns:
            Always True
        """
        return True

    async def get_available_models(self) -> list[ModelConfig]:
        """Get mock model configuration.
        
        Returns:
            List with mock model config
        """
        return [ModelConfig(
            name="mock-jerry",
            type=ModelType.CHAT,
            model_path="",
            context_length=4096,
        )]


def create_model_service(config: Config) -> ModelService:
    """Factory function to create the appropriate model service.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured model service instance
    """
    model_type = getattr(config, 'model_type', 'noop').lower()

    if model_type == 'openai' and hasattr(config, 'openai_api_key'):
        logger.info("Creating OpenAI-compatible model service")
        return OpenAICompatibleModelService(config)
    if model_type == 'llama_cpp':
        # Try to import llama-cpp-python, fallback if not available
        try:
            from .local_model_service import LlamaCppModelService
            logger.info("Creating llama-cpp model service")
            return LlamaCppModelService(config)
        except ImportError:
            logger.warning("llama-cpp-python not available, falling back to NoOp service")
            return NoOpModelService()
    else:
        logger.info("Creating NoOp model service for development")
        return NoOpModelService()
