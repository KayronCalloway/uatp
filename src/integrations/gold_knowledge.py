#!/usr/bin/env python3
"""
Gold Standard Knowledge System
==============================

World-class knowledge architecture for AI learning from interactions.

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE SYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: PRINCIPLES (meta-patterns across domains)             │
│  Layer 3: CONCEPTS (synthesized from multiple insights)         │
│  Layer 2: INSIGHTS (extracted from individual capsules)         │
│  Layer 1: EMBEDDINGS (semantic vectors for similarity)          │
│  Layer 0: CAPSULES (immutable source of truth)                  │
├─────────────────────────────────────────────────────────────────┤
│                     RETRIEVAL SYSTEM                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Semantic│  │Confidence│  │ Recency │  │ Outcome │           │
│  │ Search  │ ×│ Weight  │ ×│ Decay   │ ×│ Verified│ = Score   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
├─────────────────────────────────────────────────────────────────┤
│                     LEARNING LOOP                                │
│  Capsule → Extract → Embed → Index → Retrieve → Outcome → Learn │
└─────────────────────────────────────────────────────────────────┘

Gold Standard Principles:
1. Semantic search via embeddings (not keywords)
2. Confidence-weighted retrieval (calibrated by outcomes)
3. Hierarchical knowledge (facts → insights → concepts → principles)
4. Incremental learning (real-time, not batch)
5. Active verification (outcomes update knowledge confidence)
6. Memory decay (unused knowledge fades, used knowledge strengthens)
7. Never blocks user (all heavy ops async)
"""

import hashlib
import json
import math
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Try to import sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None

# Fallback: Use Ollama's embedding API
import requests


@dataclass
class KnowledgeNode:
    """A node in the knowledge hierarchy."""

    id: str
    level: int  # 0=capsule, 1=insight, 2=concept, 3=principle
    content: str
    embedding: Optional[np.ndarray] = None
    confidence: float = 0.5
    source_ids: List[str] = field(default_factory=list)  # Parent nodes
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    outcome_positive: int = 0
    outcome_negative: int = 0
    tags: List[str] = field(default_factory=list)

    @property
    def outcome_ratio(self) -> float:
        """Ratio of positive to total outcomes."""
        total = self.outcome_positive + self.outcome_negative
        if total == 0:
            return 0.5  # Unknown
        return self.outcome_positive / total

    @property
    def recency_score(self) -> float:
        """Decay based on time since last access."""
        days_old = (time.time() - self.last_accessed) / 86400
        return math.exp(-0.1 * days_old)  # Half-life ~7 days

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "level": self.level,
            "content": self.content,
            "confidence": self.confidence,
            "source_ids": self.source_ids,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "outcome_positive": self.outcome_positive,
            "outcome_negative": self.outcome_negative,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(
        cls, d: Dict, embedding: Optional[np.ndarray] = None
    ) -> "KnowledgeNode":
        return cls(
            id=d["id"],
            level=d["level"],
            content=d["content"],
            embedding=embedding,
            confidence=d.get("confidence", 0.5),
            source_ids=d.get("source_ids", []),
            created_at=d.get("created_at", time.time()),
            last_accessed=d.get("last_accessed", time.time()),
            access_count=d.get("access_count", 0),
            outcome_positive=d.get("outcome_positive", 0),
            outcome_negative=d.get("outcome_negative", 0),
            tags=d.get("tags", []),
        )


class EmbeddingEngine:
    """
    Semantic embedding engine.

    Uses sentence-transformers if available, falls back to Ollama.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        ollama_url: str = "http://localhost:11434",
    ):
        self.ollama_url = ollama_url
        self.model = None
        self.use_ollama = False
        self.dimension = 384  # Default for MiniLM

        # Query embedding cache (avoid repeated Ollama calls)
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_max = 100

        if EMBEDDINGS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
                print(f"[Embeddings] Using sentence-transformers ({model_name})")
            except Exception as e:
                print(f"[Embeddings] sentence-transformers failed: {e}")
                self.use_ollama = True
        else:
            self.use_ollama = True
            print("[Embeddings] Using Ollama API fallback")

    def embed(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text (cached)."""
        # Check cache first
        cache_key = text[:200]  # Truncate for cache key
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = None
        if self.model:
            try:
                result = self.model.encode(text, convert_to_numpy=True)
            except Exception:
                pass

        if result is None and self.use_ollama:
            result = self._embed_ollama(text)

        # Cache result
        if result is not None:
            if len(self._cache) >= self._cache_max:
                # Remove oldest (first) entry
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = result

        return result

    def embed_batch(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """Batch embed multiple texts."""
        if self.model:
            try:
                return list(self.model.encode(texts, convert_to_numpy=True))
            except Exception:
                pass

        # Fallback to individual embeds
        return [self.embed(t) for t in texts]

    def _embed_ollama(self, text: str) -> Optional[np.ndarray]:
        """Use Ollama's embedding API."""
        try:
            resp = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=5,  # Fast timeout - skip if slow
            )
            if resp.status_code == 200:
                embedding = resp.json().get("embedding")
                if embedding:
                    self.dimension = len(embedding)
                    return np.array(embedding)
        except Exception:
            pass
        return None


