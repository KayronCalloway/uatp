"""
Capsule Embeddings Module
=========================

Generates and manages vector embeddings for capsules.
Enables similarity search, clustering, and semantic retrieval.
"""

from .capsule_embedder import CapsuleEmbedder, get_embedder

__all__ = ["CapsuleEmbedder", "get_embedder"]
