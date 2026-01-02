"""
Capsule Embedder
================

Generates vector embeddings for capsules using TF-IDF.
Pure Python, no external APIs required.

Features:
- TF-IDF vectorization (configurable dimensions)
- Batched processing for efficiency
- Cosine similarity search
- Works fully offline
"""

import hashlib
import json
import logging
import math
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "tfidf-v1"
EMBEDDING_DIM = 512  # Hash-based TF-IDF dimension


class CapsuleEmbedder:
    """
    Generates and manages embeddings for capsules.

    Usage:
        embedder = CapsuleEmbedder(db_url)

        # Embed a single capsule
        embedding = embedder.embed_capsule(capsule_data)

        # Find similar capsules
        similar = embedder.find_similar(query_text, limit=10)

        # Backfill all capsules
        embedder.backfill_all()
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the embedder.

        Args:
            database_url: PostgreSQL connection URL. If None, uses DATABASE_URL env var.
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://uatp_user@localhost:5432/uatp_capsule_engine"
        )
        self.model_name = MODEL_NAME
        self.embedding_dim = EMBEDDING_DIM
        # IDF values computed from corpus (updated during backfill)
        self._idf_cache: Dict[str, float] = {}
        self._doc_count = 0

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split on non-alphanumeric."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z][a-z0-9]{2,}\b', text)
        return tokens

    def _hash_token(self, token: str, dim: int = EMBEDDING_DIM) -> int:
        """Hash a token to a dimension index."""
        h = hashlib.md5(token.encode()).hexdigest()
        return int(h, 16) % dim

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency (normalized)."""
        counts = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {token: count / total for token, count in counts.items()}

    def _compute_tfidf_vector(self, text: str) -> List[float]:
        """
        Compute TF-IDF vector using feature hashing.

        Uses hashing trick to map arbitrary vocabulary to fixed dimensions.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.embedding_dim

        tf = self._compute_tf(tokens)

        # Build vector using feature hashing
        vector = [0.0] * self.embedding_dim
        for token, tf_val in tf.items():
            # Use default IDF of 1.0 if not in cache (treats as common word)
            idf = self._idf_cache.get(token, 1.0)
            tfidf = tf_val * idf

            # Hash to dimension
            idx = self._hash_token(token)
            # Use sign hash to reduce collision bias
            sign = 1 if int(hashlib.md5((token + "_sign").encode()).hexdigest(), 16) % 2 == 0 else -1
            vector[idx] += sign * tfidf

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def _get_connection(self):
        """Get a database connection."""
        import psycopg2
        return psycopg2.connect(self.database_url)

    def _extract_text_from_capsule(self, capsule: Dict[str, Any]) -> str:
        """
        Extract text content from a capsule for embedding.

        Combines prompt, reasoning steps, and key metadata into a single text.
        """
        parts = []

        # Get payload (might be string or dict)
        payload = capsule.get("payload", {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}

        # Add prompt/task
        if prompt := payload.get("prompt"):
            parts.append(f"Task: {prompt}")

        # Add reasoning steps
        reasoning_steps = payload.get("reasoning_steps", [])
        for step in reasoning_steps[:10]:  # Limit to first 10 steps
            if isinstance(step, dict):
                if reasoning := step.get("reasoning"):
                    parts.append(reasoning[:500])  # Limit each step
            elif isinstance(step, str):
                parts.append(step[:500])

        # Add decision/output if present
        if decision := payload.get("decision"):
            parts.append(f"Decision: {decision[:500]}")

        # Fallback to capsule_type if no content
        if not parts:
            if capsule_type := capsule.get("capsule_type"):
                parts.append(capsule_type)

        text = " ".join(parts)

        # Ensure we have some text
        if not text.strip():
            text = "empty capsule"

        return text[:8000]  # Limit total length

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text using TF-IDF.

        Args:
            text: Text to embed

        Returns:
            List of floats (embedding vector)
        """
        return self._compute_tfidf_vector(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return [self._compute_tfidf_vector(t) for t in texts]

    def build_idf_from_corpus(self, texts: List[str]) -> None:
        """
        Build IDF values from a corpus of texts.

        Call this before embedding to improve quality.
        """
        doc_freq: Dict[str, int] = Counter()
        self._doc_count = len(texts)

        for text in texts:
            tokens = set(self._tokenize(text))
            for token in tokens:
                doc_freq[token] += 1

        # Compute IDF: log(N / df) with smoothing
        for token, df in doc_freq.items():
            self._idf_cache[token] = math.log((self._doc_count + 1) / (df + 1)) + 1

        logger.info(f"Built IDF from {self._doc_count} documents, {len(self._idf_cache)} unique terms")

    def embed_capsule(self, capsule: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a capsule.

        Args:
            capsule: Capsule data dict

        Returns:
            Embedding vector
        """
        text = self._extract_text_from_capsule(capsule)
        return self.embed_text(text)

    def save_embedding(self, capsule_id: str, embedding: List[float]) -> bool:
        """
        Save embedding to database.

        Args:
            capsule_id: Capsule identifier
            embedding: Embedding vector

        Returns:
            True if successful
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE capsules
                    SET embedding = %s,
                        embedding_model = %s,
                        embedding_created_at = %s
                    WHERE capsule_id = %s
                    """,
                    (
                        json.dumps(embedding),
                        self.model_name,
                        datetime.now(timezone.utc),
                        capsule_id
                    )
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            a, b: Embedding vectors

        Returns:
            Similarity score (0-1)
        """
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def find_similar(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Tuple[str, float, datetime]]:
        """
        Find capsules similar to a query.

        Args:
            query: Query text
            limit: Maximum results
            min_similarity: Minimum similarity threshold

        Returns:
            List of (capsule_id, similarity, timestamp) tuples
        """
        query_embedding = self.embed_text(query)

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Get all capsules with embeddings
                cur.execute(
                    """
                    SELECT capsule_id, embedding, timestamp
                    FROM capsules
                    WHERE embedding IS NOT NULL
                    """
                )

                results = []
                for row in cur.fetchall():
                    capsule_id, embedding_data, timestamp = row
                    # Handle both JSON string and already-parsed list
                    if isinstance(embedding_data, str):
                        embedding = json.loads(embedding_data)
                    else:
                        embedding = embedding_data
                    similarity = self.cosine_similarity(query_embedding, embedding)
                    if similarity >= min_similarity:
                        results.append((capsule_id, similarity, timestamp))

                # Sort by similarity descending
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:limit]
        finally:
            conn.close()

    def backfill_all(self, batch_size: int = 50) -> Dict[str, int]:
        """
        Backfill embeddings for all capsules without embeddings.

        Args:
            batch_size: Number of capsules to process at once

        Returns:
            Stats dict with counts
        """
        conn = self._get_connection()
        stats = {"processed": 0, "skipped": 0, "errors": 0}

        try:
            with conn.cursor() as cur:
                # Get capsules without embeddings
                cur.execute(
                    """
                    SELECT capsule_id, payload
                    FROM capsules
                    WHERE embedding IS NULL
                    ORDER BY timestamp DESC
                    """
                )

                rows = cur.fetchall()
                total = len(rows)
                logger.info(f"Backfilling {total} capsules...")

                if total == 0:
                    return stats

                # First pass: extract all texts for IDF computation
                logger.info("Building IDF from corpus...")
                all_texts = []
                all_capsules = []
                for capsule_id, payload in rows:
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except json.JSONDecodeError:
                            payload = {}
                    capsule = {"capsule_id": capsule_id, "payload": payload}
                    all_capsules.append(capsule)
                    all_texts.append(self._extract_text_from_capsule(capsule))

                # Build IDF from corpus
                self.build_idf_from_corpus(all_texts)

                # Second pass: embed and save
                logger.info("Generating embeddings...")
                for i in range(0, total, batch_size):
                    batch_capsules = all_capsules[i:i + batch_size]
                    batch_texts = all_texts[i:i + batch_size]

                    # Generate embeddings
                    try:
                        embeddings = self.embed_texts(batch_texts)
                    except Exception as e:
                        logger.error(f"Batch embedding failed: {e}")
                        stats["errors"] += len(batch_capsules)
                        continue

                    # Save to database
                    for capsule, embedding in zip(batch_capsules, embeddings):
                        try:
                            cur.execute(
                                """
                                UPDATE capsules
                                SET embedding = %s,
                                    embedding_model = %s,
                                    embedding_created_at = %s
                                WHERE capsule_id = %s
                                """,
                                (
                                    json.dumps(embedding),
                                    self.model_name,
                                    datetime.now(timezone.utc),
                                    capsule["capsule_id"]
                                )
                            )
                            stats["processed"] += 1
                        except Exception as e:
                            logger.error(f"Failed to save {capsule['capsule_id']}: {e}")
                            stats["errors"] += 1

                    conn.commit()
                    logger.info(f"Processed {min(i + batch_size, total)}/{total} capsules")

        finally:
            conn.close()

        logger.info(f"Backfill complete: {stats}")
        return stats

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about embeddings in the database."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        COUNT(embedding) as with_embedding,
                        COUNT(*) - COUNT(embedding) as without_embedding
                    FROM capsules
                    """
                )
                row = cur.fetchone()
                return {
                    "total_capsules": row[0],
                    "with_embedding": row[1],
                    "without_embedding": row[2],
                    "coverage": f"{row[1]/row[0]*100:.1f}%" if row[0] > 0 else "0%"
                }
        finally:
            conn.close()


# Singleton instance
_embedder = None


def get_embedder() -> CapsuleEmbedder:
    """Get the singleton embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = CapsuleEmbedder()
    return _embedder


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Capsule Embedder")
    parser.add_argument("--backfill", action="store_true", help="Backfill all capsules")
    parser.add_argument("--stats", action="store_true", help="Show embedding stats")
    parser.add_argument("--search", type=str, help="Search for similar capsules")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    embedder = CapsuleEmbedder()

    if args.stats:
        stats = embedder.get_embedding_stats()
        print(f"Embedding Stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    if args.backfill:
        stats = embedder.backfill_all()
        print(f"Backfill complete: {stats}")

    if args.search:
        results = embedder.find_similar(args.search, limit=5)
        print(f"\nTop 5 similar capsules for '{args.search}':")
        for capsule_id, similarity, timestamp in results:
            print(f"  {capsule_id}: {similarity:.3f} ({timestamp})")
