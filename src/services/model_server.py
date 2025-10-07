"""
FastAPI model service server for Jerry AI.

This module provides a REST API server for AI model inference,
serving as the central model service for Jerry's self-hosted AI.
"""

import time
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import Field

from ..services.local_model_service import LocalModelService
from ..services.model_service import ChatRequest
from ..services.model_service import InferenceError
from ..services.model_service import ModelNotLoadedError
from ..services.model_service import ModelService
from ..services.model_service import ModelServiceRegistry
from ..utils.config import Config
from ..utils.config import load_config
from ..utils.logging import get_logger
from ..utils.logging import setup_logging

logger = get_logger(__name__)

# Global registry for model services
model_registry = ModelServiceRegistry()
config: Config | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global config, model_registry

    # Startup
    logger.info("Starting Model Service Server...")

    try:
        # Load configuration
        config = load_config()
        setup_logging(config.logging)

        # Initialize local model service
        local_service = LocalModelService(config.model)
        model_registry.register("local", local_service, default=True)

        # Load the default model
        await local_service.load_model()
        logger.info("Model service startup complete")

    except Exception as e:
        logger.error(f"Failed to start model service: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Model Service Server...")
    try:
        await model_registry.shutdown_all()
        logger.info("Model service shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# FastAPI app with lifespan management
app = FastAPI(
    title="Jerry AI Model Service",
    description="Internal API for Jerry's AI model interactions",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatCompletionRequest(BaseModel):
    """Request model for chat completions."""

    messages: list[dict]
    model: str = "local"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    stream: bool = False
    stop: list[str] | None = None
    user: str | None = None


class ChatCompletionResponse(BaseModel):
    """Response model for chat completions."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict


class HealthResponse(BaseModel):
    """Response model for health checks."""

    status: str
    healthy: bool
    model_loaded: bool
    model_name: str
    memory_usage_mb: int
    uptime_seconds: int
    timestamp: int


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str
    detail: str | None = None
    timestamp: int


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """Generate chat completion using the model service."""
    start_time = time.time()

    try:
        # Get model service
        service = model_registry.get(
            request.model if request.model != "local" else None
        )

        if not service.is_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")

        # Convert request to internal format
        chat_request = ChatRequest(
            messages=[
                {"role": msg["role"], "content": msg["content"]}
                for msg in request.messages
            ],
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
            stop=request.stop,
            user_id=request.user,
        )

        # Handle streaming vs non-streaming
        if request.stream:
            return StreamingResponse(
                _stream_chat_completion(service, chat_request), media_type="text/plain"
            )

        # Generate response
        response = await service.chat_completion(chat_request)

        # Convert to OpenAI-compatible format
        return ChatCompletionResponse(
            id=response.id,
            created=int(time.time()),
            model=response.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": response.role,
                        "content": response.content,
                    },
                    "finish_reason": response.finish_reason,
                }
            ],
            usage={
                "prompt_tokens": 0,  # TODO: Implement token counting
                "completion_tokens": response.tokens_used,
                "total_tokens": response.tokens_used,
            },
        )

    except ModelNotLoadedError:
        raise HTTPException(status_code=503, detail="Model service not available")
    except InferenceError as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in chat completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Chat completion took {duration_ms:.2f}ms")


async def _stream_chat_completion(service: ModelService, request: ChatRequest):
    """Stream chat completion responses."""
    try:
        async for chunk in service.chat_completion_stream(request):
            # Convert to OpenAI-compatible server-sent events format
            data = {
                "id": chunk.id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": chunk.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk.content},
                        "finish_reason": chunk.finish_reason,
                    }
                ],
            }
            yield f"data: {data}\n\n"

        # Send final chunk
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error in streaming: {e}", exc_info=True)
        error_data = {"error": str(e), "timestamp": int(time.time())}
        yield f"data: {error_data}\n\n"


@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    """Check the health status of the model service."""
    try:
        service = model_registry.get()
        health = await service.health_check()

        return HealthResponse(
            status="healthy" if health.healthy else "unhealthy",
            healthy=health.healthy,
            model_loaded=health.model_loaded,
            model_name=health.model_name,
            memory_usage_mb=health.memory_usage_mb,
            uptime_seconds=health.uptime_seconds,
            timestamp=int(time.time()),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            healthy=False,
            model_loaded=False,
            model_name="unknown",
            memory_usage_mb=0,
            uptime_seconds=0,
            timestamp=int(time.time()),
        )


@app.get("/v1/models")
async def list_models():
    """List available models."""
    try:
        models = model_registry.list_services()
        model_info = []

        for model_name in models:
            try:
                service = model_registry.get(model_name)
                health = await service.health_check()

                model_info.append(
                    {
                        "id": model_name,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "jerry-self-hosted",
                        "ready": health.model_loaded,
                        "name": health.model_name,
                    }
                )
            except Exception as e:
                logger.warning(f"Could not get info for model {model_name}: {e}")
                model_info.append(
                    {
                        "id": model_name,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "jerry-self-hosted",
                        "ready": False,
                        "name": model_name,
                    }
                )

        return {"object": "list", "data": model_info}

    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list models")


@app.post("/v1/models/{model_name}/load")
async def load_model(model_name: str, background_tasks: BackgroundTasks):
    """Load a specific model."""
    try:
        service = model_registry.get(model_name)

        if service.is_loaded:
            return {"status": "already_loaded", "model": model_name}

        # Load model in background
        background_tasks.add_task(_load_model_background, service, model_name)

        return {"status": "loading", "model": model_name}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load model")


@app.post("/v1/models/{model_name}/unload")
async def unload_model(model_name: str):
    """Unload a specific model."""
    try:
        service = model_registry.get(model_name)

        if not service.is_loaded:
            return {"status": "already_unloaded", "model": model_name}

        await service.unload_model()

        return {"status": "unloaded", "model": model_name}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error unloading model {model_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unload model")


async def _load_model_background(service: ModelService, model_name: str):
    """Load model in background task."""
    try:
        logger.info(f"Loading model {model_name} in background...")
        await service.load_model()
        logger.info(f"Model {model_name} loaded successfully")
    except Exception as e:
        logger.error(
            f"Failed to load model {model_name} in background: {e}", exc_info=True
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": int(time.time()),
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "detail": str(exc) if config and config.debug else None,
        "timestamp": int(time.time()),
    }


if __name__ == "__main__":
    import uvicorn

    # Load configuration
    config = load_config()
    setup_logging(config.logging)

    # Run the server
    uvicorn.run(
        "src.services.model_server:app",
        host="0.0.0.0",
        port=8001,
        reload=config.debug,
        log_level=config.logging.level.lower(),
    )
