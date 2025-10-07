"""Contract tests for Jerry Agent Service API."""

import httpx
import pytest


class TestAgentServiceContract:
    """Test contract compliance for agent service API."""

    BASE_URL = "http://localhost:8003"

    @pytest.mark.asyncio
    async def test_post_chat_endpoint_exists(self):
        """Test that POST /v1/chat endpoint exists and accepts requests."""
        async with httpx.AsyncClient() as client:
            request_data = {
                "user_id": "test_user_123",
                "message": "Hello Jerry, tell me about solar panels",
                "channel_id": "test_channel_123",
                "use_rag": True,
                "use_cache": True,
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat", json=request_data, timeout=30.0
            )

            # Should not get 404 (endpoint exists)
            assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_post_chat_response_schema(self):
        """Test that POST /v1/chat returns expected response schema."""
        async with httpx.AsyncClient() as client:
            request_data = {
                "user_id": "test_user_123",
                "message": "What are the benefits of solar energy?",
                "channel_id": "test_channel_123",
                "use_rag": True,
                "use_cache": False,
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat", json=request_data, timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()

                # Required fields according to contract
                assert "message" in data
                assert "conversation_id" in data
                assert "response_time_ms" in data
                assert "tokens_used" in data
                assert "sources_used" in data
                assert "tools_used" in data
                assert "cached" in data

                # Type validation
                assert isinstance(data["message"], str)
                assert isinstance(data["response_time_ms"], int)
                assert isinstance(data["tokens_used"], int)
                assert isinstance(data["sources_used"], list)
                assert isinstance(data["tools_used"], list)
                assert isinstance(data["cached"], bool)

    @pytest.mark.asyncio
    async def test_post_chat_bad_request_handling(self):
        """Test that POST /v1/chat handles bad requests properly."""
        async with httpx.AsyncClient() as client:
            # Missing required fields
            invalid_request = {"message": "Hello"}

            response = await client.post(
                f"{self.BASE_URL}/v1/chat", json=invalid_request, timeout=30.0
            )

            # Should return 400 for bad request or 422 for validation error
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_conversation_summary_endpoint_exists(self):
        """Test that POST /v1/conversations/{id}/summary endpoint exists."""
        async with httpx.AsyncClient() as client:
            conversation_id = "550e8400-e29b-41d4-a716-446655440000"

            response = await client.post(
                f"{self.BASE_URL}/v1/conversations/{conversation_id}/summary",
                timeout=30.0,
            )

            # Should not get 404 (endpoint exists)
            assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_health_endpoint_exists(self):
        """Test that health check endpoint exists."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/health", timeout=10.0)

            # Should not get 404 (endpoint exists)
            assert response.status_code != 404


# This test should initially FAIL since service doesn't exist yet
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
