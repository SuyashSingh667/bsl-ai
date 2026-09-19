"""
Phase 4: Adaptive Verification State and Slot Tracking Engine.
Maintains explicit interview state across turns:
- Facts extracted so far (slots filled)
- Missing priority slots
- Questions already asked
- Next question selection via hazard information needs & grounded SOP citations
"""

from __future__ import annotations

import re
from typing import Any
from app.services import hazard_checklists, hybrid_retrieval


class InterviewState:
    def __init__(
        self,
        hazard_type: str,
        zone_id: str | None = None,
        language: str = "en",
        initial_report: str = "",
    ):
        self.hazard_type = hazard_type
        self.zone_id = zone_id
        self.language = language
        self.initial_report = initial_report
        self.filled_slots: dict[str, str] = {}
        self.asked_questions: list[str] = []
        self.asked_slots: set[str] = set()
        self.turn_count: int = 0

        # Extract initial slots directly from initial report
        self._extract_slots_from_text(initial_report)

    def _extract_slots_from_text(self, text: str) -> None:
        """Rule & regex slot extractor for factual extraction from worker utterance."""
        t_low = text.lower()

        # 1. Victims / Casualties
        if any(w in t_low for w in ["unconscious", "behosh", "बेहोश", "collapsed", "fainted"]):
            self.filled_slots["victims_condition"] = "unconscious"
        elif any(w in t_low for w in ["dizzy", "nausea", "headache", "vomit", "chakkar"]):
            self.filled_slots["victims_condition"] = "symptomatic_dizziness"
        elif any(w in t_low for w in ["burn", "jal gaya", "blister", "scald"]):
            self.filled_slots["victims_condition"] = "burn_injuries"
        elif any(w in t_low for w in ["trapped", "fasa", "pinned", "entangled"]):
            self.filled_slots["victims_condition"] = "trapped_casualty"
        elif any(w in t_low for w in ["no one hurt", "safe", "nobody injured", "koi ghayal nahi"]):
            self.filled_slots["victims_condition"] = "no_injuries"

        # 2. Isolation / Containment
        if any(w in t_low for w in ["isolated", "shut", "closed", "tripped", "bandh", "loto", "locked"]):
            self.filled_slots["isolation_status"] = "isolated_safely"
            self.filled_slots["equipment_e_stop_loto"] = "stopped_loto"
            self.filled_slots["circuit_deenergized_loto"] = "deenergized"
        elif any(w in t_low for w in ["cannot access", "cannot reach", "inaccessible", "too hot", "live"]):
            self.filled_slots["isolation_status"] = "inaccessible_cannot_reach"

        # 3. Evacuation
        if any(w in t_low for w in ["evacuated", "cleared", "assembly point", "surakshit dur", "chale gaye"]):
            self.filled_slots["evacuation_status"] = "evacuated_safe"
            self.filled_slots["personnel_clear_path"] = "cleared_path"
            self.filled_slots["load_drop_zone_clearance"] = "drop_zone_cleared"

        # 4. Fire / Extinguishment
        if any(w in t_low for w in ["extinguished", "bujha diya", "put out", "controlled", "under control"]):
            self.filled_slots["spread_barrier_isolation"] = "extinguished_controlled"

        # 5. Materials / Hazmat
        if any(w in t_low for w in ["cable", "panel", "wire", "switchgear"]):
            self.filled_slots["material_involved"] = "electrical"
        elif any(w in t_low for w in ["oil", "transformer oil", "diesel", "fuel"]):
            self.filled_slots["material_involved"] = "oil_fuel"
        elif any(w in t_low for w in ["acid", "hcl", "sulfuric", "hydrochloric"]):
            self.filled_slots["chemical_identity_hazmat"] = "acid"
        elif any(w in t_low for w in ["caustic", "naoh", "alkali"]):
            self.filled_slots["chemical_identity_hazmat"] = "caustic_soda"

        # 6. Water on Molten Slag / Metal
        if any(w in t_low for w in ["dry", "sukha", "no water"]):
            self.filled_slots["water_exclusion_status"] = "dry_safe"
        elif any(w in t_low for w in ["water dripping", "water near", "rain", "wet"]):
            self.filled_slots["water_exclusion_status"] = "water_contact_warning"

    def _deduce_slot_from_question(self, question: str) -> str | None:
        """Deduces the target slot from question text across registry and keywords."""
        q_norm = question.strip().lower()
        if not q_norm:
            return None

        # 1. Match against default_q across all registry items
        for items in hazard_checklists.INFORMATION_NEEDS_REGISTRY.values():
            for item in items:
                for lang_q in item.get("default_q", {}).values():
                    l_norm = lang_q.strip().lower()
                    if l_norm == q_norm or l_norm in q_norm or q_norm in l_norm:
                        return item["slot"]

        # 2. Heuristic keywords from question
        if any(k in q_norm for k in ["isolation valve", "gas supply", "safely closed", "valve", "आइसोलेशन", "वाल्व"]):
            return "isolation_status"
        if any(k in q_norm for k in ["unconscious", "dizziness", "trapped", "behoosh", "hurt", "injured", "बेहोश", "चक्कर", "फंसा"]):
            return "victims_condition"
        if any(k in q_norm for k in ["evacuated", "upwind", "assembly point", "हवा की विपरीत", "निकासी"]):
            return "evacuation_status"
        if any(k in q_norm for k in ["flames", "hot work", "engine", "ignition", "खुली आग", "वेल्डिंग"]):
            return "ignition_source"
        if any(k in q_norm for k in ["power", "de-energized", "breaker", "tripped", "बिजली", "ब्रेकर"]):
            return "electrical_power_cut"
        if any(k in q_norm for k in ["material", "burning", "cables", "transformer oil", "conveyor", "केबल"]):
            return "material_involved"
        if any(k in q_norm for k in ["water", "slag", "molten", "moisture", "पानी"]):
            return "water_exclusion_status"
        return None

    def record_turn(self, question: str, answer: str, slot_asked: str | None = None) -> None:
        """Records completed turn and extracts newly answered slots."""
        self.turn_count += 1
        q_clean = question.strip()
        self.asked_questions.append(q_clean)

        deduced_slot = slot_asked or self._deduce_slot_from_question(q_clean)
        if deduced_slot:
            self.asked_slots.add(deduced_slot)
            if answer and answer.strip() and deduced_slot not in self.filled_slots:
                self.filled_slots[deduced_slot] = answer.strip()

        self._extract_slots_from_text(answer)

    def get_missing_priority_slots(self) -> list[dict[str, Any]]:
        """Returns ordered missing priority slots for this hazard type."""
        checklist = hazard_checklists.INFORMATION_NEEDS_REGISTRY.get(self.hazard_type, [])
        missing = []
        for item in checklist:
            slot_name = item["slot"]
            if slot_name not in self.filled_slots and slot_name not in self.asked_slots:
                missing.append(item)
        # Sort by priority ascending (1 is top priority)
        return sorted(missing, key=lambda x: x["priority"])


