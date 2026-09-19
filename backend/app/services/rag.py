"""
Deep RAG Pipeline for Bokaro Steel Limited (BSL) Safety SOPs.
Chunks approved safety procedures and references, embeds them with all-MiniLM-L6-v2,
and performs hybrid dense-semantic + lexical retrieval with multilingual query expansion.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from app.config import RAG_DOCUMENTS_DIR
from app.services import embeddings, translation

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

_CATEGORY_ANCHOR_TERMS: dict[str, str] = {
    "gas_leak": "gas leak emergency response toxic flammable CO BFG escape SCBA isolation valve upwind evacuation",
    "fire": "fire emergency response immediate actions firefighting extinguisher class A B C D electrical evacuation",
    "electrical_hazard": "electrical safety lockout tagout LOTO arc flash switchgear transformer shock hazard de-energize",
    "mechanical_failure": "mechanical isolation permit to work PTW conveyor equipment failure emergency stop jammed",
    "slip_fall": "slip trip fall prevention housekeeping wet floor platform ladder scaffolding safety harness",
    "ppe_violation": "mandatory personal protective equipment PPE helmet safety boots face shield gloves harness",
    "molten_metal_spill": "molten metal slag breakout liquid steel ladle tundish splash hazard dry area evacuation",
    "confined_space_emergency": "confined space emergency response rescue permit atmospheric testing gas detector SCBA",
    "crane_lifting_failure": "crane heavy lifting failure wire rope snap suspended load dropped load rigging hook exclusion zone",
    "vehicle_traffic_incident": "vehicle traffic collision dumper rail locomotive forklift accident traffic management",
    "chemical_spill": "chemical spill response acid leak hydrochloric sulfuric neutralization containment eyewash",
}


@dataclass
class Chunk:
    doc_title: str
    doc_path: str
    incident_types: list[str]
    section: str
    text: str
    embedding: np.ndarray | None = field(default=None, repr=False)


_chunks: list[Chunk] = []
_embeddings: np.ndarray | None = None


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    raw_meta, body = match.groups()
    meta: dict = {}
    for line in raw_meta.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key] = value
    return meta, body


def _split_sections(body: str) -> list[tuple[str, str]]:
    sections = []
    current_header = "Introduction"
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_header, "\n".join(current_lines).strip()))
            current_header = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_header, "\n".join(current_lines).strip()))
    return [(h, c) for h, c in sections if c]


def build_index() -> None:
    global _chunks, _embeddings

    chunks: list[Chunk] = []
    for md_path in sorted(RAG_DOCUMENTS_DIR.rglob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception:
            continue
        meta, body = _parse_frontmatter(text)
        incident_types = meta.get("incident_type", [])
        title = meta.get("title", md_path.stem)
        for section_header, section_text in _split_sections(body):
            chunks.append(
                Chunk(
                    doc_title=title,
                    doc_path=str(md_path.relative_to(RAG_DOCUMENTS_DIR.parent)),
                    incident_types=incident_types,
                    section=section_header,
                    text=section_text,
                )
            )

    if not chunks:
        _chunks, _embeddings = [], None
        return

    texts = [f"{c.doc_title} — {c.section}\n{c.text}" for c in chunks]
    _chunks = chunks
    _embeddings = embeddings.encode(texts)


def _has_non_latin(text: str) -> bool:
    """Returns True if string contains non-ASCII/Indic characters."""
    return any(ord(c) > 127 for c in text)


def _expand_query(query: str, incident_type: str | None = None) -> str:
    """
    Translates Indic queries into English and injects category-grounded domain anchors.
    """
    clean_q = query.strip()
    if _has_non_latin(clean_q):
        try:
            # Map through neural/dictionary translator to standard English
            translated = translation.to_english(clean_q, "hi")
            clean_q = f"{translated} {clean_q}"
        except Exception:
            pass

    if incident_type and incident_type in _CATEGORY_ANCHOR_TERMS:
        clean_q = f"{clean_q} {_CATEGORY_ANCHOR_TERMS[incident_type]}"

    return clean_q.strip()


def retrieve(query: str, incident_type: str | None = None, top_k: int = 3) -> list[dict]:
    """
    Deep hybrid retrieval over Bokaro Steel safety procedures:
    1. Normalizes and expands queries across Hindi, Indian vernacular, and English.
    2. Filters or boosts candidate chunks matching the incident type.
    3. Blends dense semantic cosine similarity with exact keyword term hits.
    """
    if _embeddings is None:
        build_index()
    if _embeddings is None or len(_chunks) == 0:
        return []

    expanded_query = _expand_query(query, incident_type)
    query_vec = embeddings.encode([expanded_query])[0]

    candidate_indices = list(range(len(_chunks)))
    if incident_type:
        type_filtered = [i for i in candidate_indices if incident_type in _chunks[i].incident_types]
        if type_filtered:
            candidate_indices = type_filtered

    # Dense semantic cosine similarities
    dense_sims = _embeddings[candidate_indices] @ query_vec

    # Lexical matching on query tokens
    query_words = set(re.findall(r"\w+", expanded_query.lower()))
    scored_candidates = []
    for idx, d_sim in zip(candidate_indices, dense_sims):
        chunk = _chunks[idx]
        chunk_text = f"{chunk.doc_title} {chunk.section} {chunk.text}".lower()
        keyword_hits = sum(1 for w in query_words if len(w) >= 3 and w in chunk_text)
        # Hybrid combined score
        hybrid_score = float(d_sim) + 0.02 * min(keyword_hits, 10)
        scored_candidates.append((idx, hybrid_score))

    ranked = sorted(scored_candidates, key=lambda x: -x[1])[:top_k]

    results = []
    for idx, score in ranked:
        c = _chunks[idx]
        results.append(
            {
                "doc_title": c.doc_title,
                "doc_path": c.doc_path,
                "section": c.section,
                "text": c.text,
                "similarity": round(float(score), 3),
            }
        )
    return results


def generate_guidance(category: str | None, query: str) -> tuple[str, list[dict]]:
    if not category:
        return (
            "Incident category could not be determined with sufficient confidence. "
            "This has been flagged for manual review by a safety officer rather than "
            "generating guidance from an uncertain classification.",
            [],
        )

    chunks = retrieve(query, incident_type=category, top_k=3)
    if not chunks:
        return (
            "No approved procedure was found for this incident type in the current "
            "knowledge base. Do not treat this as an absence of risk — escalate to the "
            "designated safety authority for manual guidance.",
            [],
        )

    lines = [f"Guidance for a reported {category.replace('_', ' ')} incident, grounded in approved procedure:\n"]
    for c in chunks:
        first_lines = "\n".join(c["text"].splitlines()[:6])
        lines.append(f"**{c['section']}** (from {c['doc_title']}):\n{first_lines}\n")

    sources = [{"title": c["doc_title"], "section": c["section"], "path": c["doc_path"]} for c in chunks]
    return "\n".join(lines), sources
