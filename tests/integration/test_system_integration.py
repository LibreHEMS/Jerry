"""
Integration tests to verify all Jerry AI services work together.

This module provides end-to-end integration tests for the complete
Jerry AI system, testing all components working together.
"""

import asyncio
from typing import Any

import pytest

from src.data.models import Conversation
from src.data.models import User
from src.rag.retriever import RAGRetriever
from src.rag.vector_store import ChromaVectorStore
from src.services.agent_service import JerryAgent
from src.utils.cache import get_memory_cache
from src.utils.cache import get_semantic_cache
from src.utils.config import get_config
from src.utils.metrics import get_metrics_collector
from src.utils.performance import PerformanceOptimizer


class TestSystemIntegration:
    """Integration tests for the complete Jerry AI system."""

    @pytest.fixture
    async def setup_system(self):
        """Setup the complete system for testing."""
        config = get_config()

        # Initialize performance optimizations
        optimizer = PerformanceOptimizer("integration_test")

        # Initialize caching
        semantic_cache = get_semantic_cache()
        memory_cache = get_memory_cache()

        # Initialize metrics
        metrics = get_metrics_collector("integration_test")

        # Setup vector store
        vector_store = ChromaVectorStore()

        # Setup RAG retriever
        rag_retriever = RAGRetriever(vector_store)

        # Mock model service for testing
        class MockModelService:
            async def generate_response(self, request):
                return {
                    "response": f"Mock response to: {request.messages[-1].content}",
                    "model": "mock-jerry-7b",
                    "usage": {"total_tokens": 50},
                }

        model_service = MockModelService()

        # Setup agent
        agent = JerryAgent(config=config.agent, model_service=model_service)

        return {
            "agent": agent,
            "model_service": model_service,
            "rag_retriever": rag_retriever,
            "vector_store": vector_store,
            "optimizer": optimizer,
            "metrics": metrics,
            "semantic_cache": semantic_cache,
            "memory_cache": memory_cache,
        }

    @pytest.mark.asyncio
    async def test_end_to_end_conversation(self, setup_system):
        """Test complete conversation flow through all services."""
        system = await setup_system

        # Create test user and conversation
        user = User(
            id="test_user_123",
            discord_id="discord_123",
            username="TestUser",
            created_at=None,
        )

        conversation = Conversation(
            id="conv_123",
            user_id=user.id,
            channel_id="channel_123",
            messages=[],
            created_at=None,
            updated_at=None,
        )

        # Test message processing
        message_content = "Hello Jerry, can you help me understand AI?"

        response, metadata = await system["agent"].process_message(
            user=user, conversation=conversation, message_content=message_content
        )

        # Verify response
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Mock response to:" in response

        # Verify metadata
        assert metadata is not None
        assert isinstance(metadata, dict)

    @pytest.mark.asyncio
    async def test_rag_integration(self, setup_system):
        """Test RAG system integration."""
        system = await setup_system

        # Add test knowledge to vector store
        from src.data.models import KnowledgeChunk

        test_chunks = [
            KnowledgeChunk(
                id="chunk_1",
                document_id="doc_1",
                title="AI Basics",
                content="Artificial Intelligence is the simulation of human intelligence in machines.",
                metadata={"category": "ai", "difficulty": "beginner"},
                chunk_index=0,
                embedding=None,
            ),
            KnowledgeChunk(
                id="chunk_2",
                document_id="doc_1",
                title="Machine Learning",
                content="Machine Learning is a subset of AI that enables computers to learn without explicit programming.",
                metadata={"category": "ml", "difficulty": "intermediate"},
                chunk_index=1,
                embedding=None,
            ),
        ]

        # Add chunks to vector store
        for chunk in test_chunks:
            await system["vector_store"].add_chunks([chunk])

        # Test search
        search_results = system["rag_retriever"].search(
            query="What is artificial intelligence?", top_k=2
        )

        # Verify search results
        assert len(search_results) > 0
        assert any(
            "intelligence" in result.content.lower() for result in search_results
        )

    @pytest.mark.asyncio
    async def test_caching_integration(self, setup_system):
        """Test caching system integration."""
        system = await setup_system

        # Test semantic cache
        query = "What is machine learning?"
        response = "Machine learning is a method of data analysis that automates analytical model building."

        # Store in cache
        success = system["semantic_cache"].put(
            query=query,
            response=response,
            context={"test": True},
            model_used="test-model",
        )
        assert success

        # Retrieve from cache
        cached_response = system["semantic_cache"].get(
            query=query, context={"test": True}, model_used="test-model"
        )
        assert cached_response == response

        # Test memory cache
        cache_key = "test_key"
        cache_value = {"data": "test_value", "timestamp": "2024-01-01"}

        system["memory_cache"].put(cache_key, cache_value, 3600)
        retrieved_value = system["memory_cache"].get(cache_key)
        assert retrieved_value == cache_value

    @pytest.mark.asyncio
    async def test_metrics_collection(self, setup_system):
        """Test metrics collection integration."""
        system = await setup_system

        # Record some test metrics
        system["metrics"].increment_counter("test_counter")
        system["metrics"].record_gauge("test_gauge", 42.0)
        system["metrics"].record_histogram("test_histogram", 1.5)

        # Record request metrics
        system["metrics"].record_request(
            endpoint="/test", method="POST", status_code=200, duration=0.123
        )

        # Get metrics
        metrics_data = system["metrics"].get_all_metrics()
        assert metrics_data is not None
        assert isinstance(metrics_data, dict)

    @pytest.mark.asyncio
    async def test_performance_optimization(self, setup_system):
        """Test performance optimization integration."""
        system = await setup_system

        # Test performance decorator
        @system["optimizer"].timed_execution("test_operation")
        async def test_operation():
            await asyncio.sleep(0.1)  # Simulate work
            return "operation_result"

        result = await test_operation()
        assert result == "operation_result"

        # Test caching decorator
        call_count = 0

        @system["optimizer"].cached_response(ttl_seconds=3600)
        async def cached_operation(query):
            nonlocal call_count
            call_count += 1
            return f"result_for_{query}"

        # First call - should execute function
        result1 = await cached_operation("test_query")
        assert result1 == "result_for_test_query"
        assert call_count == 1

        # Second call - should use cache
        result2 = await cached_operation("test_query")
        assert result2 == "result_for_test_query"
        assert call_count == 1  # Should not have incremented

    @pytest.mark.asyncio
    async def test_health_checks(self, setup_system):
        """Test health check system integration."""
        from src.utils.health import HealthChecker

        # Create health checker
        health_checker = HealthChecker("integration_test")

        # Add test checks
        def test_check_success():
            return True, "All systems operational"

        def test_check_failure():
            return False, "System error detected"

        async def async_test_check():
            await asyncio.sleep(0.01)
            return {"status": "healthy", "message": "Async check passed"}

        health_checker.add_check("success_check", test_check_success, critical=True)
        health_checker.add_check("failure_check", test_check_failure, critical=False)
        health_checker.add_check("async_check", async_test_check, critical=True)

        # Get health status
        health_response = await health_checker.get_health(include_metrics=True)

        # Verify health response
        assert health_response.service == "integration_test"
        assert health_response.status is not None
        assert len(health_response.checks) == 3
        assert health_response.uptime_seconds > 0
        assert health_response.metrics is not None

    @pytest.mark.asyncio
    async def test_full_service_startup(self, setup_system):
        """Test complete service startup sequence."""
        system = await setup_system

        # Simulate service startup sequence
        startup_tasks = []

        # 1. Initialize configuration
        config = get_config()
        assert config is not None
        startup_tasks.append("✓ Configuration loaded")

        # 2. Initialize caching
        semantic_cache = get_semantic_cache()
        memory_cache = get_memory_cache()
        assert semantic_cache is not None
        assert memory_cache is not None
        startup_tasks.append("✓ Caching systems initialized")

        # 3. Initialize metrics
        metrics = get_metrics_collector("startup_test")
        assert metrics is not None
        startup_tasks.append("✓ Metrics collection initialized")

        # 4. Initialize vector store
        vector_store = ChromaVectorStore()
        assert vector_store is not None
        startup_tasks.append("✓ Vector store initialized")

        # 5. Initialize services
        agent = system["agent"]
        assert agent is not None
        startup_tasks.append("✓ Agent service initialized")

        # 6. Verify service integration
        user = User(
            id="startup_test", discord_id="123", username="test", created_at=None
        )
        conversation = Conversation(
            id="startup_conv",
            user_id=user.id,
            channel_id="test_channel",
            messages=[],
            created_at=None,
            updated_at=None,
        )

        response, metadata = await agent.process_message(
            user=user, conversation=conversation, message_content="System startup test"
        )

        assert response is not None
        startup_tasks.append("✓ End-to-end message processing verified")

        # Print startup sequence for verification
        print("\nService Startup Sequence:")
        for task in startup_tasks:
            print(f"  {task}")

        assert len(startup_tasks) == 6


