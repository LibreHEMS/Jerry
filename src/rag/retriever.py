"""
RAG retriever implementation for knowledge base search.

This module provides the main RAG retrieval functionality, combining
vector search with optional reranking for the Jerry AI assistant.
"""

import logging

from ..data.models import KnowledgeChunk
from .embeddings import EmbeddingsService
from .embeddings import get_embeddings_service
from .vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class RAGRetriever:
    """RAG retriever for knowledge base search and context retrieval."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embeddings_service: EmbeddingsService | None = None,
        default_top_k: int = 5,
        similarity_threshold: float = 0.7,
    ):
        """Initialize the RAG retriever.

        Args:
            vector_store: Vector store for similarity search
            embeddings_service: Service for generating query embeddings
            default_top_k: Default number of chunks to retrieve
            similarity_threshold: Minimum similarity score for results
        """
        self.vector_store = vector_store
        self.embeddings_service = embeddings_service or get_embeddings_service()
        self.default_top_k = default_top_k
        self.similarity_threshold = similarity_threshold

        logger.info(
            f"Initialized RAG retriever with top_k={default_top_k}, threshold={similarity_threshold}"
        )

    def search(
        self,
        query: str,
        top_k: int | None = None,
        metadata_filter: dict | None = None,
        similarity_threshold: float | None = None,
    ) -> list[KnowledgeChunk]:
        """Search for relevant knowledge chunks.

        Args:
            query: Search query text
            top_k: Number of chunks to retrieve (default: self.default_top_k)
            metadata_filter: Optional metadata filter for search
            similarity_threshold: Minimum similarity score (default: self.similarity_threshold)

        Returns:
            List of relevant knowledge chunks, sorted by relevance
        """
        if not query.strip():
            logger.warning("Empty query provided to RAG retriever")
            return []

        # Use default values if not provided
        if top_k is None:
            top_k = self.default_top_k
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold

        try:
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {query[:100]}...")
            query_embedding = self.embeddings_service.encode_query(query)

            # Search vector store
            logger.debug(f"Searching vector store with top_k={top_k}")
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                n_results=top_k * 2,  # Get more results for filtering
                metadata_filter=metadata_filter,
            )

            # Filter by similarity threshold and update relevance scores
            filtered_chunks = []
            for chunk, similarity_score in results:
                if similarity_score >= similarity_threshold:
                    chunk.relevance_score = similarity_score
                    filtered_chunks.append(chunk)

            # Sort by relevance score (descending) and limit to top_k
            filtered_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
            final_chunks = filtered_chunks[:top_k]

            logger.info(f"Retrieved {len(final_chunks)} relevant chunks for query")
            return final_chunks

        except Exception as e:
            logger.error(f"Error during RAG search: {e}")
            return []

    def search_by_document(
        self, query: str, document_id: str, top_k: int | None = None
    ) -> list[KnowledgeChunk]:
        """Search for relevant chunks within a specific document.

        Args:
            query: Search query text
            document_id: ID of the document to search within
            top_k: Number of chunks to retrieve

        Returns:
            List of relevant knowledge chunks from the specified document
        """
        metadata_filter = {"document_id": document_id}
        return self.search(query=query, top_k=top_k, metadata_filter=metadata_filter)

    def get_context_for_query(
        self, query: str, max_context_length: int = 4000, top_k: int | None = None
    ) -> tuple[str, list[KnowledgeChunk]]:
        """Get formatted context string for a query.

        Args:
            query: Search query text
            max_context_length: Maximum length of context string
            top_k: Number of chunks to retrieve

        Returns:
            Tuple of (formatted_context, source_chunks)
        """
        chunks = self.search(query, top_k=top_k)

        if not chunks:
            return "", []

        # Build context string
        context_parts = []
        current_length = 0
        used_chunks = []

        for chunk in chunks:
            # Format chunk context
            chunk_text = f"[Source: {chunk.title}]\n{chunk.content}\n"

            # Check if adding this chunk would exceed max length
            if current_length + len(chunk_text) > max_context_length:
                # Try to include a truncated version
                remaining_space = (
                    max_context_length - current_length - 50
                )  # Leave space for truncation note
                if remaining_space > 100:  # Only include if meaningful space left
                    truncated_content = chunk.content[:remaining_space]
                    chunk_text = f"[Source: {chunk.title}]\n{truncated_content}...\n"
                    context_parts.append(chunk_text)
                    used_chunks.append(chunk)
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)
            used_chunks.append(chunk)

        context_string = "\n".join(context_parts)

        logger.info(
            f"Generated context with {len(used_chunks)} chunks, length: {len(context_string)}"
        )
        return context_string, used_chunks

    def get_similar_chunks(
        self,
        reference_chunk: KnowledgeChunk,
        top_k: int = 3,
        exclude_same_document: bool = False,
    ) -> list[KnowledgeChunk]:
        """Find chunks similar to a reference chunk.

        Args:
            reference_chunk: Chunk to find similar content for
            top_k: Number of similar chunks to return
            exclude_same_document: Whether to exclude chunks from same document

        Returns:
            List of similar knowledge chunks
        """
        if not reference_chunk.embedding:
            logger.warning("Reference chunk has no embedding")
            return []

        # Set up metadata filter
        metadata_filter = None
        if exclude_same_document:
            # This would require a "not equals" filter which Chroma doesn't support directly
            # For now, we'll filter after retrieval
            pass

        try:
            # Search using reference chunk's embedding
            results = self.vector_store.search_similar(
                query_embedding=reference_chunk.embedding,
                n_results=top_k * 2 if exclude_same_document else top_k,
                metadata_filter=metadata_filter,
            )

            similar_chunks = []
            for chunk, similarity_score in results:
                # Skip the reference chunk itself
                if chunk.id == reference_chunk.id:
                    continue

                # Skip chunks from same document if requested
                if (
                    exclude_same_document
                    and chunk.document_id == reference_chunk.document_id
                ):
                    continue

                chunk.relevance_score = similarity_score
                similar_chunks.append(chunk)

                if len(similar_chunks) >= top_k:
                    break

            logger.info(f"Found {len(similar_chunks)} similar chunks")
            return similar_chunks

        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            return []

    def update_retrieval_stats(
        self, query: str, retrieved_chunks: list[KnowledgeChunk]
    ) -> None:
        """Update retrieval statistics (for monitoring/optimization).

        Args:
            query: The search query
            retrieved_chunks: The chunks that were retrieved
        """
        # This could be extended to log retrieval metrics
        logger.debug(
            f"Query '{query[:50]}...' retrieved {len(retrieved_chunks)} chunks"
        )

        if retrieved_chunks:
            avg_relevance = sum(
                chunk.relevance_score for chunk in retrieved_chunks
            ) / len(retrieved_chunks)
            logger.debug(f"Average relevance score: {avg_relevance:.3f}")


class HybridRetriever(RAGRetriever):
    """Hybrid retriever combining semantic and keyword search."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embeddings_service: EmbeddingsService | None = None,
        default_top_k: int = 5,
        similarity_threshold: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """Initialize the hybrid retriever.

        Args:
            vector_store: Vector store for similarity search
            embeddings_service: Service for generating query embeddings
            default_top_k: Default number of chunks to retrieve
            similarity_threshold: Minimum similarity score for results
            keyword_weight: Weight for keyword search (0.0 to 1.0)
        """
        super().__init__(
            vector_store, embeddings_service, default_top_k, similarity_threshold
        )
        self.keyword_weight = keyword_weight
        self.semantic_weight = 1.0 - keyword_weight

        logger.info(
            f"Initialized hybrid retriever with keyword_weight={keyword_weight}"
        )

    def _keyword_search(
        self, query: str, chunks: list[KnowledgeChunk]
    ) -> dict[str, float]:
        """Perform simple keyword search scoring.

        Args:
            query: Search query
            chunks: Chunks to score

        Returns:
            Dictionary mapping chunk IDs to keyword scores
        """
        query_terms = set(query.lower().split())
        scores = {}

        for chunk in chunks:
            content_terms = set(chunk.content.lower().split())

            # Simple term overlap scoring
            overlap = len(query_terms.intersection(content_terms))
            max_terms = max(len(query_terms), len(content_terms))

            keyword_score = overlap / max_terms if max_terms > 0 else 0.0

            scores[str(chunk.id)] = keyword_score

        return scores

    def search(
        self,
        query: str,
        top_k: int | None = None,
        metadata_filter: dict | None = None,
        similarity_threshold: float | None = None,
    ) -> list[KnowledgeChunk]:
        """Hybrid search combining semantic and keyword search.

        Args:
            query: Search query text
            top_k: Number of chunks to retrieve
            metadata_filter: Optional metadata filter for search
            similarity_threshold: Minimum similarity score

        Returns:
            List of relevant knowledge chunks with hybrid scoring
        """
        # Get semantic search results
        semantic_chunks = super().search(
            query=query,
            top_k=top_k * 2
            if top_k
            else self.default_top_k * 2,  # Get more for reranking
            metadata_filter=metadata_filter,
            similarity_threshold=0.5,  # Lower threshold for hybrid
        )

        if not semantic_chunks:
            return []

        # Perform keyword scoring
        keyword_scores = self._keyword_search(query, semantic_chunks)

        # Combine scores
        for chunk in semantic_chunks:
            semantic_score = chunk.relevance_score
            keyword_score = keyword_scores.get(str(chunk.id), 0.0)

            # Weighted combination
            hybrid_score = (
                self.semantic_weight * semantic_score
                + self.keyword_weight * keyword_score
            )

            chunk.relevance_score = hybrid_score

        # Apply final threshold and sorting
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold

        filtered_chunks = [
            chunk
            for chunk in semantic_chunks
            if chunk.relevance_score >= similarity_threshold
        ]

        filtered_chunks.sort(key=lambda x: x.relevance_score, reverse=True)

        final_top_k = top_k or self.default_top_k
        return filtered_chunks[:final_top_k]
