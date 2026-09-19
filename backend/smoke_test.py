"""
End-to-end smoke test against a running server (python app/main.py or
uvicorn app.main:app). Exercises the full flow:
1. suspected-incident report -> classification -> verification interview -> finalize -> RAG guidance -> ticket fetch
2. audio reporting flow with entity extraction
3. Hindi flow with native questions, Hindi answer, translation, guidance and audio
4. emergency bypass path
5. ticket update (status and notes)
6. similar incident intelligence and recurring hazard detection
"""

import subprocess
import sys
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8000"


def suspected_flow():
    r = requests.post(
        f"{BASE}/incidents",
        json={
            "report_type": "suspected",
            "incident_description": "I smell gas near the gas holder station, not sure how strong it is",
            "zone_id": "GHS",
            "employee_id": "emp-101",
        },
    )
    r.raise_for_status()
    ticket = r.json()
    print("created ticket:", ticket["id"], "category:", ticket["predicted_category"], "confidence:", ticket["category_confidence"])
    assert ticket["predicted_category"] == "gas_leak"
    ticket_id = ticket["id"]

    while True:
        nq = requests.get(f"{BASE}/verification/{ticket_id}/next-question").json()
        if nq["done"]:
            break
        print("Q:", nq["question"])
        answer = "yes, I saw gas escaping and it is still leaking" if "see" in nq["question"].lower() else "not sure"
        resp = requests.post(f"{BASE}/verification/{ticket_id}/answer", json={"answer_text": answer})
        resp.raise_for_status()

    ticket = requests.get(f"{BASE}/tickets/{ticket_id}").json()
    print("verification_status:", ticket["verification_status"], "score:", ticket["verification_score"])
    print("routing_tier:", ticket["routing_tier"], "risk_score:", ticket["risk_score"])
    print("impact_assessment:", ticket["impact_assessment"])
    assert ticket["routing_tier"] is not None

    guided = requests.post(f"{BASE}/guidance/{ticket_id}").json()
    print("guidance_sources:", guided["guidance_sources"])
    assert guided["guidance_sources"], "expected at least one cited source"

    print("SUSPECTED FLOW OK\n")
    return ticket_id


def audio_flow():
    audio_path = Path("/tmp/bsl_test_report.aiff")
    if not audio_path.exists():
        try:
            subprocess.run(
                ["say", "-o", str(audio_path), "There is a gas leak near the gas holder station. Two people are dizzy."],
                check=True,
            )
        except Exception as e:
            print("Skipping audio_flow because say failed:", e)
            return

    with open(audio_path, "rb") as f:
        r = requests.post(
            f"{BASE}/incidents/audio",
            data={"report_type": "suspected", "employee_id": "emp-303"},
            files={"file": ("test_report.aiff", f, "audio/aiff")},
        )
    r.raise_for_status()
    ticket = r.json()
    print("audio ticket transcript:", ticket["incident_description"])
    print("audio ticket language:", ticket["language"], ticket["language_confidence"])
    print("audio ticket category:", ticket["predicted_category"])
    print("audio ticket extracted_entities:", ticket["extracted_entities"])
    assert ticket["predicted_category"] == "gas_leak"
    assert ticket["zone_id"] == "GHS", "entity extraction should have inferred the zone from the transcript"
    assert ticket["extracted_entities"]["people_affected"] == 2
    print("AUDIO FLOW OK\n")


def hindi_flow():
    r = requests.post(
        f"{BASE}/incidents",
        json={
            "report_type": "suspected",
            "incident_description": "मुझे गैस होल्डर स्टेशन के पास गैस की गंध आ रही है",
            "language": "hi",
            "zone_id": "GHS",
            "employee_id": "emp-404",
        },
    )
    r.raise_for_status()
    ticket = r.json()
    print("hindi ticket native:", ticket["incident_description"])
    print("hindi ticket translated (en):", ticket["incident_description_en"])
    print("hindi ticket category:", ticket["predicted_category"], "confidence:", ticket["category_confidence"])
    assert ticket["incident_description_en"] != ticket["incident_description"], "translation should have changed the text"
    assert ticket["predicted_category"] == "gas_leak", "classification should work off the translated English text"
    ticket_id = ticket["id"]

    nq = requests.get(f"{BASE}/verification/{ticket_id}/next-question").json()
    print("hindi Q (asked in Hindi):", nq["question"])
    # Verify the question is in Hindi (contains Devanagari script)
    assert any("\u0900" <= c <= "\u097f" for c in nq["question"]), "question should be in Hindi"

    resp = requests.post(
        f"{BASE}/verification/{ticket_id}/answer",
        json={"answer_text": "हाँ, मैंने गैस को बाहर निकलते देखा"},  # "Yes, I saw gas escaping"
    )
    resp.raise_for_status()
    ticket = resp.json()
    print("hindi answer native:", ticket["verification_answers"][-1])
    print("hindi answer translated (en):", ticket["verification_answers_en"][-1])
    assert ticket["verification_answers_en"][-1] != ticket["verification_answers"][-1]

    guided = requests.post(f"{BASE}/guidance/{ticket_id}").json()
    print("hindi guidance_text_native:\n", guided["guidance_text_native"][:100] + "...")
    print("hindi guidance_audio_path:", guided["guidance_audio_path"])
    assert guided["guidance_text_native"], "expected translated guidance text"
    assert guided["guidance_audio_path"]

    print("HINDI FLOW OK\n")
    return ticket_id


def emergency_flow():
    r = requests.post(
        f"{BASE}/incidents",
        json={
            "report_type": "emergency",
            "incident_description": "Active fire at the coke oven battery, people trapped",
            "zone_id": "COB",
            "employee_id": "emp-202",
        },
    )
    r.raise_for_status()
    ticket = r.json()
    print("emergency ticket routing_tier:", ticket["routing_tier"], "status:", ticket["status"])
    assert ticket["routing_tier"] == "emergency_authority"
    assert ticket["status"] == "escalated"
    print("EMERGENCY FLOW OK\n")
    return ticket["id"]


def ticket_update_and_intelligence_flow(ticket_id):
    # Test PATCH /tickets/{id}
    r = requests.patch(
        f"{BASE}/tickets/{ticket_id}",
        json={"status": "in_progress", "resolution_notes": "Safety team dispatched to investigate."},
    )
    r.raise_for_status()
    updated = r.json()
    assert updated["status"] == "in_progress"
    assert updated["resolution_notes"] == "Safety team dispatched to investigate."
    print("PATCH /tickets/{id} OK: status is now", updated["status"])

    # Test GET /tickets/{id}/similar
    sim_res = requests.get(f"{BASE}/tickets/{ticket_id}/similar")
    sim_res.raise_for_status()
    sim_data = sim_res.json()
    print("Similar incidents found:", len(sim_data["similar_tickets"]))
    print("Recurring hazard alert:", sim_data["recurring_hazard"])
    print("Recurrence note:", sim_data["recurrence_note"])
    print("SIMILARITY & INTELLIGENCE FLOW OK\n")


if __name__ == "__main__":
    try:
        t1 = suspected_flow()
        audio_flow()
        t2 = hindi_flow()
        t3 = emergency_flow()
        ticket_update_and_intelligence_flow(t1)
        print("ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as exc:
        print("SMOKE TEST FAILED:", exc)
        sys.exit(1)
