"""
Document embeddings service for generating vector representations.

This module provides text embedding functionality using sentence-transformers
for the Jerry AI assistant's RAG pipeline.
"""

import logging

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str | None = None):
        """Initialize the embeddings service.

        Args:
            model_name: Name of the sentence-transformers model to use
            device: Device to run the model on ('cpu', 'cuda', or None for auto)
        """
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.device = device

        logger.info(f"Loading embeddings model: {model_name}")

        try:
            self.model = SentenceTransformer(model_name, device=device)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(
                f"Embeddings model loaded, dimension: {self.embedding_dimension}"
            )
        except Exception as e:
            logger.error(f"Failed to load embeddings model: {e}")
            raise

    def encode_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to encode

        Returns:
            List of floats representing the embedding vector
        """
        if not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.embedding_dimension

        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_tensor=False)

            # Convert to list and ensure float type
            embedding_list = embedding.tolist()

            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding_list

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimension

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts and keep track of indices
        non_empty_texts = []
        text_indices = []

        for i, text in enumerate(texts):
            if text.strip():
                non_empty_texts.append(text)
                text_indices.append(i)

        if not non_empty_texts:
            logger.warning("No non-empty texts provided for batch embedding")
            return [[0.0] * self.embedding_dimension] * len(texts)

        try:
            # Generate embeddings in batches
            embeddings = []

            for i in range(0, len(non_empty_texts), batch_size):
                batch = non_empty_texts[i : i + batch_size]
                batch_embeddings = self.model.encode(
                    batch, convert_to_tensor=False, batch_size=batch_size
                )

                # Convert to list format
                for embedding in batch_embeddings:
                    embeddings.append(embedding.tolist())

            # Create result array with zero vectors for empty texts
            result = [[0.0] * self.embedding_dimension] * len(texts)

            # Fill in the actual embeddings
            for embedding, orig_index in zip(embeddings, text_indices, strict=False):
                result[orig_index] = embedding

            logger.info(f"Generated embeddings for {len(texts)} texts")
            return result

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dimension] * len(texts)

    def encode_query(self, query: str) -> list[float]:
        """Generate embedding for a search query.

        This method is identical to encode_text but provides semantic clarity
        for query encoding.

        Args:
            query: Search query to encode

        Returns:
            List of floats representing the query embedding vector
        """
        return self.encode_text(query)

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors.

        Returns:
            Embedding vector dimension
        """
        return self.embedding_dimension

    def get_model_info(self) -> dict:
        """Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": str(self.device) if self.device else "auto",
            "embedding_dimension": self.embedding_dimension,
            "max_seq_length": getattr(self.model, "max_seq_length", "unknown"),
        }


class MockEmbeddingsService(EmbeddingsService):
    """Mock embeddings service for testing purposes."""

    def __init__(self, embedding_dimension: int = 384):
        """Initialize mock embeddings service.

        Args:
            embedding_dimension: Dimension of mock embeddings
        """
        self.model_name = "mock"
        self.device = "cpu"
        self.embedding_dimension = embedding_dimension
        self.model = None

        logger.info(
            f"Initialized mock embeddings service with dimension {embedding_dimension}"
        )

    def encode_text(self, text: str) -> list[float]:
        """Generate mock embedding for text.

        Args:
            text: Text to encode (not actually used)

        Returns:
            Mock embedding vector
        """
        import hashlib
        import struct

        # Generate deterministic mock embedding based on text hash
        text_hash = hashlib.md5(text.encode()).digest()

        # Convert hash to float values
        embedding = []
        for i in range(0, min(len(text_hash), self.embedding_dimension * 4), 4):
            chunk = text_hash[i : i + 4]
            if len(chunk) == 4:
                # Convert 4 bytes to float
                float_val = struct.unpack("f", chunk)[0]
                # Normalize to [-1, 1] range
                normalized = max(-1.0, min(1.0, float_val / 1e6))
                embedding.append(normalized)

        # Pad with zeros if needed
        while len(embedding) < self.embedding_dimension:
            embedding.append(0.0)

        return embedding[: self.embedding_dimension]

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate mock embeddings for batch of texts.

        Args:
            texts: List of texts to encode
            batch_size: Ignored in mock implementation

        Returns:
            List of mock embedding vectors
        """
        return [self.encode_text(text) for text in texts]


# Global instance for reuse
_embeddings_service: EmbeddingsService | None = None


def get_embeddings_service(
    model_name: str = "all-MiniLM-L6-v2",
    device: str | None = None,
    use_mock: bool = False,
) -> EmbeddingsService:
    """Get or create the global embeddings service instance.

    Args:
        model_name: Name of the sentence-transformers model to use
        device: Device to run the model on
        use_mock: Whether to use mock embeddings service

    Returns:
        EmbeddingsService instance
    """
    global _embeddings_service

    if _embeddings_service is None:
        if use_mock:
            _embeddings_service = MockEmbeddingsService()
        else:
            _embeddings_service = EmbeddingsService(model_name, device)

    return _embeddings_service