class GoldKnowledgeSystem:
    """
    Gold standard knowledge system.

    Features:
    - Semantic search via embeddings
    - Hierarchical knowledge (capsules → insights → concepts → principles)
    - Confidence-weighted retrieval
    - Outcome-based learning
    - Memory decay and reinforcement
    """

    def __init__(
        self,
        db_path: str = "uatp_dev.db",
        knowledge_db: str = "knowledge.db",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.db_path = db_path
        self.knowledge_db = knowledge_db

        # Embedding engine
        self.embedder = EmbeddingEngine(model_name=embedding_model)

        # In-memory index for fast retrieval
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._embeddings: Dict[str, np.ndarray] = {}

        # State
        self._ready = False
        self._building = False

        # Initialize knowledge database
        self._init_db()

    def _init_db(self):
        """Initialize knowledge database schema."""
        conn = sqlite3.connect(self.knowledge_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                level INTEGER NOT NULL,
                content TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                source_ids TEXT,  -- JSON array
                created_at REAL,
                last_accessed REAL,
                access_count INTEGER DEFAULT 0,
                outcome_positive INTEGER DEFAULT 0,
                outcome_negative INTEGER DEFAULT 0,
                tags TEXT  -- JSON array
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                node_id TEXT PRIMARY KEY,
                embedding BLOB,  -- numpy array as bytes
                dimension INTEGER,
                FOREIGN KEY (node_id) REFERENCES knowledge_nodes(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                source_id TEXT,
                target_id TEXT,
                relation TEXT,  -- 'derived_from', 'related_to', 'supports', 'contradicts'
                weight REAL DEFAULT 1.0,
                PRIMARY KEY (source_id, target_id, relation)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_level ON knowledge_nodes(level)
        """)

        conn.commit()
        conn.close()

    def build_async(self):
        """Build knowledge index in background."""
        if self._building:
            return
        thread = threading.Thread(target=self._build_index, daemon=True)
        thread.start()

    def _build_index(self):
        """Build the knowledge index from capsules."""
        self._building = True
        start = time.time()

        try:
            # Load existing knowledge nodes
            self._load_nodes()

            # Index new capsules
            self._index_new_capsules()

            self._ready = True
            print(
                f"[GoldKnowledge] Index built in {(time.time() - start) * 1000:.0f}ms"
            )
            print(
                f"[GoldKnowledge] {len(self._nodes)} nodes, {len(self._embeddings)} embeddings"
            )

        except Exception as e:
            print(f"[GoldKnowledge] Build failed: {e}")
        finally:
            self._building = False

    def _load_nodes(self):
        """Load existing knowledge nodes into memory."""
        conn = sqlite3.connect(self.knowledge_db)
        cursor = conn.cursor()

        # Load nodes
        cursor.execute("SELECT * FROM knowledge_nodes")
        for row in cursor.fetchall():
            node_dict = {
                "id": row[0],
                "level": row[1],
                "content": row[2],
                "confidence": row[3],
                "source_ids": json.loads(row[4]) if row[4] else [],
                "created_at": row[5],
                "last_accessed": row[6],
                "access_count": row[7],
                "outcome_positive": row[8],
                "outcome_negative": row[9],
                "tags": json.loads(row[10]) if row[10] else [],
            }
            self._nodes[row[0]] = KnowledgeNode.from_dict(node_dict)

        # Load embeddings
        cursor.execute("SELECT node_id, embedding, dimension FROM embeddings")
        for row in cursor.fetchall():
            if row[1]:
                self._embeddings[row[0]] = np.frombuffer(row[1], dtype=np.float32)

        conn.close()

    def _index_new_capsules(self):
        """Index capsules that haven't been processed yet."""
        if not Path(self.db_path).exists():
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get capsules with content
        cursor.execute("""
            SELECT
                capsule_id,
                json_extract(payload, '$.prompt') as prompt,
                json_extract(payload, '$.response') as response,
                timestamp
            FROM capsules
            WHERE json_extract(payload, '$.prompt') IS NOT NULL
              AND json_extract(payload, '$.response') IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 200
        """)

        new_capsules = []
        for row in cursor.fetchall():
            capsule_id, prompt, response, timestamp = row
            node_id = f"capsule_{capsule_id}"

            # Skip if already indexed
            if node_id in self._nodes:
                continue

            if prompt and response:
                new_capsules.append(
                    {
                        "id": node_id,
                        "capsule_id": capsule_id,
                        "prompt": prompt,
                        "response": response,
                        "timestamp": timestamp,
                    }
                )

        conn.close()

        if not new_capsules:
            return

        print(f"[GoldKnowledge] Indexing {len(new_capsules)} new capsules...")

        # Generate embeddings for new capsules
        texts = [f"{c['prompt']}\n{c['response']}" for c in new_capsules]
        embeddings = self.embedder.embed_batch(texts)

        # Create nodes and save
        knowledge_conn = sqlite3.connect(self.knowledge_db)
        knowledge_cursor = knowledge_conn.cursor()

        for capsule, embedding in zip(new_capsules, embeddings, strict=False):
            node = KnowledgeNode(
                id=capsule["id"],
                level=0,  # Capsule level
                content=f"Q: {capsule['prompt'][:500]}\nA: {capsule['response'][:1000]}",
                embedding=embedding,
                confidence=0.5,
                source_ids=[capsule["capsule_id"]],
            )

            self._nodes[node.id] = node
            if embedding is not None:
                self._embeddings[node.id] = embedding

            # Save to DB
            knowledge_cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_nodes
                (id, level, content, confidence, source_ids, created_at, last_accessed, access_count, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    node.id,
                    node.level,
                    node.content,
                    node.confidence,
                    json.dumps(node.source_ids),
                    node.created_at,
                    node.last_accessed,
                    node.access_count,
                    json.dumps(node.tags),
                ),
            )

            if embedding is not None:
                knowledge_cursor.execute(
                    """
                    INSERT OR REPLACE INTO embeddings (node_id, embedding, dimension)
                    VALUES (?, ?, ?)
                """,
                    (node.id, embedding.astype(np.float32).tobytes(), len(embedding)),
                )

        knowledge_conn.commit()
        knowledge_conn.close()

    def search(
        self,
        query: str,
        max_results: int = 5,
        min_level: int = 0,
        max_level: int = 3,
    ) -> List[Tuple[KnowledgeNode, float]]:
        """
        Semantic search with confidence-weighted ranking.

        Score = semantic_similarity * confidence * recency * outcome_ratio
        """
        if not self._ready or not self._embeddings:
            return []

        # Embed query
        query_embedding = self.embedder.embed(query)
        if query_embedding is None:
            return []

        # Calculate scores
        scored = []
        for node_id, embedding in self._embeddings.items():
            node = self._nodes.get(node_id)
            if not node or not (min_level <= node.level <= max_level):
                continue

            # Cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding) + 1e-8
            )

            # Combined score
            score = (
                similarity
                * node.confidence
                * node.recency_score
                * (0.5 + 0.5 * node.outcome_ratio)  # Outcome bonus
            )

            scored.append((node, score))

        # Sort and return top results
        scored.sort(key=lambda x: x[1], reverse=True)

        # Update access stats for returned nodes
        for node, _ in scored[:max_results]:
            node.last_accessed = time.time()
            node.access_count += 1

        return scored[:max_results]

    def get_context(self, query: str, max_chars: int = 1000) -> str:
        """
        Get relevant context for a query.

        Returns formatted string ready for injection into prompt.
        """
        results = self.search(query, max_results=3)

        if not results:
            return ""

        parts = []
        total_chars = 0

        for node, score in results:
            if total_chars >= max_chars:
                break

            # Format based on level
            if node.level == 0:
                prefix = "Previous interaction"
            elif node.level == 1:
                prefix = "Known insight"
            elif node.level == 2:
                prefix = "Established concept"
            else:
                prefix = "Principle"

            content = node.content[:300]
            confidence_pct = int(node.confidence * 100)

            part = f"[{prefix} ({confidence_pct}% confidence)]: {content}"
            parts.append(part)
            total_chars += len(part)

        if not parts:
            return ""

        return "Relevant knowledge:\n" + "\n\n".join(parts)

    def record_outcome(self, query: str, positive: bool):
        """
        Record outcome for knowledge used in a response.

        This is the learning loop - outcomes update knowledge confidence.
        """
        # Find nodes that were likely used for this query
        results = self.search(query, max_results=5)

        conn = sqlite3.connect(self.knowledge_db)
        cursor = conn.cursor()

        for node, score in results:
            if positive:
                node.outcome_positive += 1
                # Increase confidence (bounded)
                node.confidence = min(0.95, node.confidence + 0.05 * score)
            else:
                node.outcome_negative += 1
                # Decrease confidence (bounded)
                node.confidence = max(0.1, node.confidence - 0.05 * score)

            # Persist
            cursor.execute(
                """
                UPDATE knowledge_nodes
                SET confidence = ?, outcome_positive = ?, outcome_negative = ?, last_accessed = ?
                WHERE id = ?
            """,
                (
                    node.confidence,
                    node.outcome_positive,
                    node.outcome_negative,
                    time.time(),
                    node.id,
                ),
            )

        conn.commit()
        conn.close()

    def add_insight(
        self, content: str, source_capsule_ids: List[str], tags: List[str] = None
    ) -> str:
        """
        Add a new insight (Level 1) derived from capsules.
        """
        node_id = f"insight_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

        embedding = self.embedder.embed(content)

        node = KnowledgeNode(
            id=node_id,
            level=1,
            content=content,
            embedding=embedding,
            confidence=0.6,  # Insights start slightly above baseline
            source_ids=source_capsule_ids,
            tags=tags or [],
        )

        self._nodes[node_id] = node
        if embedding is not None:
            self._embeddings[node_id] = embedding

        # Persist
        conn = sqlite3.connect(self.knowledge_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_nodes
            (id, level, content, confidence, source_ids, created_at, last_accessed, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                node.id,
                node.level,
                node.content,
                node.confidence,
                json.dumps(node.source_ids),
                node.created_at,
                node.last_accessed,
                json.dumps(node.tags),
            ),
        )

        if embedding is not None:
            cursor.execute(
                """
                INSERT OR REPLACE INTO embeddings (node_id, embedding, dimension)
                VALUES (?, ?, ?)
            """,
                (node_id, embedding.astype(np.float32).tobytes(), len(embedding)),
            )

        # Add edges from sources
        for source_id in source_capsule_ids:
            cursor.execute(
                """
                INSERT OR IGNORE INTO knowledge_edges (source_id, target_id, relation)
                VALUES (?, ?, 'derived_from')
            """,
                (f"capsule_{source_id}", node_id),
            )

        conn.commit()
        conn.close()

        return node_id

    def synthesize_concept(
        self, insight_ids: List[str], concept_name: str, description: str
    ) -> str:
        """
        Synthesize a concept (Level 2) from multiple insights.
        """
        node_id = f"concept_{hashlib.sha256(concept_name.encode()).hexdigest()[:12]}"

        content = f"{concept_name}: {description}"
        embedding = self.embedder.embed(content)

        # Average confidence of source insights
        source_confidences = [
            self._nodes[iid].confidence for iid in insight_ids if iid in self._nodes
        ]
        avg_confidence = (
            sum(source_confidences) / len(source_confidences)
            if source_confidences
            else 0.5
        )

        node = KnowledgeNode(
            id=node_id,
            level=2,
            content=content,
            embedding=embedding,
            confidence=avg_confidence,
            source_ids=insight_ids,
            tags=[concept_name.lower()],
        )

        self._nodes[node_id] = node
        if embedding is not None:
            self._embeddings[node_id] = embedding

        # Persist (similar to add_insight)
        conn = sqlite3.connect(self.knowledge_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_nodes
            (id, level, content, confidence, source_ids, created_at, last_accessed, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                node.id,
                node.level,
                node.content,
                node.confidence,
                json.dumps(node.source_ids),
                node.created_at,
                node.last_accessed,
                json.dumps(node.tags),
            ),
        )

        if embedding is not None:
            cursor.execute(
                """
                INSERT OR REPLACE INTO embeddings (node_id, embedding, dimension)
                VALUES (?, ?, ?)
            """,
                (node_id, embedding.astype(np.float32).tobytes(), len(embedding)),
            )

        conn.commit()
        conn.close()

        return node_id

    @property
    def stats(self) -> Dict:
        """Get system statistics."""
        level_counts = {}
        for node in self._nodes.values():
            level_counts[node.level] = level_counts.get(node.level, 0) + 1

        return {
            "ready": self._ready,
            "total_nodes": len(self._nodes),
            "total_embeddings": len(self._embeddings),
            "capsules": level_counts.get(0, 0),
            "insights": level_counts.get(1, 0),
            "concepts": level_counts.get(2, 0),
            "principles": level_counts.get(3, 0),
            "embedding_dimension": self.embedder.dimension,
        }


# Singleton
_system: Optional[GoldKnowledgeSystem] = None


def get_knowledge_system(db_path: str = "uatp_dev.db") -> GoldKnowledgeSystem:
    """Get or create the global knowledge system."""
    global _system
    if _system is None:
        _system = GoldKnowledgeSystem(db_path=db_path)
        _system.build_async()
    return _system
