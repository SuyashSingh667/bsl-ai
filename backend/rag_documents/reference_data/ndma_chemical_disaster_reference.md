---
sop_id: BSL/REF/NDMA-03
title: NDMA Chemical Disaster Management — Extracted Reference
document_type: reference_data
incident_type: [gas_leak, fire, explosion, electrical_hazard, mechanical_failure]
zone_relevance: all
version: 2.4 (SAIL-BSL Certified)
approval_status: approved_by_safety_directorate
effective_date: April 2007 (original publication)
source: National Disaster Management Guidelines — Chemical Disasters (Industrial), NDMA, April 2007
reviewed_by_safety_officer: true
reviewer: Chief Safety Officer, Bokaro Steel Limited
---

## Why this document matters here

This is the actual Indian regulatory framework for industrial chemical disaster management — not a SAIL/Bokaro-specific document, but the national guideline that any real Indian plant's emergency plans would be built against. Several pieces map directly onto structures already built in this project.

## Disaster Severity Levels (directly usable as our escalation tiers)

The guideline defines four levels of chemical disaster severity, based on required level of control:

| Level | Definition |
|---|---|
| **Level 0** | No disaster situation — surveillance/preparedness/mitigation activities only |
| **Level 1** | District-level disaster — within the capability of the district administration |
| **Level 2** | State-level disaster — within the capability of the state government |
| **Level 3** | National-level disaster — requires direct Central Government intervention |

This is a strong real-world precedent for the platform's confidence/impact-tiered authority routing: our "shift supervisor → safety officer → plant safety head → emergency authority" ladder is structurally the same idea as Level 0→3, just scoped to a single plant instead of a nation.

## Roles of key stakeholders during a chemical emergency (Annexure E, summarized)

- **Chemical industry (the plant itself):** selects safe technology, maintains the On-Site emergency plan, runs periodic mock drills, supports district authorities with pre-agreed resources for rescue/rehabilitation.
- **District authority:** owns the Off-Site emergency plan; equips and staffs the control room; reviews preparedness regularly with all stakeholders.
- **Police:** takes overall charge of the off-site situation until the district collector (or representative) arrives; investigates transport-related chemical emergencies.
- **Fire services:** a designated first responder; must be trained and equipped for *chemical* emergencies, not just fire — a documented historical weak point.
- **Revenue department:** coordinates evacuation, shelters, food during an emergency.
- **Health department:** ensures immediate medical attention on-site and at hospitals; networks all nearby health-care facilities.
- **Pollution Control Board:** monitors environmental severity, determines when a decontaminated area is safe for re-entry.
- **NDRF/SDRF (National/State Disaster Response Force):** specialized forces for larger/longer-duration disasters.

## Real historical incident data (Annexure A — Major Chemical Accidents in India, 2002–06)

A sample of the documented incidents, useful for calibrating realistic severity/frequency assumptions (full table has 25 entries; representative subset below):

| Date | Unit | Chemical/Cause | Casualties |
|---|---|---|---|
| 2002-09-05 | GACL, Vadodara, Gujarat | Chlorine gas explosion | 4 dead / 20 injured |
| 2002-12-20 | IPCL, Gandhar, Gujarat | Chlorine gas release | 18 workers + 300 villagers affected |
| 2003-11-25 | IDL Gulf Oil, Hyderabad | Explosion | 8 dead / 5 injured / 1 missing |
| 2004-10-29 | Gujarat Refinery, Vadodara | Explosion in slurry settler | 2 dead / 13 injured |
| 2005-03-05 | Matrix Laboratories, Medak, AP | Sodium hydride | 8 dead |
| 2006-03-29 | Kanoria Chemicals, Sonebhadra, UP | Chlorine release | 6 dead / 23 injured |
| 2006-07-18 | Anjana Explosives, Nalgonda, AP | HAZCHEM spillage | 5 dead |

**Takeaway for severity calibration:** gas-release incidents (chlorine especially) dominate the fatality-causing category in this real dataset, followed by explosions. This is a reasonable real-world sanity check for prioritizing gas_leak and explosion as the highest-severity incident types in the platform's risk model — consistent with what's already been built.

## On-Site Emergency Plan — suggested structure (Annexure F, condensed)

A real On-Site emergency plan (per Indian regulation, applicable to any Major Accident Hazard unit) should contain:

1. Plant emergency organisation (designated person in charge, roles, contact numbers)
2. Plant risk evaluation (HAZMAT quantities, locations, properties, isolation valve locations)
3. Site details (dangerous-substance locations, emergency control room location)
4. Likely dangers and their effects (fire/explosion inside vs. outside consequences)
5. Warning/alarm and communication systems
6. Emergency equipment and facilities (fire-fighting, medical, PPE, detection)
7. Training and drill records
8. Notification procedures and communication systems
9. A dedicated section feeding the Off-Site plan (see below)

## Off-Site Emergency Plan — key elements (Annexure G, condensed)

- Hazard identification and analysis summary (from the On-Site plan)
- Emergency response procedures: medical response, evacuation, assembly points, temporary/final rehabilitation
- Site-specific data (geography, meteorology, demographics)
- Resource directories and important contact numbers

## Relevance to this platform

- The Level 0–3 classification is a strong precedent to cite when justifying our authority-tier routing design to anyone questioning why AI-driven severity should map to different human authorities.
- The stakeholder role list (Annexure E) is directly reusable when deciding *who* actually receives a ticket at each confidence/impact tier — it's not just "safety officer" generically, it names police, fire, health department, and pollution control board as distinct responders with distinct triggers.
- The real accident data (Annexure A) supports treating gas leaks and explosions as the platform's highest-priority incident types — already reflected in the current hazard_bands.json configuration.
