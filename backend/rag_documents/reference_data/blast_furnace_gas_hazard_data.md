---
title: Blast Furnace Gas — Hazard Reference Data
document_type: reference_data
incident_type: [gas_leak, explosion]
zone_relevance: [BF1, BF2, GHS, SIN]
version: 1.0
approval_status: real-world reference (industry SDS) — not a BSL-specific document
effective_date: N/A
source: United States Steel Corporation, Blast Furnace Gas Safety Data Sheet, USS IHS 82495, Rev. 09/2020
---

## Composition (% by volume)

| Component | CAS Number | % Volume |
|---|---|---|
| Nitrogen | 7727-37-9 | 47–60 |
| Carbon Monoxide | 630-08-0 | 19–25 |
| Carbon Dioxide | 124-38-9 | 17–25 |
| Hydrogen | 1333-74-0 | 2–9.6 |

## Hazard Classification

- **Extremely flammable gas.** Flammability range: 27%–75% (lower/upper explosive limit).
- **Simple asphyxiant** — displaces oxygen, can cause rapid suffocation at high concentration.
- **Acute toxicity (inhalation)** — harmful if inhaled, due to carbon monoxide content.
- **Chronic (STOT repeated exposure)** — prolonged/repeated exposure causes damage to the heart (carboxyhemoglobin formation reduces oxygen-carrying capacity of blood).
- Vapor density (air = 1): 1.02 — roughly neutral buoyancy, does not reliably rise or sink; can accumulate in enclosed/low-ventilation areas.
- Odor: may have a slight sulfur odor, but **this must not be relied on as a warning of its presence** — the gas can be present at hazardous concentration without noticeable smell.

## Occupational Exposure Limits — Carbon Monoxide (the controlling component)

| Standard | Limit |
|---|---|
| OSHA PEL (8-hr TWA) | 50 ppm |
| ACGIH TLV (8-hr TWA) | 25 ppm |
| NIOSH REL (10-hr TWA) | 35 ppm |
| IDLH | 1,200 ppm |

No person should work in or enter an area where CO content exceeds 50 ppm without a gas mask/appropriate respiratory protection.

## First-Aid

- **Inhalation:** move to fresh air immediately. If not breathing, give artificial respiration; if breathing is difficult, give oxygen. Seek medical attention.
- Acute high-concentration exposure acts as a simple asphyxiant (oxygen displacement).
- Chronic/repeated exposure: may cause heart problems (cardiac hypertrophy documented in inhalation studies).

## Fire-Fighting

- **Do not extinguish a leaking-gas fire unless the leak itself can be stopped safely** — an unstopped leak that continues to burn is safer than one that reignites explosively after being extinguished.
- Eliminate ignition sources if it is safe to do so.
- Once the leak is stopped, extinguish with foam, CO₂, dry powder, or water fog. Do **not** use a solid water stream — it scatters and spreads the fire.
- Firefighters require self-contained breathing apparatus (SCBA) and full protective/thermal clothing.

## Accidental Release

- If leakage cannot be stopped: **evacuate the area.**
- Before re-entry, the area must be tested (gas concentration confirmed safe) by qualified personnel.
- Eliminate all ignition sources in the immediate area (no smoking, sparks, flares, open flame).

## Relevance to this platform

This is the real hazard basis for the platform's Gas Holder Station (GHS) and Blast Furnace (BF1/BF2) zones — the "toxic_gas" and "explosion" hazard tags on those zones in `zones.json` are grounded in this data, not invented. The 50 ppm / 1,200 ppm CO thresholds are a defensible reference point for calibrating future severity/confidence scoring specific to gas-leak incidents in these zones.
