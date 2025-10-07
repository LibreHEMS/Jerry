"""Contract tests for Jerry Model Service API."""

import httpx
import pytest


class TestModelServiceContract:
    """Test contract compliance for model service API."""

    BASE_URL = "http://localhost:8002"

    @pytest.mark.asyncio
    async def test_post_inference_endpoint_exists(self):
        """Test that POST /v1/inference endpoint exists and accepts requests."""
        async with httpx.AsyncClient() as client:
            request_data = {
                "prompt": "What are the benefits of solar energy?",
                "max_tokens": 100,
                "temperature": 0.7,
                "stop_sequences": ["</response>"],
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/inference", json=request_data, timeout=60.0
            )

            # Should not get 404 (endpoint exists)
            assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_post_inference_response_schema(self):
        """Test that POST /v1/inference returns expected response schema."""
        async with httpx.AsyncClient() as client:
            request_data = {
                "prompt": "Hello, how are you?",
                "max_tokens": 50,
                "temperature": 0.5,
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/inference", json=request_data, timeout=60.0
            )

            if response.status_code == 200:
                data = response.json()

                # Required fields according to contract
                assert "text" in data
                assert "tokens_used" in data
                assert "response_time_ms" in data
                assert "model_used" in data

                # Type validation
                assert isinstance(data["text"], str)
                assert isinstance(data["tokens_used"], int)
                assert isinstance(data["response_time_ms"], int)
                assert isinstance(data["model_used"], str)

    @pytest.mark.asyncio
    async def test_post_inference_bad_request_handling(self):
        """Test that POST /v1/inference handles bad requests properly."""
        async with httpx.AsyncClient() as client:
            # Missing required fields
            invalid_request = {"max_tokens": 100}

            response = await client.post(
                f"{self.BASE_URL}/v1/inference", json=invalid_request, timeout=30.0
            )

            # Should return 400 for bad request or 422 for validation error
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_models_endpoint_exists(self):
        """Test that GET /v1/models endpoint exists."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/v1/models", timeout=10.0)

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
