"""
Adaptive verification: selects the next question for a category and scores
completed answers.

The scoring in `evaluate` is a rule-based placeholder for the "verification
score" described in the design — it is evidence/consistency-flavored (hedge
words lower confidence, direct-observation words raise it) but is not a
trained model. It exists so the routing tier has something real to act on
now, with a clear seam for a trained classifier or LLM-based consistency
check to replace it later.
"""

from __future__ import annotations

import json

from app.config import VERIFICATION_QUESTIONS_PATH
from app.services import rag_interview

_HEDGE_WORDS = ["not sure", "don't know", "dont know", "maybe", "i think", "didn't see", "didnt see", "not certain"]
_DIRECT_WORDS = ["saw", "confirmed", "yes", "definitely", "witnessed"]

with open(VERIFICATION_QUESTIONS_PATH) as f:
    _QUESTION_BANK = json.load(f)["question_sets"]


def get_questions(category: str, language: str = "en") -> list[str]:
    raw_list = _QUESTION_BANK.get(category, [])
    resolved = []
    for item in raw_list:
        if isinstance(item, dict):
            resolved.append(item.get(language) or item.get("en") or "")
        else:
            resolved.append(str(item))
    return resolved


def next_question(
    category: str,
    answered_count: int,
    language: str = "en",
    incident_description_en: str = "",
    prior_questions: list[str] | None = None,
    prior_answers_en: list[str] | None = None,
    zone_id: str | None = None,
    raw_description: str = "",
) -> tuple[str | None, int, list[str], str | None, bool]:
    """
    Returns (question_text, question_index, options, sop_source, is_personalized).
    Generates dynamic SOP-grounded questions via RAG first, falling back to static questions.
    """
    prior_q = prior_questions or []
    prior_a = prior_answers_en or []

    # 1. Attempt RAG-grounded adaptive personalized question first
    if incident_description_en or raw_description or prior_q:
        rag_result = rag_interview.generate_rag_question(
            category=category,
            incident_description_en=incident_description_en,
            prior_questions=prior_q,
            prior_answers_en=prior_a,
            zone_id=zone_id,
            language=language,
            raw_description=raw_description,
        )
        if rag_result is not None:
            q_text, opts, sop_source, is_personalized = rag_result
            return q_text, answered_count, opts, sop_source, is_personalized
        if answered_count >= 4:
            return None, answered_count, [], None, False

    # 2. Static question bank fallback
    raw_list = _QUESTION_BANK.get(category, [])
    if answered_count >= len(raw_list):
        return None, len(raw_list), [], None, False
    item = raw_list[answered_count]
    if isinstance(item, dict):
        q = item.get(language) or item.get("en") or ""
        opts_data = item.get("options", {})
        if isinstance(opts_data, dict):
            opts = opts_data.get(language) or opts_data.get("en") or []
        elif isinstance(opts_data, list):
            opts = opts_data
        else:
            opts = []
        return q, answered_count, opts, None, False
    return str(item), answered_count, [], None, False


def find_english_option(
    category: str,
    question_idx: int,
    answer_text: str,
    incident_description_en: str = "",
    prior_questions: list[str] | None = None,
    prior_answers_en: list[str] | None = None,
    zone_id: str | None = None,
    language: str = "en",
    raw_description: str = "",
) -> str | None:
    """
    If the worker's answer matches a quick-option in ANY language (Tamil, Bengali, Hindi, etc.),
    maps it directly to the corresponding English option string.
    Checks dynamic RAG options first, then falls back to static question bank options.
    """
    target = answer_text.strip().lower()

    # 1. Check dynamic RAG options
    if incident_description_en or raw_description or prior_questions:
        res_native = rag_interview.generate_rag_question(
            category=category,
            incident_description_en=incident_description_en,
            prior_questions=prior_questions or [],
            prior_answers_en=prior_answers_en or [],
            zone_id=zone_id,
            language=language,
            raw_description=raw_description,
        )
        res_en = rag_interview.generate_rag_question(
            category=category,
            incident_description_en=incident_description_en,
            prior_questions=prior_questions or [],
            prior_answers_en=prior_answers_en or [],
            zone_id=zone_id,
            language="en",
            raw_description=raw_description,
        )
        if res_native and res_en:
            opts_native = res_native[1]
            opts_en = res_en[1]
            for i, opt in enumerate(opts_native):
                if opt.strip().lower() == target:
                    if i < len(opts_en):
                        return opts_en[i]
            for i, opt in enumerate(opts_en):
                if opt.strip().lower() == target:
                    return opts_en[i]

    # 2. Check static question bank options
    raw_list = _QUESTION_BANK.get(category, [])
    if question_idx >= len(raw_list):
        return None
    item = raw_list[question_idx]
    if not isinstance(item, dict):
        return None
    opts_data = item.get("options", {})
    if not isinstance(opts_data, dict):
        return None
    en_opts = opts_data.get("en", [])
    for lang, opts_list in opts_data.items():
        if isinstance(opts_list, list):
            for i, opt in enumerate(opts_list):
                if opt.strip().lower() == target:
                    if i < len(en_opts):
                        return en_opts[i]
    return None


def evaluate(category: str, answers: list[str]) -> tuple[float, str]:
    questions = get_questions(category)
    if not questions:
        return 0.0, "needs_verification"

    completeness = len(answers) / len(questions)

    hedge_count = sum(1 for a in answers if any(h in a.lower() for h in _HEDGE_WORDS))
    direct_count = sum(1 for a in answers if any(d in a.lower() for d in _DIRECT_WORDS))

    score = completeness - 0.15 * hedge_count + 0.05 * direct_count
    score = max(0.0, min(1.0, score))

    if score >= 0.7:
        status = "strongly_supported"
    elif score >= 0.4:
        status = "needs_verification"
    else:
        status = "inconsistent_insufficient"

    return round(score, 2), status
