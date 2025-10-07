"""
Semantic cache implementation for Jerry AI assistant.

This module provides semantic caching capabilities to improve response times
and reduce computational overhead for similar queries.
"""

import hashlib
import json
import logging
import sqlite3
import time
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..data.models import CacheEntry
from ..rag.embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


class SemanticCache:
    """Semantic cache for AI assistant responses."""

    def __init__(
        self,
        cache_db_path: str = "./data/cache.db",
        similarity_threshold: float = 0.95,
        default_ttl_seconds: int = 3600,
        max_cache_size: int = 10000,
    ):
        """Initialize semantic cache.

        Args:
            cache_db_path: Path to SQLite cache database
            similarity_threshold: Minimum similarity for cache hit
            default_ttl_seconds: Default TTL for cache entries
            max_cache_size: Maximum number of cache entries
        """
        self.cache_db_path = Path(cache_db_path)
        self.similarity_threshold = similarity_threshold
        self.default_ttl_seconds = default_ttl_seconds
        self.max_cache_size = max_cache_size

        # Ensure cache directory exists
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Get embeddings service for similarity calculation
        self.embeddings_service = get_embeddings_service()

        logger.info(f"Initialized semantic cache at {cache_db_path}")

    def _init_database(self) -> None:
        """Initialize the cache database schema."""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id TEXT PRIMARY KEY,
                    query_hash TEXT UNIQUE NOT NULL,
                    query_text TEXT NOT NULL,
                    query_embedding BLOB NOT NULL,
                    response TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    context_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    last_accessed TIMESTAMP NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    ttl_seconds INTEGER NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            """)

            # Create indexes for performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_query_hash ON cache_entries(query_hash)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)"
            )

            conn.commit()

    def _serialize_embedding(self, embedding: list[float]) -> bytes:
        """Serialize embedding vector to bytes.

        Args:
            embedding: Embedding vector

        Returns:
            Serialized embedding
        """
        return json.dumps(embedding).encode("utf-8")

    def _deserialize_embedding(self, data: bytes) -> list[float]:
        """Deserialize embedding vector from bytes.

        Args:
            data: Serialized embedding data

        Returns:
            Embedding vector
        """
        return json.loads(data.decode("utf-8"))

    def _calculate_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        import math

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

    def _generate_query_hash(self, query: str, context_hash: str = "") -> str:
        """Generate hash for query and context.

        Args:
            query: Query text
            context_hash: Optional context hash

        Returns:
            Query hash
        """
        combined = f"{query.lower().strip()}:{context_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _generate_context_hash(self, context: dict[str, Any]) -> str:
        """Generate hash for conversation context.

        Args:
            context: Context dictionary

        Returns:
            Context hash
        """
        # Sort keys for consistent hashing
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()

    def _cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()

        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE expires_at < ?", (now,)
            )
            removed_count = cursor.rowcount
            conn.commit()

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} expired cache entries")

        return removed_count

    def _cleanup_lru(self) -> int:
        """Remove least recently used entries if cache is full.

        Returns:
            Number of entries removed
        """
        with sqlite3.connect(self.cache_db_path) as conn:
            # Count current entries
            cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
            current_count = cursor.fetchone()[0]

            if current_count <= self.max_cache_size:
                return 0

            # Remove oldest entries
            entries_to_remove = (
                current_count - self.max_cache_size + 100
            )  # Remove extra for buffer

            cursor = conn.execute(
                """
                DELETE FROM cache_entries
                WHERE id IN (
                    SELECT id FROM cache_entries
                    ORDER BY last_accessed ASC
                    LIMIT ?
                )
            """,
                (entries_to_remove,),
            )

            removed_count = cursor.rowcount
            conn.commit()

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} LRU cache entries")

        return removed_count

    def get(
        self, query: str, context: dict[str, Any] | None = None, model_used: str = ""
    ) -> str | None:
        """Get cached response for query.

        Args:
            query: Query text
            context: Optional conversation context
            model_used: Model identifier for cache key

        Returns:
            Cached response if found, None otherwise
        """
        if not query.strip():
            return None

        # Clean up expired entries periodically
        if hash(query) % 100 == 0:  # 1% of requests trigger cleanup
            self._cleanup_expired()

        # Generate context hash
        context_hash = self._generate_context_hash(context or {})

        try:
            # Generate query embedding
            query_embedding = self.embeddings_service.encode_text(query)

            # Search for similar cached entries
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, query_text, query_embedding, response, access_count, expires_at
                    FROM cache_entries
                    WHERE context_hash = ? AND model_used = ?
                    AND expires_at > ?
                """,
                    (context_hash, model_used, datetime.utcnow()),
                )

                candidates = cursor.fetchall()

            # Find best match by similarity
            best_match = None
            best_similarity = 0.0

            for entry in candidates:
                (
                    entry_id,
                    entry_query,
                    entry_embedding_data,
                    response,
                    access_count,
                    expires_at,
                ) = entry

                # Deserialize embedding
                entry_embedding = self._deserialize_embedding(entry_embedding_data)

                # Calculate similarity
                similarity = self._calculate_similarity(
                    query_embedding, entry_embedding
                )

                if (
                    similarity > best_similarity
                    and similarity >= self.similarity_threshold
                ):
                    best_similarity = similarity
                    best_match = (entry_id, response, access_count)

            if best_match:
                entry_id, response, access_count = best_match

                # Update access statistics
                with sqlite3.connect(self.cache_db_path) as conn:
                    conn.execute(
                        """
                        UPDATE cache_entries
                        SET last_accessed = ?, access_count = access_count + 1
                        WHERE id = ?
                    """,
                        (datetime.utcnow(), entry_id),
                    )
                    conn.commit()

                logger.debug(f"Cache hit with similarity {best_similarity:.3f}")
                return response

        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")

        return None

    def put(
        self,
        query: str,
        response: str,
        context: dict[str, Any] | None = None,
        model_used: str = "",
        ttl_seconds: int | None = None,
    ) -> bool:
        """Store response in cache.

        Args:
            query: Query text
            response: Response to cache
            context: Optional conversation context
            model_used: Model identifier
            ttl_seconds: Time to live in seconds

        Returns:
            True if stored successfully
        """
        if not query.strip() or not response.strip():
            return False

        ttl = ttl_seconds or self.default_ttl_seconds
        context_hash = self._generate_context_hash(context or {})
        query_hash = self._generate_query_hash(query, context_hash)

        try:
            # Generate query embedding
            query_embedding = self.embeddings_service.encode_text(query)
            embedding_data = self._serialize_embedding(query_embedding)

            # Create cache entry
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=ttl)

            entry = CacheEntry(
                id=uuid4(),
                query_hash=query_hash,
                query_embedding=query_embedding,
                response=response,
                model_used=model_used,
                context_hash=context_hash,
                created_at=now,
                last_accessed=now,
                access_count=1,
                ttl_seconds=ttl,
            )

            # Store in database
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache_entries
                    (id, query_hash, query_text, query_embedding, response, model_used,
                     context_hash, created_at, last_accessed, access_count, ttl_seconds, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(entry.id),
                        entry.query_hash,
                        query,
                        embedding_data,
                        response,
                        model_used,
                        context_hash,
                        now,
                        now,
                        1,
                        ttl,
                        expires_at,
                    ),
                )
                conn.commit()

            # Cleanup if cache is getting full
            self._cleanup_lru()

            logger.debug(f"Cached response for query (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries removed
        """
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.execute("DELETE FROM cache_entries")
            removed_count = cursor.rowcount
            conn.commit()

        logger.info(f"Cleared {removed_count} cache entries")
        return removed_count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                # Total entries
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                total_entries = cursor.fetchone()[0]

                # Expired entries
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM cache_entries WHERE expires_at < ?",
                    (datetime.utcnow(),),
                )
                expired_entries = cursor.fetchone()[0]

                # Total access count
                cursor = conn.execute("SELECT SUM(access_count) FROM cache_entries")
                total_accesses = cursor.fetchone()[0] or 0

                # Average access count
                avg_accesses = total_accesses / max(total_entries, 1)

                # Cache size (approximate)
                cursor = conn.execute("""
                    SELECT SUM(LENGTH(query_text) + LENGTH(response) + LENGTH(query_embedding))
                    FROM cache_entries
                """)
                cache_size_bytes = cursor.fetchone()[0] or 0

            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
                "total_accesses": total_accesses,
                "avg_accesses_per_entry": round(avg_accesses, 2),
                "cache_size_mb": round(cache_size_bytes / (1024 * 1024), 2),
                "max_cache_size": self.max_cache_size,
                "similarity_threshold": self.similarity_threshold,
                "default_ttl_seconds": self.default_ttl_seconds,
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def optimize(self) -> dict[str, int]:
        """Optimize cache by cleaning expired and LRU entries.

        Returns:
            Dictionary with optimization results
        """
        expired_removed = self._cleanup_expired()
        lru_removed = self._cleanup_lru()

        # Vacuum database to reclaim space
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute("VACUUM")
                conn.commit()
        except Exception as e:
            logger.error(f"Error vacuuming cache database: {e}")

        return {
            "expired_removed": expired_removed,
            "lru_removed": lru_removed,
            "total_removed": expired_removed + lru_removed,
        }


class InMemoryCache:
    """Simple in-memory cache for frequently accessed data."""

    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 300):
        """Initialize in-memory cache.

        Args:
            max_size: Maximum number of cache entries
            default_ttl_seconds: Default TTL for entries
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)

        logger.info(f"Initialized in-memory cache (max_size={max_size})")

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self.cache:
            return None

        value, expires_at = self.cache[key]

        if time.time() > expires_at:
            # Expired, remove it
            del self.cache[key]
            return None

        return value

    def put(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Time to live in seconds
        """
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = time.time() + ttl

        # Clean up if cache is full
        if len(self.cache) >= self.max_size:
            self._cleanup_lru()

        self.cache[key] = (value, expires_at)

    def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        return count

    def _cleanup_lru(self) -> None:
        """Remove least recently used entries."""
        # For simplicity, remove oldest 25% of entries
        if len(self.cache) < self.max_size:
            return

        # Sort by expiration time (oldest first)
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])

        # Remove oldest 25%
        remove_count = len(self.cache) // 4
        for i in range(remove_count):
            key = sorted_items[i][0]
            del self.cache[key]

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        now = time.time()
        expired_count = sum(
            1 for _, expires_at in self.cache.values() if expires_at < now
        )

        return {
            "total_entries": len(self.cache),
            "active_entries": len(self.cache) - expired_count,
            "expired_entries": expired_count,
            "max_size": self.max_size,
            "default_ttl_seconds": self.default_ttl_seconds,
        }


# Global cache instances
_semantic_cache: SemanticCache | None = None
_memory_cache: InMemoryCache | None = None


def get_semantic_cache() -> SemanticCache:
    """Get or create the global semantic cache instance.

    Returns:
        SemanticCache instance
    """
    global _semantic_cache

    if _semantic_cache is None:
        from .config import get_config

        config = get_config()

        # Use configuration if available
        cache_config = getattr(config, "cache", {})
        cache_db_path = cache_config.get("semantic_db_path", "./data/cache.db")
        similarity_threshold = cache_config.get("similarity_threshold", 0.95)
        default_ttl = cache_config.get("default_ttl_seconds", 3600)
        max_size = cache_config.get("max_cache_size", 10000)

        _semantic_cache = SemanticCache(
            cache_db_path=cache_db_path,
            similarity_threshold=similarity_threshold,
            default_ttl_seconds=default_ttl,
            max_cache_size=max_size,
        )

    return _semantic_cache


def get_memory_cache() -> InMemoryCache:
    """Get or create the global in-memory cache instance.

    Returns:
        InMemoryCache instance
    """
    global _memory_cache

    if _memory_cache is None:
        _memory_cache = InMemoryCache()

    return _memory_cache