# Test utilities for integration testing
class IntegrationTestUtils:
    """Utilities for integration testing."""

    @staticmethod
    async def create_test_user() -> User:
        """Create a test user."""
        return User(
            id="integration_test_user",
            discord_id="integration_discord_123",
            username="IntegrationTestUser",
            created_at=None,
        )

    @staticmethod
    async def create_test_conversation(user_id: str) -> Conversation:
        """Create a test conversation."""
        return Conversation(
            id="integration_test_conv",
            user_id=user_id,
            channel_id="integration_test_channel",
            messages=[],
            created_at=None,
            updated_at=None,
        )

    @staticmethod
    async def simulate_http_request(url: str, data: dict[str, Any]) -> dict[str, Any]:
        """Simulate HTTP request for API testing."""
        # This would normally use aiohttp to make real requests
        # For integration tests, we can mock the responses

        if "/health" in url:
            return {
                "service": "test_service",
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "uptime_seconds": 123.45,
            }
        if "/v1/agent/process" in url:
            return {
                "response": f"Mock response to: {data.get('message', '')}",
                "conversation_id": data.get("conversation_id", "mock_conv"),
                "metadata": {"processing_time": 0.123, "model_used": "mock-jerry-7b"},
            }
        if "/v1/search" in url:
            return {
                "query": data.get("query", ""),
                "results": [
                    {
                        "id": "mock_result_1",
                        "content": "Mock search result content",
                        "relevance_score": 0.95,
                    }
                ],
                "total_results": 1,
            }
        return {"error": "Unknown endpoint"}


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
