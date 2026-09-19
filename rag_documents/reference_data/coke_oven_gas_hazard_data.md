---
title: Coke Oven Gas — Hazard Reference Data
document_type: reference_data
incident_type: [gas_leak, fire, explosion]
zone_relevance: [COB, GHS]
version: 1.0
approval_status: real-world reference (industry SDS + general chemistry) — not a BSL-specific document
effective_date: N/A
source: composition of pipeline residue from United States Steel Corporation SDS (USS IHS 13960, Rev. 10/2020); raw-gas composition figures are well-established general process chemistry, not from a fetched SDS — flagged below
---

## Important sourcing note

Two different things are covered here, and they should not be conflated:

1. **Coke Oven Gas Pipeline Residue** — a solid/sludge tar deposit that precipitates inside gas piping. Real SDS data below.
2. **Raw coke oven gas itself** (the flammable/toxic gas that would actually leak) — its general composition is well-documented process chemistry (not pulled from a specific fetched SDS in this session): roughly 50–60% hydrogen, 25–30% methane, 5–8% carbon monoxide, 5–10% nitrogen, plus trace tar vapors, benzene, hydrogen sulfide, and hydrogen cyanide. This should be verified against a raw-gas SDS before being treated as authoritative.

## Pipeline Residue — Composition (% by weight, real SDS data)

| Component | CAS Number | % Weight |
|---|---|---|
| Sulfur | 7704-34-9 | 40–55 |
| Iron | 7439-89-6 | 5–15 |
| Ammonia | 7664-41-7 | 1–5 |
| Cyanide | 57-12-5 | 0.1–4 |
| Crystalline Silica (as Quartz) | 14808-60-7 | 0–1 |
| Benzene | 71-43-2 | 0–0.5 |

## Hazard Classification (pipeline residue)

- **Toxic if swallowed; causes severe skin burns and eye damage.**
- **Carcinogenicity (Category 1A)** — contains benzene and crystalline silica, both confirmed human carcinogens (IARC-1).
- **Germ cell mutagenicity, reproductive toxicity** — benzene-driven.
- **STOT (repeated exposure)** — damage to blood/blood-forming system and lungs/CNS from benzene and crystalline silica.
- **Combustible dust hazard** if ≥5% by weight has particle size <500 µm.

## Key component hazards (relevant to a gas-leak/exposure scenario, not just the residue)

- **Cyanide:** fatal if swallowed, absorbed through skin, or inhaled. Causes headache, dizziness, arrhythmia, loss of consciousness, coma, death.
- **Ammonia:** corrosive; produces burns; injury ranges from mild irritation to severe burns and life-threatening pulmonary edema depending on concentration/duration.
- **Benzene:** CNS depression, respiratory irritation, drowsiness; human carcinogen; chronic exposure linked to leukemia via bone marrow effects.
- **Crystalline silica:** causes silicosis (progressive, irreversible lung scarring) on chronic exposure.

## Exposure Limits (selected components)

| Component | OSHA PEL | ACGIH TLV | IDLH |
|---|---|---|---|
| Ammonia | 50 ppm | 25 ppm | 300 ppm |
| Benzene | 1.0 ppm (STEL 5.0) | 0.5 ppm skin (STEL 2.5) | 500 ppm, carcinogen |
| Crystalline Silica | 0.05 mg/m³ | 0.025 mg/m³ | 50 mg/m³ (as quartz) |

## First-Aid

- **Inhalation:** remove to fresh air; if unconscious or symptomatic, call poison control/doctor immediately.
- **Skin/eye contact:** remove contaminated clothing immediately, rinse with water/shower for several minutes.
- **Ingestion:** call poison control immediately; do NOT induce vomiting.

## Relevance to this platform

Grounds the "toxic_gas" hazard tag on the Coke Oven Battery (COB) zone. The benzene/cyanide/ammonia content is the real basis for why a coke-oven-area incident should be treated as a serious inhalation and long-term carcinogen exposure risk, not just a generic "gas smell" report — this should inform verification-question priority (e.g. asking about direct exposure duration matters more here than for less toxic gas sources).
