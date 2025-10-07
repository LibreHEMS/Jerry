"""
RAG search tool for LangChain agent integration.

This module provides a LangChain tool that enables the Jerry AI assistant
to search and retrieve relevant information from its knowledge base.
"""

import logging
from typing import Any

from langchain.tools import BaseTool
from pydantic import BaseModel
from pydantic import Field

from ...data.models import KnowledgeChunk
from ...rag.embeddings import get_embeddings_service
from ...rag.retriever import RAGRetriever
from ...rag.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class RAGSearchInput(BaseModel):
    """Input schema for RAG search tool."""

    query: str = Field(description="The search query to find relevant information")
    top_k: int | None = Field(
        default=3, description="Number of results to return (1-10)"
    )
    include_metadata: bool | None = Field(
        default=False, description="Whether to include source metadata"
    )


class RAGSearchTool(BaseTool):
    """LangChain tool for searching the knowledge base."""

    name: str = "rag_search"
    description: str = """
    Search Jerry's knowledge base for relevant information about renewable energy, solar panels,
    home automation, energy management, and Australian energy topics. Use this tool when you need
    to find specific technical information, regulations, product details, or best practices.

    The tool returns relevant excerpts from Jerry's knowledge base with source information.
    """
    args_schema: type[BaseModel] = RAGSearchInput

    def __init__(
        self,
        rag_retriever: RAGRetriever | None = None,
        max_results: int = 5,
        similarity_threshold: float = 0.7,
        **kwargs,
    ):
        """Initialize the RAG search tool.

        Args:
            rag_retriever: RAG retriever instance (created if not provided)
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            **kwargs: Additional arguments for BaseTool
        """
        super().__init__(**kwargs)

        self.max_results = max_results
        self.similarity_threshold = similarity_threshold

        # Initialize RAG retriever if not provided
        if rag_retriever is None:
            rag_retriever = self._create_default_retriever()

        self.rag_retriever = rag_retriever

        logger.info(f"Initialized RAG search tool with max_results={max_results}")

    def _create_default_retriever(self) -> RAGRetriever:
        """Create a default RAG retriever instance.

        Returns:
            Configured RAGRetriever instance
        """
        try:
            # Initialize vector store with default settings
            vector_store = ChromaVectorStore(
                persist_directory="./data/chroma",
                collection_name="jerry_knowledge_base",
            )

            # Get embeddings service
            embeddings_service = get_embeddings_service()

            # Create retriever
            return RAGRetriever(
                vector_store=vector_store,
                embeddings_service=embeddings_service,
                default_top_k=self.max_results,
                similarity_threshold=self.similarity_threshold,
            )

        except Exception as e:
            logger.error(f"Failed to create default RAG retriever: {e}")
            raise

    def _run(
        self,
        query: str,
        top_k: int | None = None,
        include_metadata: bool | None = None,
        run_manager=None,
    ) -> str:
        """Execute the RAG search.

        Args:
            query: Search query
            top_k: Number of results to return
            include_metadata: Whether to include metadata
            run_manager: LangChain run manager

        Returns:
            Formatted search results as string
        """
        if not query.strip():
            return "Error: Search query cannot be empty."

        # Set defaults
        if top_k is None:
            top_k = 3
        if include_metadata is None:
            include_metadata = False

        # Limit top_k to reasonable range
        top_k = max(1, min(top_k, self.max_results))

        try:
            logger.debug(f"Searching knowledge base for: {query[:100]}...")

            # Perform search
            chunks = self.rag_retriever.search(
                query=query, top_k=top_k, similarity_threshold=self.similarity_threshold
            )

            if not chunks:
                return (
                    f"No relevant information found for '{query}'. "
                    "I might not have specific details about this topic in my knowledge base. "
                    "I'll do my best to help with general knowledge."
                )

            # Format results
            results = self._format_search_results(chunks, include_metadata)

            logger.info(f"RAG search returned {len(chunks)} results for query")
            return results

        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return f"Error searching knowledge base: {str(e)}"

    async def _arun(
        self,
        query: str,
        top_k: int | None = None,
        include_metadata: bool | None = None,
        run_manager=None,
    ) -> str:
        """Async version of the search (calls sync version)."""
        return self._run(query, top_k, include_metadata, run_manager)

    def _format_search_results(
        self, chunks: list[KnowledgeChunk], include_metadata: bool = False
    ) -> str:
        """Format search results into a readable string.

        Args:
            chunks: List of retrieved knowledge chunks
            include_metadata: Whether to include metadata

        Returns:
            Formatted results string
        """
        if not chunks:
            return "No results found."

        result_parts = []
        result_parts.append(f"Found {len(chunks)} relevant sources:\n")

        for i, chunk in enumerate(chunks, 1):
            # Add source header
            relevance_pct = int(chunk.relevance_score * 100)
            result_parts.append(
                f"--- Source {i}: {chunk.title} (Relevance: {relevance_pct}%) ---"
            )

            # Add content
            result_parts.append(chunk.content.strip())

            # Add metadata if requested
            if include_metadata and chunk.metadata:
                metadata_items = []
                for key, value in chunk.metadata.items():
                    if key not in [
                        "chunk_number",
                        "total_chunks",
                    ]:  # Skip technical metadata
                        metadata_items.append(f"{key}: {value}")

                if metadata_items:
                    result_parts.append(f"[Metadata: {', '.join(metadata_items)}]")

            # Add spacing between sources
            if i < len(chunks):
                result_parts.append("")

        return "\n".join(result_parts)

    def get_tool_info(self) -> dict[str, Any]:
        """Get information about the tool configuration.

        Returns:
            Dictionary with tool information
        """
        return {
            "name": self.name,
            "description": self.description,
            "max_results": self.max_results,
            "similarity_threshold": self.similarity_threshold,
            "retriever_configured": self.rag_retriever is not None,
        }


