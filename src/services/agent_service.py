"""
LangChain agent configuration and service for Jerry AI.

This module provides the main agent service that orchestrates
LangChain agents, tools, and conversation management.
"""

import asyncio
from typing import TYPE_CHECKING
from typing import Any
from uuid import UUID

if TYPE_CHECKING:
    from langchain.agents import AgentExecutor
    from langchain_core.language_models.llms import LLM
    from langchain_core.tools import Tool

try:
    from langchain.agents import AgentExecutor
    from langchain.agents import create_tool_calling_agent
    from langchain.memory import ConversationBufferWindowMemory
    from langchain_core.language_models.llms import LLM
    from langchain_core.messages import AIMessage
    from langchain_core.messages import HumanMessage
    from langchain_core.tools import Tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    AgentExecutor = None
    Tool = None
    LLM = None

from ..data.models import Conversation
from ..data.models import User
from ..prompts.system_prompts import JerryPrompts
from ..prompts.system_prompts import extract_user_context
from ..prompts.system_prompts import format_conversation_history
from ..services.model_service import ChatMessage
from ..services.model_service import ChatRequest
from ..services.model_service import ModelService
from ..utils.config import AgentConfig
from ..utils.logging import PerformanceTimer
from ..utils.logging import get_logger
from ..utils.metrics import get_metrics_collector
from ..utils.performance import PerformanceOptimizer
from ..utils.performance import ResponseCache

logger = get_logger(__name__)