def generate_next_best_question(
    state: InterviewState,
    max_turns: int = 4,
) -> tuple[str | None, list[str], str | None, bool, str | None]:
    """
    Chooses the next best question by:
    1. Identifying highest-priority missing slot.
    2. Grounding in retrieved SOP passage when available.
    3. Ensuring question is <= 25 words, single-sentence, non-leading, zero blame.
    4. Guarding against repetition of answered slots and already-asked questions.

    Returns:
    (question_text, options, sop_source, is_personalized, target_slot)
    """
    if state.turn_count >= max_turns:
        return None, [], None, False, None

    missing_slots = state.get_missing_priority_slots()
    if not missing_slots:
        # All critical slots filled
        return None, [], None, False, None

    # Find the first missing slot whose default question text has not been asked yet
    chosen_item = None
    q_text = None
    opts: list[str] = []
    lang = state.language or "en"

    for item in missing_slots:
        slot_name = item["slot"]
        if slot_name in state.asked_slots:
            continue

        q_dict = item.get("default_q", {})
        cand_q = q_dict.get(lang) or q_dict.get("en")
        if not cand_q:
            continue

        cand_norm = cand_q.strip().lower()
        already_asked = any(
            cand_norm == asked.strip().lower()
            or cand_norm in asked.strip().lower()
            or asked.strip().lower() in cand_norm
            for asked in state.asked_questions
        )
        if already_asked:
            state.asked_slots.add(slot_name)
            continue

        chosen_item = item
        q_text = cand_q
        opts_dict = item.get("options", {})
        opts = opts_dict.get(lang) or opts_dict.get("en") or []
        break

    if not chosen_item or not q_text:
        return None, [], None, False, None

    target_slot = chosen_item["slot"]

    # 1. Perform structured RAG retrieval
    missing_slot_names = [item["slot"] for item in missing_slots]
    query = hybrid_retrieval.build_structured_query(
        hazard_type=state.hazard_type,
        zone_id=state.zone_id,
        initial_report=state.initial_report,
        prior_answers=list(state.filled_slots.values()),
        missing_slots=missing_slot_names,
    )

    chunks, is_confident = hybrid_retrieval.retrieve_grounded_context(
        hazard_type=state.hazard_type,
        structured_query=query,
        top_k=2,
    )

    top_chunk = chunks[0] if chunks else None
    sop_title = top_chunk["doc_title"] if top_chunk else "Standard Plant Safety Procedure"

    # 2. Quality Guard: Ensure <= 25 words and single question
    words = q_text.strip().split()
    if len(words) > 25:
        q_text = " ".join(words[:24]) + "?"

    return q_text, opts, sop_title, True, target_slot
