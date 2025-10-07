"""
FastAPI server for RAG (Retrieval-Augmented Generation) service.

This module provides the HTTP API endpoints for knowledge base search
and retrieval functionality for the Jerry AI assistant.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from pydantic import BaseModel
from pydantic import Field

from ..rag.embeddings import get_embeddings_service
from ..rag.retriever import RAGRetriever
from ..rag.vector_store import ChromaVectorStore
from ..utils.config import get_config
from ..utils.logging import setup_logging
from ..utils.performance import PerformanceOptimizer
from ..utils.performance import ResponseCache

logger = logging.getLogger(__name__)

# Global instances
vector_store: ChromaVectorStore | None = None
rag_retriever: RAGRetriever | None = None
optimizer: PerformanceOptimizer | None = None
response_cache: ResponseCache | None = None
metrics: Any | None = None


# Pydantic models for request/response
class SearchRequest(BaseModel):
    """Request model for knowledge base search."""

    query: str = Field(..., description="Search query text")
    top_k: int | None = Field(5, description="Number of results to return", ge=1, le=20)
    metadata_filter: dict | None = Field(None, description="Optional metadata filter")
    similarity_threshold: float | None = Field(
        None, description="Minimum similarity score", ge=0.0, le=1.0
    )


class KnowledgeChunkResponse(BaseModel):
    """Response model for a knowledge chunk."""

    id: str
    document_id: str
    title: str
    content: str
    metadata: dict
    chunk_index: int
    relevance_score: float


class SearchResponse(BaseModel):
    """Response model for search results."""

    query: str
    results: list[KnowledgeChunkResponse]
    total_results: int
    processing_time_ms: float


class ContextRequest(BaseModel):
    """Request model for getting formatted context."""

    query: str = Field(..., description="Search query text")
    max_context_length: int | None = Field(
        4000, description="Maximum context length", ge=100, le=10000
    )
    top_k: int | None = Field(
        5, description="Number of chunks to consider", ge=1, le=20
    )


class ContextResponse(BaseModel):
    """Response model for formatted context."""

    query: str
    context: str
    source_chunks: list[KnowledgeChunkResponse]
    context_length: int


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    vector_store_stats: dict
    embeddings_model: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting RAG service...")

    global vector_store, rag_retriever

    try:
        # Load configuration
        config = get_config()

        # Initialize vector store
        vector_store_config = config.get("vector_store", {})
        persist_directory = vector_store_config.get(
            "persist_directory", "./data/chroma"
        )
        collection_name = vector_store_config.get(
            "collection_name", "jerry_knowledge_base"
        )

        vector_store = ChromaVectorStore(
            persist_directory=persist_directory, collection_name=collection_name
        )

        # Initialize embeddings service
        embeddings_config = config.get("embeddings", {})
        model_name = embeddings_config.get("model_name", "all-MiniLM-L6-v2")
        device = embeddings_config.get("device")
        use_mock = embeddings_config.get("use_mock", False)

        embeddings_service = get_embeddings_service(
            model_name=model_name, device=device, use_mock=use_mock
        )

        # Initialize RAG retriever
        retriever_config = config.get("rag_retriever", {})
        default_top_k = retriever_config.get("default_top_k", 5)
        similarity_threshold = retriever_config.get("similarity_threshold", 0.7)

        rag_retriever = RAGRetriever(
            vector_store=vector_store,
            embeddings_service=embeddings_service,
            default_top_k=default_top_k,
            similarity_threshold=similarity_threshold,
        )

        logger.info("RAG service started successfully")

    except Exception as e:
        logger.error(f"Failed to start RAG service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAG service...")


# Create FastAPI app
app = FastAPI(
    title="Jerry RAG Service",
    description="Knowledge base search and retrieval API for Jerry AI assistant",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if not vector_store or not rag_retriever:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Get vector store stats
        stats = vector_store.get_collection_stats()

        # Get embeddings model info
        model_info = rag_retriever.embeddings_service.get_model_info()

        return HealthResponse(
            status="healthy", vector_store_stats=stats, embeddings_model=model_info
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/v1/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """Search the knowledge base for relevant chunks."""
    if not rag_retriever:
        raise HTTPException(status_code=503, detail="RAG service not initialized")

    import time

    start_time = time.time()

    try:
        # Perform search
        chunks = rag_retriever.search(
            query=request.query,
            top_k=request.top_k,
            metadata_filter=request.metadata_filter,
            similarity_threshold=request.similarity_threshold,
        )

        # Convert to response format
        results = []
        for chunk in chunks:
            result = KnowledgeChunkResponse(
                id=str(chunk.id),
                document_id=chunk.document_id,
                title=chunk.title,
                content=chunk.content,
                metadata=chunk.metadata,
                chunk_index=chunk.chunk_index,
                relevance_score=chunk.relevance_score,
            )
            results.append(result)

        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Update retrieval stats
        rag_retriever.update_retrieval_stats(request.query, chunks)

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/v1/context", response_model=ContextResponse)
async def get_context_for_query(request: ContextRequest):
    """Get formatted context string for a query."""
    if not rag_retriever:
        raise HTTPException(status_code=503, detail="RAG service not initialized")

    try:
        # Get context
        context_string, source_chunks = rag_retriever.get_context_for_query(
            query=request.query,
            max_context_length=request.max_context_length,
            top_k=request.top_k,
        )

        # Convert chunks to response format
        chunk_responses = []
        for chunk in source_chunks:
            chunk_response = KnowledgeChunkResponse(
                id=str(chunk.id),
                document_id=chunk.document_id,
                title=chunk.title,
                content=chunk.content,
                metadata=chunk.metadata,
                chunk_index=chunk.chunk_index,
                relevance_score=chunk.relevance_score,
            )
            chunk_responses.append(chunk_response)

        return ContextResponse(
            query=request.query,
            context=context_string,
            source_chunks=chunk_responses,
            context_length=len(context_string),
        )

    except Exception as e:
        logger.error(f"Context generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Context generation failed: {str(e)}"
        )


@app.get("/v1/search")
async def search_knowledge_base_get(
    query: str = Query(..., description="Search query text"),
    top_k: int = Query(5, description="Number of results to return", ge=1, le=20),
    similarity_threshold: float | None = Query(
        None, description="Minimum similarity score", ge=0.0, le=1.0
    ),
):
    """Search the knowledge base using GET method (for simple queries)."""
    request = SearchRequest(
        query=query, top_k=top_k, similarity_threshold=similarity_threshold
    )
    return await search_knowledge_base(request)


@app.get("/v1/stats")
async def get_statistics():
    """Get RAG service statistics."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        stats = vector_store.get_collection_stats()
        return {"service": "rag", "status": "active", **stats}

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return {"error": "Endpoint not found", "detail": str(exc)}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}


if __name__ == "__main__":
    import uvicorn

    # Setup logging
    setup_logging()

    # Load configuration
    config = get_config()
    server_config = config.get("rag_server", {})

    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8002)
    workers = server_config.get("workers", 1)

    logger.info(f"Starting RAG server on {host}:{port}")

    uvicorn.run(
        "src.services.rag_server:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
    )
