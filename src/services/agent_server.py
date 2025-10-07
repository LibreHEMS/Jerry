"""
FastAPI agent service server for Jerry AI.

This module provides a REST API server for Jerry's AI agent,
handling conversation processing and agent orchestration.
"""

import time
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import Field

from ..data.models import Conversation
from ..data.models import User
from ..services.agent_service import AgentService
from ..services.agent_service import create_agent_service
from ..services.local_model_service import LocalModelService
from ..services.model_service import ModelServiceRegistry
from ..services.tools.web_search import create_web_search_tool
from ..utils.config import Config
from ..utils.config import load_config
from ..utils.logging import get_logger
from ..utils.logging import setup_logging

logger = get_logger(__name__)

# Global services
agent_service: AgentService | None = None
model_registry = ModelServiceRegistry()
config: Config | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global config, agent_service, model_registry

    # Startup
    logger.info("Starting Agent Service Server...")

    try:
        # Load configuration
        config = load_config()
        setup_logging(config.logging)

        # Initialize model service
        local_service = LocalModelService(config.model)
        model_registry.register("local", local_service, default=True)
        await local_service.load_model()

        # Initialize agent service with tools
        tools = []

        # Add web search tool if available
        web_search_tool = create_web_search_tool()
        if web_search_tool:
            tools.append(web_search_tool)
            logger.info("Web search tool loaded")

        # Create agent service
        agent_service = create_agent_service(config.agent, local_service)
        agent_service.create_agent("default", tools=tools)

        logger.info("Agent service startup complete")

    except Exception as e:
        logger.error(f"Failed to start agent service: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Agent Service Server...")
    try:
        await model_registry.shutdown_all()
        logger.info("Agent service shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# FastAPI app with lifespan management
app = FastAPI(
    title="Jerry AI Agent Service",
    description="Internal API for Jerry's LangChain agent interactions",
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
class ConversationRequest(BaseModel):
    """Request model for conversation processing."""

    user_id: str = Field(description="Discord user ID")
    conversation_id: str = Field(description="Conversation UUID")
    message: str = Field(description="User message content")
    user_name: str = Field(default="User", description="User display name")
    channel_id: str = Field(description="Discord channel ID")
    context: dict | None = Field(default=None, description="Additional context")


class ConversationResponse(BaseModel):
    """Response model for conversation processing."""

    id: str
    response: str
    conversation_id: str
    user_id: str
    timestamp: str
    metadata: dict
    response_time_ms: int


class SummaryRequest(BaseModel):
    """Request model for conversation summarization."""

    conversation_id: str
    force: bool = Field(
        default=False, description="Force summarization even if not needed"
    )


class SummaryResponse(BaseModel):
    """Response model for conversation summarization."""

    conversation_id: str
    summary: str
    timestamp: str
    message_count: int


class HealthResponse(BaseModel):
    """Response model for health checks."""

    status: str
    healthy: bool
    agent_ready: bool
    model_loaded: bool
    tools_available: list[str]
    timestamp: int


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str
    detail: str | None = None
    timestamp: int


@app.post("/v1/chat", response_model=ConversationResponse)
async def process_conversation(request: ConversationRequest):
    """Process a conversation message through Jerry agent."""
    start_time = time.time()

    try:
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not available")

        # Create user and conversation objects
        from datetime import datetime

        user = User(
            discord_id=request.user_id,
            username=request.user_name,
            display_name=request.user_name,
            first_interaction=datetime.utcnow(),
            last_interaction=datetime.utcnow(),
        )

        conversation = Conversation(
            id=UUID(request.conversation_id),
            user_discord_id=request.user_id,
            channel_id=request.channel_id,
            started_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
        )

        # Process message through agent
        response_content, metadata = await agent_service.process_conversation(
            user=user,
            conversation=conversation,
            message_content=request.message,
            context=request.context,
        )

        response_time_ms = int((time.time() - start_time) * 1000)

        return ConversationResponse(
            id=str(UUID(request.conversation_id)),
            response=response_content,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata,
            response_time_ms=response_time_ms,
        )

    except Exception as e:
        logger.error(f"Error processing conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process conversation: {str(e)}"
        )


@app.post("/v1/conversations/{conversation_id}/summary", response_model=SummaryResponse)
async def summarize_conversation(conversation_id: str, request: SummaryRequest):
    """Generate or retrieve conversation summary."""
    try:
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not available")

        conversation_uuid = UUID(conversation_id)

        # Get conversation summary
        summary = await agent_service.summarize_conversation(conversation_uuid)

        if not summary:
            summary = "No conversation history available for summarization."

        return SummaryResponse(
            conversation_id=conversation_id,
            summary=summary,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            message_count=0,  # TODO: Get actual message count
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
    except Exception as e:
        logger.error(f"Error summarizing conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to summarize conversation: {str(e)}"
        )


@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    """Check the health status of the agent service."""
    try:
        # Check agent service
        agent_ready = agent_service is not None

        # Check model service
        model_loaded = False
        if model_registry:
            try:
                service = model_registry.get()
                health = await service.health_check()
                model_loaded = health.model_loaded and health.healthy
            except Exception:
                model_loaded = False

        # Get available tools
        tools_available = []
        if agent_service:
            try:
                agent = agent_service.get_agent("default")
                tools_available = [tool.name for tool in agent.tools]
            except Exception:
                pass

        overall_healthy = agent_ready and model_loaded

        return HealthResponse(
            status="healthy" if overall_healthy else "degraded",
            healthy=overall_healthy,
            agent_ready=agent_ready,
            model_loaded=model_loaded,
            tools_available=tools_available,
            timestamp=int(time.time()),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            healthy=False,
            agent_ready=False,
            model_loaded=False,
            tools_available=[],
            timestamp=int(time.time()),
        )


@app.get("/v1/agents")
async def list_agents():
    """List available agents."""
    try:
        if not agent_service:
            return {"agents": []}

        agents = agent_service.list_agents()

        agent_info = []
        for agent_id in agents:
            try:
                agent = agent_service.get_agent(agent_id)
                tool_names = (
                    [tool.name for tool in agent.tools]
                    if hasattr(agent, "tools")
                    else []
                )

                agent_info.append(
                    {
                        "id": agent_id,
                        "status": "ready",
                        "tools": tool_names,
                        "created": time.strftime(
                            "%Y-%m-%d %H:%M:%S UTC", time.gmtime()
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"Could not get info for agent {agent_id}: {e}")
                agent_info.append(
                    {
                        "id": agent_id,
                        "status": "error",
                        "tools": [],
                        "created": "unknown",
                    }
                )

        return {"agents": agent_info}

    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list agents")


@app.post("/v1/agents/{agent_id}/clear")
async def clear_agent_memory(agent_id: str, conversation_id: str | None = None):
    """Clear memory for an agent or specific conversation."""
    try:
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not available")

        agent = agent_service.get_agent(agent_id)

        if conversation_id:
            # Clear specific conversation
            await agent.clear_conversation_memory(UUID(conversation_id))
            return {"status": "cleared", "conversation_id": conversation_id}
        # Clear all conversations for this agent (if method exists)
        # For now, just acknowledge the request
        return {"status": "acknowledged", "agent_id": agent_id}

    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid agent ID or conversation ID format"
        )
    except Exception as e:
        logger.error(f"Error clearing agent memory: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to clear agent memory: {str(e)}"
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
        "src.services.agent_server:app",
        host="0.0.0.0",
        port=8003,
        reload=config.debug,
        log_level=config.logging.level.lower(),
    )
