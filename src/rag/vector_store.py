"""
Vector store implementation using Chroma DB for RAG pipeline.

This module provides a wrapper around Chroma DB for storing and retrieving
document embeddings for the Jerry AI assistant's knowledge base.
"""

import logging
from uuid import UUID

import chromadb
from chromadb import Collection
from chromadb.config import Settings

from ..data.models import KnowledgeChunk

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Vector store implementation using Chroma DB."""

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "jerry_knowledge_base",
    ):
        """Initialize the Chroma vector store.

        Args:
            persist_directory: Directory to persist the Chroma database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self.collection: Collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Jerry AI knowledge base embeddings"},
        )

        logger.info(f"Initialized Chroma vector store at {persist_directory}")

    def add_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        """Add knowledge chunks to the vector store.

        Args:
            chunks: List of knowledge chunks with embeddings
        """
        if not chunks:
            return

        # Prepare data for Chroma
        ids = [str(chunk.id) for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = []

        for chunk in chunks:
            metadata = {
                "document_id": chunk.document_id,
                "title": chunk.title,
                "chunk_index": chunk.chunk_index,
                "created_at": chunk.created_at.isoformat(),
                **chunk.metadata,
            }
            metadatas.append(metadata)

        # Add to collection
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

        logger.info(f"Added {len(chunks)} chunks to vector store")

    def update_chunk(self, chunk: KnowledgeChunk) -> None:
        """Update an existing chunk in the vector store.

        Args:
            chunk: Updated knowledge chunk
        """
        chunk_id = str(chunk.id)

        # Check if chunk exists
        try:
            existing = self.collection.get(ids=[chunk_id])
            if not existing["ids"]:
                # Chunk doesn't exist, add it
                self.add_chunks([chunk])
                return
        except Exception as e:
            logger.warning(f"Error checking existing chunk {chunk_id}: {e}")
            return

        # Update existing chunk
        metadata = {
            "document_id": chunk.document_id,
            "title": chunk.title,
            "chunk_index": chunk.chunk_index,
            "created_at": chunk.created_at.isoformat(),
            "updated_at": chunk.updated_at.isoformat(),
            **chunk.metadata,
        }

        self.collection.update(
            ids=[chunk_id],
            embeddings=[chunk.embedding],
            documents=[chunk.content],
            metadatas=[metadata],
        )

        logger.info(f"Updated chunk {chunk_id} in vector store")

    def delete_chunk(self, chunk_id: UUID) -> None:
        """Delete a chunk from the vector store.

        Args:
            chunk_id: ID of the chunk to delete
        """
        self.collection.delete(ids=[str(chunk_id)])
        logger.info(f"Deleted chunk {chunk_id} from vector store")

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks for a specific document.

        Args:
            document_id: ID of the document to delete
        """
        # Query for all chunks with this document_id
        results = self.collection.get(where={"document_id": document_id})

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(
                f"Deleted {len(results['ids'])} chunks for document {document_id}"
            )

    def search_similar(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        """Search for similar chunks using embedding similarity.

        Args:
            query_embedding: Query vector embedding
            n_results: Number of results to return
            metadata_filter: Optional metadata filter

        Returns:
            List of tuples containing (KnowledgeChunk, similarity_score)
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=metadata_filter,
            )

            if not results["ids"] or not results["ids"][0]:
                return []

            chunks_with_scores = []

            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                document = results["documents"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0.0

                # Convert distance to similarity score (1 - distance)
                similarity_score = 1.0 - distance

                # Reconstruct KnowledgeChunk
                chunk = KnowledgeChunk(
                    id=UUID(chunk_id),
                    document_id=metadata["document_id"],
                    title=metadata["title"],
                    content=document,
                    embedding=query_embedding,  # Not the actual embedding, but sufficient for result
                    metadata={
                        k: v
                        for k, v in metadata.items()
                        if k
                        not in [
                            "document_id",
                            "title",
                            "chunk_index",
                            "created_at",
                            "updated_at",
                        ]
                    },
                    created_at=metadata.get("created_at", ""),
                    updated_at=metadata.get("updated_at", ""),
                    chunk_index=metadata.get("chunk_index", 0),
                    relevance_score=similarity_score,
                )

                chunks_with_scores.append((chunk, similarity_score))

            logger.info(f"Found {len(chunks_with_scores)} similar chunks")
            return chunks_with_scores

        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def get_chunk(self, chunk_id: UUID) -> KnowledgeChunk | None:
        """Retrieve a specific chunk by ID.

        Args:
            chunk_id: ID of the chunk to retrieve

        Returns:
            KnowledgeChunk if found, None otherwise
        """
        try:
            results = self.collection.get(ids=[str(chunk_id)])

            if not results["ids"]:
                return None

            metadata = results["metadatas"][0]
            document = results["documents"][0]

            return KnowledgeChunk(
                id=chunk_id,
                document_id=metadata["document_id"],
                title=metadata["title"],
                content=document,
                embedding=[],  # Embedding not returned by get()
                metadata={
                    k: v
                    for k, v in metadata.items()
                    if k
                    not in [
                        "document_id",
                        "title",
                        "chunk_index",
                        "created_at",
                        "updated_at",
                    ]
                },
                created_at=metadata.get("created_at", ""),
                updated_at=metadata.get("updated_at", ""),
                chunk_index=metadata.get("chunk_index", 0),
            )

        except Exception as e:
            logger.error(f"Error retrieving chunk {chunk_id}: {e}")
            return None

    def get_collection_stats(self) -> dict[str, int]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_chunks": 0, "collection_name": self.collection_name}

    def reset_collection(self) -> None:
        """Reset the collection (delete all data).

        Warning: This will delete all stored embeddings!
        """
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Jerry AI knowledge base embeddings"},
        )
        logger.warning(f"Reset collection {self.collection_name}")