class KnowledgeBaseTool(RAGSearchTool):
    """Alias for RAGSearchTool with knowledge base specific naming."""

    name: str = "search_knowledge_base"
    description: str = """
    Search Jerry's comprehensive knowledge base about Australian renewable energy, solar power systems,
    battery storage, energy management, home automation, and related topics. This tool provides access to
    detailed technical information, regulatory guidelines, product specifications, and best practices.

    Use this when you need specific information about:
    - Solar panel systems and installations
    - Battery storage solutions
    - Energy management and optimization
    - Home automation systems
    - Australian energy regulations and incentives
    - Product comparisons and recommendations
    - Technical troubleshooting and maintenance
    """


def create_rag_search_tool(
    rag_retriever: RAGRetriever | None = None,
    max_results: int = 5,
    similarity_threshold: float = 0.7,
    tool_name: str = "rag_search",
) -> RAGSearchTool:
    """Factory function to create a RAG search tool.

    Args:
        rag_retriever: Optional RAG retriever instance
        max_results: Maximum number of results to return
        similarity_threshold: Minimum similarity score
        tool_name: Name of the tool ("rag_search" or "search_knowledge_base")

    Returns:
        Configured RAG search tool
    """
    if tool_name == "search_knowledge_base":
        return KnowledgeBaseTool(
            rag_retriever=rag_retriever,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
        )
    return RAGSearchTool(
        rag_retriever=rag_retriever,
        max_results=max_results,
        similarity_threshold=similarity_threshold,
    )


# Tool instances for easy import
def get_rag_search_tool(**kwargs) -> RAGSearchTool:
    """Get a configured RAG search tool instance.

    Returns:
        RAG search tool ready for use with LangChain agents
    """
    return create_rag_search_tool(**kwargs)


def get_knowledge_base_tool(**kwargs) -> KnowledgeBaseTool:
    """Get a configured knowledge base search tool instance.

    Returns:
        Knowledge base search tool ready for use with LangChain agents
    """
    return create_rag_search_tool(tool_name="search_knowledge_base", **kwargs)
