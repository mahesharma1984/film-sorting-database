"""
RAG for Development Methodology - Queryable Documentation Search

Semantic retrieval system for methodology docs with authority-weighted ranking.
Turns passive documentation into a queryable verification tool.

Usage:
    # Build index
    python -m lib.rag.indexer

    # Query
    python -m lib.rag.query "How does authentication work?"

    # Programmatic
    from lib.rag.query import query_docs
    results = query_docs("deployment procedure", top_k=5)
"""

from .query import query_docs
from .retriever import RAGRetriever

__all__ = ["query_docs", "RAGRetriever"]
