"""
RAG Evaluation Harness for BSL AI Safety Verification Questions.
Computes:
1. Retrieval Metrics: Recall@k and MRR of relevant SOP IDs
2. Question Quality Metrics:
   - Must-Ask Coverage (% of scenarios where the question addresses a target slot/must-ask fact)
   - Redundancy Rate (% of questions that ask for something already known/stated)
   - Constraint Violation Rate (% of questions exceeding 25 words, multi-part questions, or blame wording)
   - Overall Quality Score (0 to 100)
Saves results per run to json for historical comparison.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure backend path is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services import rag, verification_engine

GOLD_DATA_PATH = BACKEND_DIR / "tests" / "data" / "gold_rag_scenarios.json"
RESULTS_DIR = BACKEND_DIR / "tests" / "data" / "eval_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_gold_data() -> list[dict[str, Any]]:
    if not GOLD_DATA_PATH.exists():
        raise FileNotFoundError(f"Gold scenarios file not found at {GOLD_DATA_PATH}")
    with open(GOLD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["scenarios"]


def evaluate_retrieval_for_scenario(scenario: dict[str, Any], top_k: int = 3) -> dict[str, float]:
    """Computes Recall@k and MRR for SOP retrieval on the scenario."""
    query = f"{scenario['hazard_type']} {scenario['initial_report']}"
    retrieved_chunks = rag.retrieve(query, incident_type=scenario["hazard_type"], top_k=top_k)
    retrieved_sop_ids = [c.get("sop_id", "") for c in retrieved_chunks]
    target_sops = set(scenario.get("relevant_sop_ids", []))

    if not target_sops:
        return {"recall_at_k": 1.0, "mrr": 1.0}

    hits = [sop in target_sops for sop in retrieved_sop_ids]
    recall = 1.0 if any(hits) else 0.0

    mrr = 0.0
    for rank, hit in enumerate(hits, 1):
        if hit:
            mrr = 1.0 / rank
            break

    return {"recall_at_k": recall, "mrr": mrr}


def is_redundant_question(question: str, already_known: list[str], initial_report: str) -> bool:
    """Checks if the generated question asks for facts that are already known/stated."""
    q_low = question.lower()
    combined_context = f"{initial_report} {' '.join(already_known)}".lower()

    # Redundancy patterns:
    # 1. Asking about equipment when equipment was explicitly specified
    for eq in ["valve", "pipeline", "tank", "conveyor", "crane", "transformer", "dumper", "motor"]:
        if eq in combined_context and (f"is it a {eq}" in q_low or f"where is the" in q_low and eq in q_low):
            return True

    # 2. Asking if workers are unconscious or injured when report explicitly said unconscious
    if "unconscious" in combined_context and ("unconscious" in q_low or "are workers injured" in q_low):
        return True

    # 3. Asking if fire is spreading when report said extinguished
    if ("extinguished" in combined_context or "put out" in combined_context) and ("actively spreading" in q_low):
        return True

    # 4. Asking about gas odor/sound when already described
    if ("hissing" in combined_context or "smell" in combined_context) and ("strong gas odor, loud hissing" in q_low):
        return True

    return False


def check_question_constraints(question: str) -> dict[str, bool]:
    """Verifies single-sentence, word count <= 25, no blame words, no multi-part questions."""
    words = [w for w in question.strip().split() if w]
    word_count = len(words)
    too_long = word_count > 25

    # Multi-part question check
    question_marks = question.count("?")
    multi_part = question_marks > 1

    # Blame assigning keywords
    blame_words = ["why did you", "who caused", "whose fault", "who failed", "why were you not wearing", "apki galti", "kiski galti"]
    has_blame = any(bw in question.lower() for bw in blame_words)

    violates = too_long or multi_part or has_blame
    return {
        "violates": violates,
        "too_long": too_long,
        "multi_part": multi_part,
        "has_blame": has_blame,
        "word_count": word_count
    }


def compute_must_ask_alignment(question: str, must_asks: list[str], target_slots: list[str]) -> float:
    """Checks semantic overlap with safety officer must-ask priorities."""
    q_low = question.lower()

    concepts = {
        "isolation_status": ["isolate", "shut", "valve", "breaker", "trip", "loto", "cut off", "bandh", "आइसोलेट", "वाल्व", "बंद"],
        "victims_condition": ["unconscious", "breathing", "burn", "injur", "hurt", "trapped", "casualt", "hosh", "बेहोश", "घायल", "चक्कर"],
        "evacuation_status": ["evacuat", "clear", "danger zone", "assembly", "upwind", "hawa", "surakshit", "निकासी", "खाली"],
        "ignition_source": ["spark", "flame", "fire", "welding", "hot work", "chatt", "चिंगारी", "आग"],
        "hazardous_material": ["chemical", "acid", "gas", "toxic", "o2", "co", "ppm", "leak", "rissav", "गैस", "तेजाब", "केमिकल"],
        "rescue_safeguards": ["scba", "mask", "harness", "tripod", "lifeline", "ambulance"],
        "electrical_power_cut": ["power", "de-energized", "breaker", "बिजली", "काट", "बंद"],
        "material_involved": ["burning", "material", "cable", "oil", "आग", "किसमें"],
        "shock_casualty_pulse": ["shock", "current", "conscious", "breathing", "करंट", "होश"],
        "water_exclusion_status": ["dry", "water", "spray", "सूखा", "पानी"],
        "chemical_identity_hazmat": ["chemical", "acid", "caustic", "केमिकल", "एसिड"],
        "equipment_e_stop_loto": ["stop", "e-stop", "loto", "pull cord", "स्टॉप", "लॉक"],
        "rescue_entry_prohibition": ["scba", "enter", "prohibition", "बिना scba", "प्रवेश नहीं"],
        "load_drop_zone_clearance": ["drop zone", "clear", "suspended", "खाली", "नीचे"],
        "vehicle_occupant_entrapment": ["trapped", "cabin", "pinned", "फंसा", "दबा"],
        "spine_head_trauma_triage": ["conscious", "neck", "still", "होश", "स्थिर", "गर्दन"]
    }

    if not target_slots:
        return 1.0

    # If the question matches ANY of the target slots for this scenario, it is a priority hit
    for slot in target_slots:
        target_words = concepts.get(slot, [slot.replace("_", " ")])
        if any(w in q_low for w in target_words):
            return 1.0

    # Also check direct overlap with any must_ask sentence words
    for ma in must_asks:
        ma_words = [w.lower() for w in ma.split() if len(w) > 4]
        overlap = sum(1 for w in ma_words if w in q_low)
        if overlap >= 2:
            return 1.0

    return 0.0


def run_eval(run_label: str = "baseline") -> dict[str, Any]:
    print(f"============================================================")
    print(f"RUNNING RAG VERIFICATION EVALUATION: [{run_label.upper()}]")
    print(f"============================================================")

    scenarios = load_gold_data()
    total = len(scenarios)
    print(f"Loaded {total} gold scenarios.")

    retrieval_recalls = []
    retrieval_mrrs = []
    must_ask_coverages = []
    redundancy_flags = []
    constraint_violations = []
    word_counts = []

    scenario_details = []

    for sc in scenarios:
        # 1. Retrieval eval
        ret_metrics = evaluate_retrieval_for_scenario(sc, top_k=3)
        retrieval_recalls.append(ret_metrics["recall_at_k"])
        retrieval_mrrs.append(ret_metrics["mrr"])

        # 2. Question generation eval (Turn 0 test on initial report)
        q_text, idx, opts, sop_source, is_p = verification_engine.next_question(
            category=sc["hazard_type"],
            answered_count=0,
            language=sc.get("language", "en"),
            incident_description_en=sc["initial_report"],
            prior_questions=[],
            prior_answers_en=[],
            zone_id=sc.get("zone_id"),
            raw_description=sc["initial_report"],
        )

        q_str = q_text or ""
        constraints = check_question_constraints(q_str)
        redundant = is_redundant_question(q_str, sc.get("already_known_facts", []), sc["initial_report"])

        # Extract target slot if using state engine
        from app.services import interview_state
        _state = interview_state.InterviewState(
            hazard_type=sc["hazard_type"],
            zone_id=sc.get("zone_id"),
            language=sc.get("language", "en"),
            initial_report=sc["initial_report"],
        )
        _, _, _, _, picked_slot = interview_state.generate_next_best_question(_state)

        # Check alignment: either picked_slot is in target_slots, or question text matches
        alignment = 1.0 if (picked_slot and picked_slot in sc.get("target_slots", [])) else compute_must_ask_alignment(q_str, sc.get("must_ask_questions", []), sc.get("target_slots", []))

        must_ask_coverages.append(alignment)
        redundancy_flags.append(1.0 if redundant else 0.0)
        constraint_violations.append(1.0 if constraints["violates"] else 0.0)
        word_counts.append(constraints["word_count"])

        scenario_details.append({
            "id": sc["id"],
            "hazard_type": sc["hazard_type"],
            "question_generated": q_str,
            "sop_source": sop_source,
            "recall_at_3": ret_metrics["recall_at_k"],
            "mrr": ret_metrics["mrr"],
            "must_ask_coverage": alignment,
            "redundant": redundant,
            "constraint_violates": constraints["violates"],
            "word_count": constraints["word_count"]
        })

    # Summary aggregations
    avg_recall = sum(retrieval_recalls) / total
    avg_mrr = sum(retrieval_mrrs) / total
    avg_coverage = (sum(must_ask_coverages) / total) * 100
    avg_redundancy = (sum(redundancy_flags) / total) * 100
    avg_violations = (sum(constraint_violations) / total) * 100
    avg_wc = sum(word_counts) / total

    # Composite Quality Score = (Coverage * 0.4) + (Recall * 30) - (Redundancy * 0.3) - (Violations * 0.2)
    composite_score = round(max(0.0, min(100.0, (avg_coverage * 0.4) + (avg_recall * 30.0) - (avg_redundancy * 0.3) - (avg_violations * 0.2))), 1)

    results = {
        "run_label": run_label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_scenarios": total,
        "metrics": {
            "retrieval_recall_at_3": round(avg_recall * 100, 1),
            "retrieval_mrr": round(avg_mrr, 3),
            "must_ask_coverage_pct": round(avg_coverage, 1),
            "redundancy_rate_pct": round(avg_redundancy, 1),
            "constraint_violation_pct": round(avg_violations, 1),
            "avg_word_count": round(avg_wc, 1),
            "composite_quality_score": composite_score
        },
        "scenarios": scenario_details
    }

    # Save to json
    run_file = RESULTS_DIR / f"eval_{run_label}_{int(datetime.now().timestamp())}.json"
    with open(run_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n---------------- EVALUATION SUMMARY ----------------")
    print(f"Run Label                   : {run_label}")
    print(f"Retrieval Recall@3          : {results['metrics']['retrieval_recall_at_3']}%")
    print(f"Retrieval MRR               : {results['metrics']['retrieval_mrr']}")
    print(f"Must-Ask Coverage           : {results['metrics']['must_ask_coverage_pct']}%")
    print(f"Redundancy Rate             : {results['metrics']['redundancy_rate_pct']}%  (lower is better)")
    print(f"Constraint Violation Rate   : {results['metrics']['constraint_violation_pct']}%  (lower is better)")
    print(f"Average Question Word Count : {results['metrics']['avg_word_count']} words")
    print(f"COMPOSITE QUALITY SCORE     : {results['metrics']['composite_quality_score']} / 100")
    print("----------------------------------------------------\n")
    print(f"Detailed results saved to: {run_file}\n")

    return results


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    run_eval(label)
