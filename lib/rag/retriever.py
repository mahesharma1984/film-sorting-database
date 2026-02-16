"""Hybrid semantic + keyword + authority retrieval engine."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from . import config
from .metadata import get_authority_boost, parse_canonical_sources_table

# Optional dependencies
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    if not TYPE_CHECKING:
        SentenceTransformer = None
        np = None

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    if not TYPE_CHECKING:
        BM25Okapi = None


class RAGRetriever:
    """Hybrid retrieval engine for documentation chunks.

    Combines three signals for ranking:
    - Semantic similarity (embedding cosine distance)
    - Keyword matching (BM25)
    - Authority scoring (document status + freshness)

    Query pipeline:
        1. Structured Lookup: Deterministic keyword matching (fast, precise)
        2. Phase A (Precision): Keyword extraction, classification, filtering
        3. Phase B (Reasoning): Semantic ranking of filtered candidates
    """

    def __init__(
        self,
        index_file: Path = config.INDEX_FILE,
        embeddings_file: Path = config.EMBEDDINGS_FILE
    ):
        if not HAS_EMBEDDINGS:
            print("Error: sentence-transformers and numpy required")
            print("Install with: pip install sentence-transformers numpy")
            sys.exit(1)

        if not index_file.exists():
            print(f"Error: Index file not found: {index_file}")
            print("Build index with: python -m lib.rag.indexer")
            sys.exit(1)

        if not embeddings_file.exists():
            print(f"Error: Embeddings file not found: {embeddings_file}")
            print("Build index with: python -m lib.rag.indexer")
            sys.exit(1)

        print("Loading RAG index...")
        self.chunks = self._load_index(index_file)
        self.embeddings = np.load(embeddings_file)
        self.bm25 = self._build_bm25_index(self.chunks) if HAS_BM25 else None
        self.model = self._load_model()

        # Load layered retrieval data
        self.quick_ref_index = self._load_quick_reference()
        self.canonical_sources = self._load_canonical_sources()

        # Load structured lookup data
        self.qr_entries = None
        if config.ENABLE_STRUCTURED_LOOKUP:
            from .metadata import parse_quick_reference_table
            self.qr_entries = parse_quick_reference_table()

        print(f"  Loaded {len(self.chunks)} chunks")
        print(f"  Embeddings shape: {self.embeddings.shape}")
        if self.bm25:
            print(f"  BM25 index: ready")
        else:
            print(f"  BM25 not available (install rank-bm25 for keyword search)")
        if self.quick_ref_index:
            print(f"  Quick Reference: {len(self.quick_ref_index)} questions")
        if self.canonical_sources:
            print(f"  Canonical Sources: {len(self.canonical_sources)} concepts")
        if self.qr_entries:
            print(f"  Structured Lookup: {len(self.qr_entries)} QR questions")

    def query(
        self,
        query_text: str,
        top_k: int = config.DEFAULT_TOP_K,
        filter_status: Optional[List[str]] = None,
        enable_precision_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k chunks using hybrid scoring.

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            filter_status: Optional filter ["AUTHORITATIVE", "STABLE"]
            enable_precision_filter: Enable Phase A precision pre-filter

        Returns:
            List of chunks with scores, sorted by final_score desc
        """
        if not query_text:
            return self._top_authoritative(top_k)

        # ========== STEP 1: STRUCTURED LOOKUP ==========
        if config.ENABLE_STRUCTURED_LOOKUP and self.qr_entries:
            from .structured_lookup import structured_lookup

            match = structured_lookup(
                query_text,
                self.qr_entries,
                self.canonical_sources or {}
            )

            if match.matched:
                query_embedding = self._embed_query(query_text)
                results = self._get_chunks_from_files(
                    match.file_paths,
                    top_k,
                    query_embedding,
                    query_text
                )
                for r in results:
                    r["lookup_method"] = match.match_type
                    r["structured_confidence"] = match.confidence
                return results

        # ========== STEP 2: BROAD SEARCH ==========
        query_embedding = self._embed_query(query_text)

        # Try legacy Quick Reference if structured lookup disabled
        if not config.ENABLE_STRUCTURED_LOOKUP:
            qr_files = self._check_quick_reference(query_text)
            if qr_files:
                return self._get_chunks_from_files(qr_files, top_k, query_embedding, query_text)

        # ========== PHASE A: PRECISION PRE-FILTER ==========
        if enable_precision_filter and config.ENABLE_PRECISION_FILTER:
            from .precision_filter import (
                expand_abbreviations,
                extract_query_keywords,
                classify_query_type,
                filter_chunks_by_precision
            )

            expanded_query = expand_abbreviations(query_text)
            query_keywords = extract_query_keywords(expanded_query)
            query_type, canonical_file = classify_query_type(expanded_query, query_keywords)

            candidate_indices = filter_chunks_by_precision(
                self.chunks,
                query_keywords,
                query_type,
                canonical_file,
                suppress_navigation=config.PRECISION_SUPPRESS_NAVIGATION,
                min_keyword_overlap=config.PRECISION_MIN_KEYWORD_OVERLAP
            )

            if not candidate_indices:
                candidate_indices = list(range(len(self.chunks)))
        else:
            candidate_indices = list(range(len(self.chunks)))
            expanded_query = query_text
            query_keywords = set()
            canonical_file = self._detect_canonical_concepts(query_text)

        # ========== PHASE B: SEMANTIC RANKING ==========
        candidate_chunks = [self.chunks[i] for i in candidate_indices]
        candidate_embeddings = self.embeddings[candidate_indices]

        semantic_scores = np.dot(candidate_embeddings, query_embedding)
        keyword_scores = self._keyword_search_subset(expanded_query if enable_precision_filter else query_text, candidate_indices)

        # Boost keywords in headings
        if enable_precision_filter and query_keywords:
            keyword_scores = self._boost_heading_matches(
                candidate_chunks, query_keywords, keyword_scores
            )

        authority_scores = self._authority_boost(candidate_chunks)

        # Apply canonical boost
        if canonical_file:
            authority_scores = self._apply_canonical_boost_subset(
                authority_scores, canonical_file, candidate_chunks
            )

        # Combine scores
        if enable_precision_filter and len(candidate_indices) < len(self.chunks):
            final_scores = (
                0.5 * semantic_scores +
                0.35 * keyword_scores +
                0.15 * authority_scores
            )
        else:
            final_scores = (
                config.SEMANTIC_WEIGHT * semantic_scores +
                config.KEYWORD_WEIGHT * keyword_scores +
                config.AUTHORITY_WEIGHT * authority_scores
            )

        results = self._rank_and_format_subset(
            final_scores, semantic_scores, keyword_scores,
            authority_scores, candidate_chunks, candidate_indices,
            top_k, filter_status,
            precision_filtered=enable_precision_filter
        )

        # Routing suppression
        results = self._suppress_routing_docs(results)

        return results

    def _load_index(self, index_file: Path) -> List[Dict]:
        """Load chunks from index.jsonl."""
        chunks = []
        with open(index_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    chunk = json.loads(line)
                    chunk.pop('embedding', None)
                    chunks.append(chunk)
                except json.JSONDecodeError:
                    continue
        return chunks

    def _load_model(self):
        """Load embedding model."""
        try:
            return SentenceTransformer(config.EMBEDDING_MODEL)
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)

    def _build_bm25_index(self, chunks: List[Dict]):
        """Build BM25 index from chunk content."""
        if not HAS_BM25:
            return None

        try:
            corpus = [
                chunk["heading_text"] + " " + chunk["content"]
                for chunk in chunks
            ]
            tokenized_corpus = [self._tokenize(doc) for doc in corpus]
            return BM25Okapi(tokenized_corpus)
        except Exception as e:
            print(f"Warning: BM25 index build failed: {e}")
            return None

    def _load_quick_reference(self) -> Optional[List[Dict]]:
        """Load Quick Reference index for Layer 1 lookups."""
        if not config.ENABLE_QUICK_REFERENCE:
            return None

        if not config.QUICK_REFERENCE_INDEX_FILE.exists():
            return None

        try:
            with open(config.QUICK_REFERENCE_INDEX_FILE, 'r', encoding='utf-8') as f:
                qr_index = json.load(f)

            if config.QUICK_REFERENCE_EMBEDDINGS_FILE.exists():
                qr_embeddings = np.load(config.QUICK_REFERENCE_EMBEDDINGS_FILE)
                for i, entry in enumerate(qr_index):
                    entry['embedding'] = qr_embeddings[i]

            return qr_index

        except Exception as e:
            print(f"Warning: Failed to load Quick Reference index: {e}")
            return None

    def _load_canonical_sources(self) -> Optional[Dict[str, str]]:
        """Load Canonical Sources mapping."""
        if not config.ENABLE_CANONICAL_BOOST:
            return None

        try:
            return parse_canonical_sources_table()
        except Exception as e:
            print(f"Warning: Failed to load Canonical Sources: {e}")
            return None

    def _embed_query(self, query_text: str):
        """Embed query text."""
        try:
            embedding = self.model.encode(
                [query_text],
                normalize_embeddings=True
            )[0]
            return embedding
        except Exception as e:
            print(f"Error embedding query: {e}")
            return np.zeros(config.EMBEDDING_DIM)

    def _keyword_search_subset(self, query_text: str, indices: List[int]):
        """BM25 scoring for a subset of chunks."""
        if not self.bm25:
            return np.zeros(len(indices))

        try:
            query_tokens = self._tokenize(query_text)
            all_scores = self.bm25.get_scores(query_tokens)
            subset_scores = all_scores[indices]

            max_score = subset_scores.max() if subset_scores.max() > 0 else 1.0
            return subset_scores / max_score

        except Exception as e:
            print(f"Warning: BM25 subset search failed: {e}")
            return np.zeros(len(indices))

    def _authority_boost(self, chunks: List[Dict]):
        """Calculate authority boost with freshness decay."""
        boosts = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            status = metadata.get("status", "unmarked")
            verified = metadata.get("verified", "unknown")
            canonical = metadata.get("canonical", False)
            boost = get_authority_boost(status, verified, canonical=canonical)
            boosts.append(boost)

        return np.array(boosts)

    def _tokenize(self, text: str):
        """Tokenize text for BM25 with light normalization."""
        text = text.lower()
        return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text)

    def _check_quick_reference(self, query_text: str) -> Optional[List[str]]:
        """Check if query matches Quick Reference questions (embedding-based)."""
        if not self.quick_ref_index or not config.ENABLE_QUICK_REFERENCE:
            return None

        query_embedding = self._embed_query(query_text)

        best_match_idx = -1
        best_similarity = 0.0

        for i, entry in enumerate(self.quick_ref_index):
            if 'embedding' in entry:
                similarity = np.dot(entry['embedding'], query_embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = i

        if best_similarity >= config.QUICK_REFERENCE_THRESHOLD:
            matched_file = self.quick_ref_index[best_match_idx]['file']
            return [matched_file]

        return None

    def _get_chunks_from_files(
        self, file_paths: List[str], top_k: int,
        query_embedding, query_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get chunks from specific files and rank semantically within them."""
        matching_indices = []
        matching_chunks = []

        for i, chunk in enumerate(self.chunks):
            chunk_file = chunk.get('source_file', '')
            if any(file_path in chunk_file for file_path in file_paths):
                matching_indices.append(i)
                matching_chunks.append(chunk)

        if not matching_chunks:
            return []

        matching_embeddings = self.embeddings[matching_indices]
        semantic_scores = np.dot(matching_embeddings, query_embedding)

        if query_text and self.bm25:
            keyword_scores = self._keyword_search_subset(query_text, matching_indices)
        else:
            keyword_scores = np.zeros(len(matching_indices))

        authority_scores = self._authority_boost(matching_chunks)

        if query_text:
            final_scores = (
                config.STRUCTURED_WITHIN_FILE_SEMANTIC_WEIGHT * semantic_scores +
                config.STRUCTURED_WITHIN_FILE_KEYWORD_WEIGHT * keyword_scores +
                config.STRUCTURED_WITHIN_FILE_AUTHORITY_WEIGHT * authority_scores
            )
        else:
            final_scores = 0.8 * semantic_scores + 0.2 * authority_scores

        sorted_indices = np.argsort(final_scores)[::-1][:top_k]

        results = []
        for idx in sorted_indices:
            result = {
                "chunk": matching_chunks[idx],
                "final_score": round(float(final_scores[idx]), 3),
                "semantic_score": round(float(semantic_scores[idx]), 3),
                "keyword_score": round(float(keyword_scores[idx]), 3) if query_text else 0.0,
                "authority_score": round(float(authority_scores[idx]), 3),
                "section_reference": matching_chunks[idx]["section_reference"],
                "layer": "quick_reference"
            }
            results.append(result)

        return results

    def _detect_canonical_concepts(self, query_text: str) -> Optional[str]:
        """Detect if query mentions a canonical concept."""
        if not self.canonical_sources or not config.ENABLE_CANONICAL_BOOST:
            return None

        query_lower = query_text.lower()

        for concept, file_path in self.canonical_sources.items():
            escaped_concept = re.escape(concept)
            concept_pattern = r'\b' + escaped_concept.replace(r'\ ', r'\s+') + r'\b'
            if re.search(concept_pattern, query_lower):
                return file_path

        return None

    def _apply_canonical_boost_subset(
        self, authority_scores, canonical_file: str, chunks: List[Dict]
    ):
        """Apply canonical boost to a subset of chunks."""
        boosted_scores = authority_scores.copy()

        for i, chunk in enumerate(chunks):
            chunk_file = chunk.get('source_file', '')
            if canonical_file in chunk_file:
                boosted_scores[i] *= config.CANONICAL_BOOST_MULTIPLIER

        return boosted_scores

    def _boost_heading_matches(
        self, chunks: List[Dict], query_keywords: set, keyword_scores
    ):
        """Boost keyword scores when keywords appear in section headings."""
        boosted_scores = keyword_scores.copy()

        for i, chunk in enumerate(chunks):
            heading = chunk.get('heading_text', '').lower()
            normalized_heading = re.sub(r'[[\]()]', '', heading)

            heading_keyword_count = 0
            for kw in query_keywords:
                if kw in heading or kw in normalized_heading:
                    heading_keyword_count += 1

            if heading_keyword_count > 0:
                boost_multiplier = min(2.0, 1.0 + (heading_keyword_count * 0.5))
                boosted_scores[i] *= boost_multiplier

        return boosted_scores

    def _rank_and_format_subset(
        self, final_scores, semantic_scores, keyword_scores,
        authority_scores, chunks: List[Dict], original_indices: List[int],
        top_k: int, filter_status: Optional[List[str]],
        precision_filtered: bool = False
    ) -> List[Dict[str, Any]]:
        """Rank and format results."""
        if filter_status:
            filter_mask = np.array([
                chunk["metadata"].get("status", "unmarked") in filter_status
                for chunk in chunks
            ])
            final_scores = final_scores * filter_mask

        top_subset_indices = np.argsort(final_scores)[::-1][:top_k]

        results = []
        for subset_idx in top_subset_indices:
            result = {
                "chunk": chunks[subset_idx],
                "final_score": round(float(final_scores[subset_idx]), 3),
                "semantic_score": round(float(semantic_scores[subset_idx]), 3),
                "keyword_score": round(float(keyword_scores[subset_idx]), 3),
                "authority_score": round(float(authority_scores[subset_idx]), 3),
                "section_reference": chunks[subset_idx]["section_reference"]
            }
            if precision_filtered:
                result["precision_filtered"] = True
            results.append(result)

        return results

    def _suppress_routing_docs(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suppress routing docs if they reference files already in the result set."""
        if not config.ENABLE_ROUTING_SUPPRESSION:
            return results

        result_files = set()
        for r in results:
            source_file = r['chunk'].get('source_file', '')
            result_files.add(source_file)

        filtered_results = []

        for r in results:
            chunk = r['chunk']
            content = chunk.get('content', '')

            is_routing = False
            referenced_file = None

            for pattern in config.ROUTING_PATTERNS:
                match = re.search(pattern, content)
                if match:
                    referenced_file = match.group(1)
                    is_routing = True
                    break

            if is_routing and referenced_file:
                for other_r in results:
                    other_file = other_r['chunk'].get('source_file', '')
                    if referenced_file in other_file:
                        break
                else:
                    filtered_results.append(r)
            else:
                filtered_results.append(r)

        return filtered_results

    def _top_authoritative(self, top_k: int) -> List[Dict[str, Any]]:
        """Return top-k most authoritative docs (for empty queries)."""
        authority_scores = self._authority_boost(self.chunks)
        top_indices = np.argsort(authority_scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            result = {
                "chunk": self.chunks[idx],
                "final_score": round(float(authority_scores[idx]), 3),
                "semantic_score": 0.0,
                "keyword_score": 0.0,
                "authority_score": round(float(authority_scores[idx]), 3),
                "section_reference": self.chunks[idx]["section_reference"]
            }
            results.append(result)

        return results
