"""Integration tests for agent with RAG retrieval."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest


class TestAgentRAGIntegration:
    """Test agent service integration with RAG retrieval."""

    @pytest.fixture
    def sample_rag_results(self):
        """Sample RAG search results."""
        return {
            "results": [
                {
                    "content": "Solar panels convert sunlight into electricity through photovoltaic cells.",
                    "metadata": {"source": "solar_guide.pdf", "page": 1},
                    "relevance_score": 0.92,
                },
                {
                    "content": "The efficiency of modern solar panels ranges from 15% to 22%.",
                    "metadata": {"source": "efficiency_report.pdf", "page": 3},
                    "relevance_score": 0.85,
                },
            ],
            "query_embedding_time_ms": 50,
            "search_time_ms": 120,
            "total_results": 2,
        }

    @pytest.mark.asyncio
    async def test_agent_uses_rag_for_knowledge_questions(self, sample_rag_results):
        """Test that agent retrieves and uses relevant knowledge."""

        with (
            patch("src.services.agent_service.rag_service") as mock_rag,
            patch("src.services.agent_service.model_service") as mock_model,
        ):
            # Mock RAG search
            mock_rag.search = AsyncMock(return_value=sample_rag_results)

            # Mock model response
            mock_model.generate = AsyncMock(
                return_value={
                    "text": "Based on the information I found, solar panels work by converting sunlight into electricity through photovoltaic cells. Modern panels have an efficiency of 15-22%.",
                    "tokens_used": 45,
                    "response_time_ms": 300,
                    "model_used": "local-llm",
                }
            )

            try:
                from src.services.agent_service import AgentService

                agent = AgentService()

                response = await agent.chat(
                    user_id="user123",
                    message="How do solar panels work?",
                    channel_id="channel123",
                )

                # Verify RAG was called
                mock_rag.search.assert_called_once()

                # Verify model was called with context
                mock_model.generate.assert_called_once()
                model_call_args = mock_model.generate.call_args[1]
                prompt = model_call_args["prompt"]

                # Should include retrieved context in prompt
                assert "photovoltaic cells" in prompt
                assert "efficiency" in prompt

                # Response should include sources
                assert "sources_used" in response
                assert len(response["sources_used"]) > 0

            except ImportError:
                pytest.fail(
                    "Agent service not implemented yet - this is expected in TDD"
                )

    @pytest.mark.asyncio
    async def test_agent_handles_no_rag_results(self):
        """Test agent behavior when no relevant documents are found."""

        with (
            patch("src.services.agent_service.rag_service") as mock_rag,
            patch("src.services.agent_service.model_service") as mock_model,
        ):
            # Mock empty RAG results
            mock_rag.search = AsyncMock(
                return_value={
                    "results": [],
                    "query_embedding_time_ms": 40,
                    "search_time_ms": 80,
                    "total_results": 0,
                }
            )

            # Mock model response without context
            mock_model.generate = AsyncMock(
                return_value={
                    "text": "I don't have specific information about that topic in my knowledge base.",
                    "tokens_used": 20,
                    "response_time_ms": 200,
                    "model_used": "local-llm",
                }
            )

            try:
                from src.services.agent_service import AgentService

                agent = AgentService()

                response = await agent.chat(
                    user_id="user123",
                    message="What's the weather on Mars?",
                    channel_id="channel123",
                )

                # Should still respond even without RAG results
                assert "message" in response
                assert response["sources_used"] == []

            except ImportError:
                pytest.fail(
                    "Agent service not implemented yet - this is expected in TDD"
                )

    @pytest.mark.asyncio
    async def test_agent_conversation_memory_with_rag(self, sample_rag_results):
        """Test that agent maintains conversation memory while using RAG."""

        with (
            patch("src.services.agent_service.rag_service") as mock_rag,
            patch("src.services.agent_service.model_service") as mock_model,
            patch("src.services.agent_service.conversation_memory") as mock_memory,
        ):
            mock_rag.search = AsyncMock(return_value=sample_rag_results)
            mock_model.generate = AsyncMock(
                return_value={
                    "text": "Response with context",
                    "tokens_used": 30,
                    "response_time_ms": 250,
                    "model_used": "local-llm",
                }
            )

            # Mock memory
            mock_memory.get_conversation_history = AsyncMock(
                return_value=[
                    {"role": "user", "content": "Tell me about solar panels"},
                    {
                        "role": "assistant",
                        "content": "Solar panels convert sunlight to electricity",
                    },
                ]
            )
            mock_memory.add_message = AsyncMock()

            try:
                from src.services.agent_service import AgentService

                agent = AgentService()

                await agent.chat(
                    user_id="user123",
                    message="How efficient are they?",
                    channel_id="channel123",
                )

                # Should retrieve conversation history
                mock_memory.get_conversation_history.assert_called_once()

                # Should add new messages to memory
                assert (
                    mock_memory.add_message.call_count >= 2
                )  # user message + assistant response

            except ImportError:
                pytest.fail(
                    "Agent service not implemented yet - this is expected in TDD"
                )

    @pytest.mark.asyncio
    async def test_agent_tool_usage_with_rag(self):
        """Test that agent can use tools alongside RAG retrieval."""

        with (
            patch("src.services.agent_service.rag_service") as mock_rag,
            patch("src.services.agent_service.web_search_tool") as mock_web_tool,
            patch("src.services.agent_service.model_service") as mock_model,
        ):
            # Mock RAG with limited results
            mock_rag.search = AsyncMock(
                return_value={
                    "results": [],
                    "query_embedding_time_ms": 30,
                    "search_time_ms": 60,
                    "total_results": 0,
                }
            )

            # Mock web search tool
            mock_web_tool.search = AsyncMock(
                return_value={
                    "results": ["Current solar panel prices from web search"],
                    "source": "web_search",
                }
            )

            mock_model.generate = AsyncMock(
                return_value={
                    "text": "Based on current market data, solar panel prices vary...",
                    "tokens_used": 40,
                    "response_time_ms": 400,
                    "model_used": "local-llm",
                }
            )

            try:
                from src.services.agent_service import AgentService

                agent = AgentService()

                response = await agent.chat(
                    user_id="user123",
                    message="What are current solar panel prices?",
                    channel_id="channel123",
                )

                # Should have used web search tool when RAG had no results
                assert "tools_used" in response
                assert len(response["tools_used"]) > 0

            except ImportError:
                pytest.fail(
                    "Agent service not implemented yet - this is expected in TDD"
                )


# These tests should initially FAIL since agent service doesn't exist yet
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
