"""
Universal SOP Document Ingestion and Parser.
Supports DOCX, PDF, Markdown, and Plain Text safety procedures.
DOCX parsing is implemented natively using Python's standard library
(zipfile + xml.etree.ElementTree) with zero third-party binary dependencies.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from app.config import BACKEND_DIR, PROJECT_ROOT, RAG_DOCUMENTS_DIR
from app.services import rag

logger = logging.getLogger(__name__)

TENANT_SOPS_DIR = BACKEND_DIR / "data" / "tenant_sops"
TENANT_SOPS_DIR.mkdir(parents=True, exist_ok=True)


def parse_docx_bytes(file_bytes: bytes) -> str:
    """Extracts text from DOCX document natively using standard library zipfile & XML."""
    import io
    text_parts = []
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx_zip:
        try:
            xml_content = docx_zip.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            # Find all paragraph elements (w:p)
            for p in tree.iter():
                if p.tag.endswith("p"):
                    para_texts = [node.text for node in p.iter() if node.tag.endswith("t") and node.text]
                    if para_texts:
                        text_parts.append("".join(para_texts))
        except Exception as exc:
            logger.error(f"Error extracting DOCX XML: {exc}")
            raise ValueError(f"Corrupted or invalid DOCX archive: {exc}")

    return "\n\n".join(text_parts)


def parse_pdf_bytes(file_bytes: bytes) -> str:
    """Extracts text from PDF stream or text chunks."""
    # Simple robust text stream parser for PDF without requiring poppler
    try:
        raw = file_bytes.decode("latin-1", errors="ignore")
        # Extract text within BT ... ET blocks
        matches = re.findall(r"BT[\s\S]*?ET", raw)
        lines = []
        for block in matches:
            # Extract parenthesized text strings (e.g. (Sample Text) Tj)
            text_tokens = re.findall(r"\((.*?)\)", block)
            if text_tokens:
                lines.append(" ".join(text_tokens))
        extracted = "\n".join(lines).strip()
        if len(extracted) > 50:
            return extracted
    except Exception:
        pass

    # Fallback to UTF-8 / ASCII clean text filtering
    cleaned = re.sub(r"[^\x20-\x7E\n\r\t]", " ", file_bytes.decode("utf-8", errors="ignore"))
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if len(p.strip()) > 30]
    return "\n\n".join(paragraphs) if paragraphs else cleaned[:4000]


def extract_sections(text: str) -> list[tuple[str, str]]:
    """Splits safety document text into header-based sections."""
    sections = []
    current_header = "Emergency Directives & Scope"
    current_lines = []

    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        # Detect headings (Markdown ## or uppercase lines or numbering)
        if stripped.startswith("## ") or (len(stripped) < 60 and (stripped.isupper() or re.match(r"^\d+\.\s+[A-Z]", stripped))):
            if current_lines:
                sections.append((current_header, "\n".join(current_lines).strip()))
            current_header = stripped.lstrip("#").strip()
            current_lines = []
        else:
            if stripped:
                current_lines.append(stripped)

    if current_lines:
        sections.append((current_header, "\n".join(current_lines).strip()))

    return [(h, c) for h, c in sections if c]


def ingest_sop_document(
    plant_id: str,
    filename: str,
    file_bytes: bytes,
    sop_id: str,
    title: str,
    version: str,
    incident_types: list[str],
    reviewer: str = "Safety Officer Command",
    reviewed_by_safety_officer: bool = True,
) -> dict[str, Any]:
    """
    Parses and stores an approved SOP document for a specific plant tenant,
    generates Markdown with governance frontmatter, and indexes into RAG.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".docx":
        raw_text = parse_docx_bytes(file_bytes)
    elif ext == ".pdf":
        raw_text = parse_pdf_bytes(file_bytes)
    else:
        # Markdown or Plain Text
        raw_text = file_bytes.decode("utf-8", errors="replace")

    sections = extract_sections(raw_text)
    if not sections:
        sections = [("General Operating Procedure", raw_text)]

    # Format into validated markdown file with frontmatter
    plant_sop_dir = TENANT_SOPS_DIR / plant_id
    plant_sop_dir.mkdir(parents=True, exist_ok=True)

    safe_sop_id = re.sub(r"[^a-zA-Z0-9_-]", "_", sop_id)
    target_md_path = plant_sop_dir / f"{safe_sop_id}.md"

    md_lines = [
        "---",
        f"sop_id: {sop_id}",
        f"title: {title}",
        f"version: '{version}'",
        f"incident_type: [{', '.join(incident_types)}]",
        f"reviewed_by_safety_officer: {str(reviewed_by_safety_officer).lower()}",
        f"reviewer: '{reviewer}'",
        f"plant_id: '{plant_id}'",
        "---",
        "",
        f"# {title}",
        "",
    ]

    for header, content in sections:
        md_lines.append(f"## {header}")
        md_lines.append(content)
        md_lines.append("")

    target_md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # Also register file in RAG directory if plant matches active
    shared_tenant_dir = RAG_DOCUMENTS_DIR / "tenants" / plant_id
    shared_tenant_dir.mkdir(parents=True, exist_ok=True)
    (shared_tenant_dir / f"{safe_sop_id}.md").write_text("\n".join(md_lines), encoding="utf-8")

    # Rebuild RAG index to include newly ingested SOP immediately
    try:
        rag.build_index()
    except Exception as exc:
        logger.warning(f"RAG rebuild after SOP ingestion warning: {exc}")

    return {
        "sop_id": sop_id,
        "title": title,
        "version": version,
        "plant_id": plant_id,
        "incident_types": incident_types,
        "section_count": len(sections),
        "file_path": str(target_md_path),
        "status": "active" if reviewed_by_safety_officer else "pending_review",
    }
