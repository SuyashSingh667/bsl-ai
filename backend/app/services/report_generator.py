"""
Structured Incident Safety Report Generator.
Synthesizes verified interview facts, spatial impact consequence models,
and approved BSL SOP procedures into an actionable, auditable safety report.

V2 Improvements:
- Chronological incident narrative combining initial report & verified facts
- Complete Verification Interview Timeline (showing Q&A with worker)
- Contextual Situation-Specific Risk Assessment
- Actionable Immediate Containment & Mitigation Directives
- Environmental & Atmospheric Safety Warnings
- Designated Dispatch Recipients
"""

from typing import Any
from app.services import rag, routing


def generate_incident_report(
    ticket_id: str,
    category: str,
    category_confidence: float | None,
    zone_id: str | None,
    initial_statement: str,
    initial_statement_en: str,
    findings: dict[str, Any],
    impact: dict[str, Any] | None,
    routing_tier: str | None,
    risk_score: float | None,
    photo_url: str | None = None,
    report_type: str = "suspected",
    verification_questions: list[str] | None = None,
    verification_answers: list[str] | None = None,
    verification_answers_en: list[str] | None = None,
) -> dict[str, Any]:
    # 1. Retrieve applicable BSL SOP chunks for procedural grounding
    query = f"{category} {zone_id or ''} {' '.join(findings.get('confirmed_equipment', []))} {' '.join(findings.get('reported_symptoms', []))}"
    chunks = rag.retrieve(query, incident_type=category, top_k=3)

    # 2. Determine verification badge & threat assessment
    ev_score = findings.get("total_evidence_score", 0.5)
    is_active = findings.get("is_hazard_active")
    has_symptoms = bool(findings.get("reported_symptoms"))
    obs_mode = findings.get("observation_mode", "unspecified")

    if is_active is True or has_symptoms or (risk_score and risk_score >= 0.7):
        threat_level = "CRITICAL / HIGH PRIORITY"
    elif is_active is False:
        threat_level = "MODERATE / CONTAINED"
    else:
        threat_level = "ELEVATED / PENDING ON-SITE VERIFICATION"

    # 3. Format findings summary
    obs_display = {
        "visual_confirmed": "Confirmed (Direct Physical Observation)",
        "both_seen_and_smelled": "Confirmed (Direct Visual & Olfactory Contact)",
        "odor_only": "Suspected (Odor / Vapor Detected; No Visual Breach Identified)",
        "uncertain": "Unconfirmed / Inconclusive",
        "unspecified": "Unspecified in Report",
    }.get(obs_mode, obs_mode)

    active_display = {
        True: "Active / Ongoing (Hazard Actively Releasing)",
        False: "Inactive / Contained (Releasing Stopped)",
        None: "Uncertain (Requires Physical Gauge Inspection)",
    }[is_active]

    equipment_display = ", ".join(findings.get("confirmed_equipment", [])) or "Specific component unconfirmed"
    symptoms_display = ", ".join(findings.get("reported_symptoms", [])) or "None reported at time of interview"
    exposed_display = f"{findings.get('people_exposed_count')} worker(s)" if findings.get("people_exposed_count") is not None else "Unspecified"

    # 4. Generate SOP Procedural Actions from retrieved chunks
    sop_directives = []
    sources = []
    for c in chunks:
        sources.append({"title": c["doc_title"], "section": c["section"], "path": c["doc_path"]})
        meaningful_lines = [l.strip() for l in c["text"].splitlines() if l.strip() and not l.startswith("#")]
        sop_directives.append({
            "sop_title": c["doc_title"],
            "section": c["section"],
            "instructions": meaningful_lines[:5],
        })

    # 5. Build Dynamic Situation-Specific Risk Narrative
    category_title = category.replace("_", " ").title()
    situation_narrative_parts = [
        f"A **{report_type.upper()}** incident categorized as **{category_title}** was reported at Zone `{zone_id or 'General Facility'}`."
    ]
    if initial_statement_en:
        situation_narrative_parts.append(f"Initial field notice indicated: *\"{initial_statement_en}\"*.")
    if is_active is True:
        situation_narrative_parts.append("Verification establishes that the hazard is **actively spreading or uncontained**, presenting an immediate life-safety concern.")
    elif is_active is False:
        situation_narrative_parts.append("Interview verification indicates the immediate release or breach has been **isolated or suppressed**, transitioning focus to post-containment monitoring.")
    if findings.get("confirmed_equipment"):
        situation_narrative_parts.append(f"Physical equipment involved includes: **{', '.join(findings['confirmed_equipment'])}**.")
    if findings.get("people_exposed_count"):
        situation_narrative_parts.append(f"Estimated **{findings['people_exposed_count']} personnel** are within the immediate exposure envelope.")
    if has_symptoms:
        situation_narrative_parts.append(f"Active health symptoms reported: **{', '.join(findings['reported_symptoms'])}**; priority emergency medical triage required.")
    situation_narrative = " ".join(situation_narrative_parts)

    # 6. Build Situation-Tailored Dispatcher Checklist
    checklist = [
        f"Establish 360-degree perimeter cordon around Zone '{zone_id or 'Incident Origin'}' immediately.",
        f"Deploy incident command team equipped with calibrated safety PPE suited for {category_title}.",
    ]
    if findings.get("confirmed_equipment"):
        checklist.append(f"Execute physical Lockout/Tagout (LOTO) and valve/switch isolation on: {equipment_display}.")
    else:
        checklist.append("Conduct visual inspection to identify and isolate root supply/electrical feed.")

    if is_active is True:
        checklist.append("URGENT: Initiate audible siren alert and direct all non-essential personnel upwind / to safe muster points.")
    if has_symptoms:
        checklist.append("Deploy on-site ambulance with supplemental oxygen; establish triage station outside hot zone.")
    if category in ["gas_leak", "chemical_spill", "confined_space_emergency"]:
        checklist.append("Continuous multi-gas atmospheric testing (CO, O2, LEL, H2S) prior to entry authorization.")
    if impact and impact.get("civilian_exposure_alert"):
        checklist.append("CRITICAL: Alert Perimeter Security & Township Emergency Coordinator for boundary drift mitigation.")
    checklist.append("Secure clearance confirmation from Plant Safety Officer prior to declaring all-clear.")

    # 7. Designated Dispatch Recipients
    recipients = routing.get_dispatch_recipients(
        category=category,
        zone_id=zone_id,
        routing_tier=routing_tier,
        risk_score=risk_score,
        report_type=report_type,
    )

    # 8. Compose Enhanced Markdown Report
    md_lines = [
        f"# BSL SAFETY INCIDENT VERIFICATION REPORT",
        f"**Ticket ID:** `{ticket_id}` | **Category:** {category_title} | **Threat Level:** {threat_level}",
        f"**Incident Location:** Zone {zone_id or 'General Plant'} | **Calculated Risk Score:** {risk_score or 'N/A'}",
        f"**Initial Worker Statement:** \"{initial_statement_en or initial_statement}\"",
        "",
        "## 1. Executive Incident Summary & Risk Narrative",
        situation_narrative,
        "",
        "## 2. Verified Field Findings & Evidence Matrix",
        f"- **Visual Confirmation Status:** {obs_display}",
        f"- **Hazard Release State:** {active_display}",
        f"- **Identified Equipment / Component:** {equipment_display}",
        f"- **Exposed Personnel Count:** {exposed_display}",
        f"- **Reported Medical Symptoms:** {symptoms_display}",
        f"- **Evidence Reliability Confidence:** {int(ev_score * 100)}%",
        "",
    ]

    sec_idx = 3

    # Interview Timeline (if Q&A provided)
    q_list = verification_questions or []
    a_list = verification_answers_en or verification_answers or []
    if q_list and a_list:
        md_lines.extend([
            f"## {sec_idx}. Verification Interview Timeline",
            "Below is the chronological sequence of safety verification questions and worker field responses:",
            "",
        ])
        for idx, (q, a) in enumerate(zip(q_list, a_list), start=1):
            md_lines.append(f"- **Turn {idx} Question:** *\"{q}\"*")
            md_lines.append(f"  - **Worker Response:** **\"{a}\"**")
        md_lines.append("")
        sec_idx += 1

    # Photographic / Video Field Evidence
    if photo_url:
        is_video = any(photo_url.lower().endswith(ext) for ext in [".mp4", ".webm", ".mov", ".mkv", ".avi"])
        if is_video:
            md_lines.extend([
                f"## {sec_idx}. Photographic & Video Field Evidence",
                f'<video controls width="100%" style="max-height: 400px; border-radius: 8px;" src="{photo_url}"></video>',
                f"*Verified on-site video recording captured for Zone {zone_id or 'Plant Facility'}.*",
                "",
            ])
        else:
            md_lines.extend([
                f"## {sec_idx}. Photographic Field Evidence",
                f"![Incident Scene Photographic Proof]({photo_url})",
                f"*Verified photographic evidence captured on site for Zone {zone_id or 'Plant Facility'}.*",
                "",
            ])
        sec_idx += 1

    # Spatial Consequence & Workforce Exposure
    if impact and impact.get("applicable"):
        md_lines.extend([
            f"## {sec_idx}. Spatial Consequence & Workforce Exposure",
            f"- **Affected Plant Zones:** {len(impact.get('affected_zones', []))} zone(s) in hazard envelope",
            f"- **Modeled Workforce at Risk:** {impact.get('estimated_persons_at_risk_range', [0, 0])[0]} to {impact.get('estimated_persons_at_risk_range', [0, 0])[1]} persons",
            f"- **Civilian Perimeter Alert:** {'YES (Boundary Warning Active)' if impact.get('civilian_exposure_alert') else 'No (Contained within plant bounds)'}",
            "",
        ])
        sec_idx += 1

    # Approved Standard Operating Procedures
    md_lines.extend([
        f"## {sec_idx}. Approved Standard Operating Procedures (SOP)",
    ])
    sec_idx += 1
    for dir_item in sop_directives:
        md_lines.append(f"### {dir_item['section']} ({dir_item['sop_title']})")
        for step in dir_item["instructions"]:
            md_lines.append(f"- {step}")
        md_lines.append("")

    # Field Response Checklist
    md_lines.extend([
        f"## {sec_idx}. Field Response & Dispatcher Checklist",
    ])
    sec_idx += 1
    for item in checklist:
        md_lines.append(f"- [ ] {item}")
    md_lines.append("")

    # Designated Dispatch Recipients
    md_lines.extend([
        f"## {sec_idx}. Designated Report Recipients & Emergency Dispatches",
        "The incident verification dossier and emergency command notifications have been dispatched to:",
    ])
    for r in recipients:
        md_lines.append(f"- **{r['department']}** ({r['contact']}) — *{r['role']}* `[{r['priority']}]` — **{r['status']}**")

    report_markdown = "\n".join(md_lines)

    return {
        "ticket_id": ticket_id,
        "threat_level": threat_level,
        "category_title": category_title,
        "photo_url": photo_url,
        "verified_summary": {
            "observation_mode": obs_display,
            "active_state": active_display,
            "equipment": equipment_display,
            "exposed_personnel": exposed_display,
            "symptoms": symptoms_display,
            "evidence_score": ev_score,
        },
        "situation_narrative": situation_narrative,
        "sop_directives": sop_directives,
        "sources": sources,
        "checklist": checklist,
        "recipients": recipients,
        "report_markdown": report_markdown,
    }