class JerryAgent:
    """Jerry AI agent using LangChain."""

    def __init__(
        self,
        config: AgentConfig,
        model_service: ModelService,
        tools: list | None = None,
    ):
        """Initialize Jerry agent."""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. "
                "Install it with: pip install langchain langchain-core"
            )

        self.config = config
        self.model_service = model_service
        self.tools = tools or []

        # Initialize performance optimizations
        self.optimizer = PerformanceOptimizer("agent")
        self.response_cache = ResponseCache("agent")
        self.metrics = get_metrics_collector("agent")

        # Initialize memory for conversations
        self.conversations: dict[UUID, ConversationBufferWindowMemory] = {}

        # Agent executor will be created when needed
        self._agent_executor: Any | None = None

    @PerformanceOptimizer("agent").timed_execution("message_processing")
    async def process_message(
        self,
        user: User,
        conversation: Conversation,
        message_content: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Process a message through the Jerry agent."""
        try:
            with PerformanceTimer(logger, "Agent message processing"):
                # Record metrics
                self.metrics.increment_counter("messages_processed")

                # Get or create conversation memory
                memory = self._get_conversation_memory(conversation.id)

                # Extract user context from conversation
                user_context = await self._extract_user_context(conversation, context)

                # Determine expertise focus
                expertise_focus = await self._determine_expertise_focus(message_content)

                # Create or update agent executor
                agent_executor = await self._get_agent_executor(
                    user_context=user_context, expertise_focus=expertise_focus
                )

                # Process the message
                response = await agent_executor.ainvoke(
                    {
                        "input": message_content,
                        "chat_history": memory.chat_memory.messages,
                    }
                )

                # Extract response content and metadata
                response_content = response.get(
                    "output",
                    "Sorry mate, I'm having trouble processing that right now.",
                )
                response_metadata = {
                    "expertise_focus": expertise_focus,
                    "tools_used": response.get("tools_used", []),
                    "confidence": response.get("confidence", "medium"),
                    "user_context": user_context,
                }

                # Update conversation memory
                memory.chat_memory.add_user_message(message_content)
                memory.chat_memory.add_ai_message(response_content)

                # Check if conversation needs summarization
                if (
                    len(memory.chat_memory.messages)
                    >= self.config.summarization_threshold
                ):
                    await self.summarize_conversation(conversation.id)

                return response_content, response_metadata

        except Exception as e:
            logger.error(f"Error processing message through agent: {e}", exc_info=True)
            return self._get_fallback_response(message_content), {"error": str(e)}

    async def _extract_user_context(
        self,
        conversation: Conversation,
        additional_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract user context from conversation history."""
        # Base context
        context = {
            "user_id": conversation.user_discord_id,
            "conversation_id": str(conversation.id),
            "location": "Australia",
            "conversation_started": conversation.started_at.isoformat(),
        }

        # Add additional context if provided
        if additional_context:
            context.update(additional_context)

        # Extract context from conversation memory if available
        memory = self.conversations.get(conversation.id)
        if memory and memory.chat_memory.messages:
            # Convert LangChain messages to simple format for analysis
            messages = []
            for msg in memory.chat_memory.messages:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})

            # Extract context from message history
            extracted_context = extract_user_context(messages)
            context.update(extracted_context)

        return context

    async def _determine_expertise_focus(self, message_content: str) -> str | None:
        """Determine which expertise area to focus on based on the message."""
        message_lower = message_content.lower()

        # Solar-related keywords
        solar_keywords = [
            "solar",
            "panel",
            "pv",
            "photovoltaic",
            "inverter",
            "installation",
            "roof",
        ]
        if any(keyword in message_lower for keyword in solar_keywords):
            return "solar"

        # Battery-related keywords
        battery_keywords = [
            "battery",
            "storage",
            "powerwall",
            "backup",
            "blackout",
            "grid",
        ]
        if any(keyword in message_lower for keyword in battery_keywords):
            return "battery"

        # Automation-related keywords
        automation_keywords = [
            "automation",
            "smart",
            "control",
            "timer",
            "load",
            "hot water",
            "pool",
        ]
        if any(keyword in message_lower for keyword in automation_keywords):
            return "automation"

        # Default to None for general conversation
        return None

    async def _get_agent_executor(
        self, user_context: dict[str, Any], expertise_focus: str | None = None
    ) -> Any:
        """Get or create an agent executor with current context."""
        # Create LangChain-compatible LLM wrapper
        llm = ModelServiceLLM(self.model_service)

        # Create prompt template
        prompt = JerryPrompts.create_chat_template(
            user_location=user_context.get("location", "Australia"),
            conversation_context=f"User context: {user_context}",
            expertise_focus=expertise_focus,
        )

        # Create agent with tools
        agent = create_tool_calling_agent(llm, self.tools, prompt)

        # Create agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
        )

    def _get_conversation_memory(
        self, conversation_id: UUID
    ) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for a conversation."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationBufferWindowMemory(
                k=self.config.max_conversation_length, return_messages=True
            )

        return self.conversations[conversation_id]

    async def summarize_conversation(self, conversation_id: UUID) -> str:
        """Summarize a conversation and update memory."""
        memory = self.conversations.get(conversation_id)
        if not memory or not memory.chat_memory.messages:
            return ""

        try:
            # Get conversation history as text
            messages = []
            for msg in memory.chat_memory.messages:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})

            conversation_text = format_conversation_history(messages)

            # Create summarization prompt
            summary_template = JerryPrompts.create_summarization_template()

            # Generate summary using model service
            summary_messages = [
                ChatMessage(
                    role="user",
                    content=summary_template.format(conversation=conversation_text),
                )
            ]

            summary_request = ChatRequest(
                messages=summary_messages,
                model="local",
                temperature=0.3,
                max_tokens=256,
            )

            response = await self.model_service.chat_completion(summary_request)
            summary = response.content

            # Clear old messages and add summary
            memory.clear()
            memory.chat_memory.add_ai_message(
                f"Previous conversation summary: {summary}"
            )

            logger.info(f"Summarized conversation {conversation_id}")
            return summary

        except Exception as e:
            logger.error(f"Failed to summarize conversation {conversation_id}: {e}")
            return ""

    async def generate_conversation_summary(self, conversation_id: UUID) -> str:
        """Generate a new conversation summary without updating memory."""
        memory = self.conversations.get(conversation_id)
        if not memory or not memory.chat_memory.messages:
            return "No conversation history available."

        try:
            # Get conversation history as text
            messages = []
            for msg in memory.chat_memory.messages:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})

            conversation_text = format_conversation_history(messages)

            # Create summarization prompt
            summary_template = JerryPrompts.create_summarization_template()

            # Generate summary using model service
            summary_messages = [
                ChatMessage(
                    role="user",
                    content=summary_template.format(conversation=conversation_text),
                )
            ]

            summary_request = ChatRequest(
                messages=summary_messages,
                model="local",
                temperature=0.3,
                max_tokens=256,
            )

            response = await self.model_service.chat_completion(summary_request)
            return response.content

        except Exception as e:
            logger.error(
                f"Failed to generate summary for conversation {conversation_id}: {e}"
            )
            return "Unable to generate conversation summary at this time."

    def _get_fallback_response(self, message_content: str) -> str:
        """Get a fallback response when agent processing fails."""
        message_lower = message_content.lower()

        # Greeting detection
        greetings = ["hello", "hi", "hey", "g'day", "gday"]
        if any(greeting in message_lower for greeting in greetings):
            return JerryPrompts.get_conversation_starter("greeting")

        # Topic-specific fallbacks
        if any(word in message_lower for word in ["solar", "panel"]):
            return JerryPrompts.get_conversation_starter("solar_interest")
        if any(word in message_lower for word in ["battery", "storage"]):
            return JerryPrompts.get_conversation_starter("battery_interest")
        if any(word in message_lower for word in ["automation", "smart"]):
            return JerryPrompts.get_conversation_starter("automation_interest")

        # Generic fallback
        return (
            "G'day! I'm Jerry, your renewable energy advisor. "
            "I'm having a bit of trouble processing your question right now, "
            "but I'm here to help with solar panels, batteries, and home automation. "
            "Could you rephrase your question for me?"
        )

    async def clear_conversation_memory(self, conversation_id: UUID) -> None:
        """Clear memory for a specific conversation."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].clear()
            logger.info(f"Cleared memory for conversation {conversation_id}")

    async def get_conversation_summary(self, conversation_id: UUID) -> str | None:
        """Get a summary of a conversation."""
        return await self.generate_conversation_summary(conversation_id)


class ModelServiceLLM(LLM):
    """LangChain LLM wrapper for ModelService."""

    def __init__(self, model_service: ModelService):
        super().__init__()
        self.model_service = model_service

    def _call(self, prompt: str, stop: list[str] | None = None, **kwargs) -> str:
        """Call the model service synchronously."""
        # Convert to async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._acall(prompt, stop, **kwargs))
        finally:
            loop.close()

    async def _acall(self, prompt: str, stop: list[str] | None = None, **kwargs) -> str:
        """Call the model service asynchronously."""
        try:
            request = ChatRequest(
                messages=[ChatMessage(role="user", content=prompt)],
                model="local",
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 512),
                stop=stop,
            )

            response = await self.model_service.chat_completion(request)
            return response.content

        except Exception as e:
            logger.error(f"Error in ModelServiceLLM: {e}")
            return "I'm having trouble processing that request right now."

    @property
    def _llm_type(self) -> str:
        """Return identifier for the LLM type."""
        return "jerry_model_service"


class AgentService:
    """Service for managing Jerry AI agents."""

    def __init__(self, config: AgentConfig, model_service: ModelService):
        self.config = config
        self.model_service = model_service
        self.agents: dict[str, JerryAgent] = {}

    def create_agent(self, agent_id: str, tools: list | None = None) -> JerryAgent:
        """Create a new Jerry agent instance."""
        agent = JerryAgent(
            config=self.config, model_service=self.model_service, tools=tools or []
        )

        self.agents[agent_id] = agent
        logger.info(f"Created agent: {agent_id}")
        return agent

    def get_agent(self, agent_id: str = "default") -> JerryAgent:
        """Get an existing agent or create a default one."""
        if agent_id not in self.agents:
            self.create_agent(agent_id)

        return self.agents[agent_id]

    async def process_conversation(
        self,
        user: User,
        conversation: Conversation,
        message_content: str,
        agent_id: str = "default",
        context: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Process a conversation message through an agent."""
        agent = self.get_agent(agent_id)
        return await agent.process_message(user, conversation, message_content, context)

    async def summarize_conversation(
        self, conversation_id: UUID, agent_id: str = "default"
    ) -> str | None:
        """Summarize a conversation."""
        agent = self.get_agent(agent_id)
        return await agent.get_conversation_summary(conversation_id)

    def list_agents(self) -> list[str]:
        """List all active agent IDs."""
        return list(self.agents.keys())


def create_agent_service(
    config: AgentConfig, model_service: ModelService
) -> AgentService:
    """Create an agent service instance."""
    return AgentService(config, model_service)
