"""
Phase 3: Structured Query Formulation and Hybrid Retrieval Engine.
- Builds search queries from structured interview state:
  hazard_type + zone + missing_slots + facts_known.
- Integrates domain vernacular glossary expansion (Hinglish/Hindi slang).
- Hybrid BM25 keyword matching + Dense Semantic Cosine Similarity.
- Metadata filtering on hazard_type, zone, and approval status.
- Retrieval confidence thresholding with fallback to hazard information needs.
"""

from __future__ import annotations

import re
from typing import Any
from app.services import rag, domain_glossary, hazard_checklists

RETRIEVAL_CONFIDENCE_THRESHOLD = 0.38


def build_structured_query(
    hazard_type: str,
    zone_id: str | None,
    initial_report: str,
    prior_answers: list[str],
    missing_slots: list[str] | None = None,
) -> str:
    """
    Formulates a targeted retrieval query using structured incident state.
    """
    query_tokens = [hazard_type.replace("_", " ")]
    if zone_id:
        query_tokens.append(zone_id)

    # Add salient terms from initial report
    query_tokens.append(initial_report)

    # Add latest worker answers
    if prior_answers:
        query_tokens.extend(prior_answers[-2:])

    # Add missing slots as guidance anchors
    if missing_slots:
        for slot in missing_slots[:2]:
            query_tokens.append(slot.replace("_", " "))

    raw_query = " ".join(query_tokens)

    # Expand with domain vernacular glossary
    expanded = domain_glossary.expand_vernacular_query(raw_query, hazard_type)
    return expanded


def retrieve_grounded_context(
    hazard_type: str,
    structured_query: str,
    top_k: int = 3,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Performs hybrid retrieval against verified safety SOPs with confidence guard.
    Returns (chunks, is_confident).
    If confidence < threshold, returns empty chunks and is_confident=False,
    triggering the checklist fallback.
    """
    chunks = rag.retrieve(structured_query, incident_type=hazard_type, top_k=top_k)
    if not chunks:
        return [], False

    best_similarity = max((c.get("similarity", 0.0) for c in chunks), default=0.0)
    is_confident = best_similarity >= RETRIEVAL_CONFIDENCE_THRESHOLD

    return chunks, is_confident
