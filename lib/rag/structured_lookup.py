"""Structured-first retrieval: deterministic keyword matching before embeddings.

Implements deterministic keyword-based matching against Quick Reference
and Canonical Sources tables, replacing embedding-based lookup when a
high-confidence match is found.

R/P Split: This module contains PRECISION tasks (keyword matching, phrase detection).
REASONING tasks (semantic ranking) remain in retriever.py.

Architecture:
    Step 1: Structured Lookup (this module) - deterministic keyword matching
    Step 2: Within-file search (retriever.py) - semantic ranking within matched file
    Step 3: Broad fallback (retriever.py) - existing Phase A->B pipeline
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from . import config


@dataclass
class StructuredMatch:
    """Result of structured lookup against Quick Reference / Canonical Sources."""
    matched: bool
    file_paths: List[str]
    confidence: float       # 0.0-1.0
    match_type: str         # "quick_reference" | "canonical" | "none"
    metadata: Dict[str, any]


def match_quick_reference(
    query: str,
    qr_entries: List[Tuple[str, str]],
    threshold: float = None
) -> Tuple[Optional[List[str]], Optional[str], float]:
    """Match query against Quick Reference questions using keyword overlap + phrase boost.

    Algorithm:
        1. Expand abbreviations in query and questions
        2. Extract keywords from both (stopword filtered)
        3. Compute Jaccard similarity
        4. Add phrase boost for 2-3 word phrase matches
        5. Return file path if score >= threshold

    Returns:
        (file_paths, matched_question, score) or (None, None, 0.0)
    """
    from .precision_filter import expand_abbreviations, extract_query_keywords

    if threshold is None:
        threshold = config.STRUCTURED_QR_THRESHOLD

    expanded_query = expand_abbreviations(query)
    query_keywords = extract_query_keywords(expanded_query)

    best_match = None
    best_score = 0.0
    best_question = None

    for question, file_path in qr_entries:
        expanded_question = expand_abbreviations(question)
        question_keywords = extract_query_keywords(expanded_question)

        # Jaccard similarity
        intersection = query_keywords & question_keywords
        union = query_keywords | question_keywords
        jaccard = len(intersection) / len(union) if union else 0.0

        # Phrase boost
        phrase_boost = 0.0
        question_lower = expanded_question.lower()
        query_lower = expanded_query.lower()

        words = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", question_lower)

        # Check trigrams
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            if len(trigram) >= config.STRUCTURED_QR_MIN_PHRASE_LENGTH and trigram in query_lower:
                phrase_boost = config.STRUCTURED_QR_PHRASE_BOOST_TRIGRAM
                break

        # Check bigrams
        if phrase_boost == 0.0:
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                if len(bigram) >= config.STRUCTURED_QR_MIN_PHRASE_LENGTH and bigram in query_lower:
                    phrase_boost = config.STRUCTURED_QR_PHRASE_BOOST_BIGRAM
                    break

        final_score = jaccard + phrase_boost

        if final_score > best_score:
            best_score = final_score
            best_match = file_path
            best_question = question

    if best_score >= threshold:
        return [best_match], best_question, best_score

    return None, None, 0.0


def match_canonical_sources(
    query: str,
    canonical_map: Dict[str, str],
    threshold: float = None
) -> Tuple[Optional[str], Optional[str], float]:
    """Match query against canonical source concepts.

    Uses substring matching first, then token overlap scoring.

    Returns:
        (file_path, concept, score) or (None, None, 0.0)
    """
    from .precision_filter import expand_abbreviations

    if threshold is None:
        threshold = config.STRUCTURED_CANONICAL_THRESHOLD

    expanded_query = expand_abbreviations(query)
    query_lower = expanded_query.lower()

    best_match = None
    best_score = 0.0
    best_concept = None

    for concept, file_path in canonical_map.items():
        concept_lower = concept.lower()

        # Exact substring match (highest priority)
        if concept_lower in query_lower:
            return file_path, concept, 1.0

        # Token overlap scoring
        query_tokens = set(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", query_lower))
        concept_tokens = set(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", concept_lower))

        intersection = query_tokens & concept_tokens
        min_tokens = min(len(query_tokens), len(concept_tokens))

        if min_tokens > 0:
            score = len(intersection) / min_tokens

            if score > best_score:
                best_score = score
                best_match = file_path
                best_concept = concept

    if best_score >= threshold:
        return best_match, best_concept, best_score

    return None, None, 0.0


def structured_lookup(
    query: str,
    qr_entries: List[Tuple[str, str]],
    canonical_map: Dict[str, str],
    qr_threshold: float = None,
    canonical_threshold: float = None
) -> StructuredMatch:
    """Perform structured lookup across Quick Reference and Canonical Sources.

    Priority:
        1. Quick Reference (user-friendly questions) - higher priority
        2. Canonical Sources (concept keywords)
        3. No match -> return unmatched for fallback to embedding search

    Returns:
        StructuredMatch with match status, file paths, confidence, and metadata
    """
    # Priority 1: Quick Reference
    qr_files, qr_question, qr_score = match_quick_reference(query, qr_entries, qr_threshold)
    if qr_files:
        return StructuredMatch(
            matched=True,
            file_paths=qr_files,
            confidence=0.9,
            match_type="quick_reference",
            metadata={
                "matched_question": qr_question,
                "score": qr_score
            }
        )

    # Priority 2: Canonical Sources
    canonical_file, canonical_concept, canonical_score = match_canonical_sources(
        query, canonical_map, canonical_threshold
    )
    if canonical_file:
        return StructuredMatch(
            matched=True,
            file_paths=[canonical_file],
            confidence=0.85,
            match_type="canonical",
            metadata={
                "matched_concept": canonical_concept,
                "score": canonical_score
            }
        )

    # No match
    return StructuredMatch(
        matched=False,
        file_paths=[],
        confidence=0.0,
        match_type="none",
        metadata={}
    )
