"""Contract tests for Jerry RAG Service API."""

import httpx
import pytest


class TestRAGServiceContract:
    """Test contract compliance for RAG service API."""

    BASE_URL = "http://localhost:8004"

    @pytest.mark.asyncio
    async def test_post_search_endpoint_exists(self):
        """Test that POST /v1/search endpoint exists and accepts requests."""
        async with httpx.AsyncClient() as client:
            request_data = {
                "query": "solar panel installation benefits",
                "top_k": 5,
                "threshold": 0.7,
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/search", json=request_data, timeout=30.0
            )

            # Should not get 404 (endpoint exists)
            assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_post_search_response_schema(self):
        """Test that POST /v1/search returns expected response schema."""
        async with httpx.AsyncClient() as client:
            request_data = {"query": "battery storage systems", "top_k": 3}

            response = await client.post(
                f"{self.BASE_URL}/v1/search", json=request_data, timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()

                # Required fields according to contract
                assert "results" in data
                assert "query_embedding_time_ms" in data
                assert "search_time_ms" in data
                assert "total_results" in data

                # Type validation
                assert isinstance(data["results"], list)
                assert isinstance(data["query_embedding_time_ms"], int)
                assert isinstance(data["search_time_ms"], int)
                assert isinstance(data["total_results"], int)

                # Result structure validation if results exist
                for result in data["results"]:
                    assert "content" in result
                    assert "metadata" in result
                    assert "relevance_score" in result
                    assert isinstance(result["content"], str)
                    assert isinstance(result["metadata"], dict)
                    assert isinstance(result["relevance_score"], (int, float))

    @pytest.mark.asyncio
    async def test_post_search_bad_request_handling(self):
        """Test that POST /v1/search handles bad requests properly."""
        async with httpx.AsyncClient() as client:
            # Missing required fields
            invalid_request = {"top_k": 5}

            response = await client.post(
                f"{self.BASE_URL}/v1/search", json=invalid_request, timeout=30.0
            )

            # Should return 400 for bad request or 422 for validation error
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_post_ingest_endpoint_exists(self):
        """Test that POST /v1/ingest endpoint exists."""
        async with httpx.AsyncClient() as client:
            request_data = {
                "document_id": "test_doc_123",
                "title": "Test Document",
                "content": "This is test content for ingestion",
                "metadata": {"source": "test"},
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/ingest", json=request_data, timeout=30.0
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
