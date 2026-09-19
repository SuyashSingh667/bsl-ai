# BSL AI Safety Platform — First Plant Pilot Plan

**Version:** 1.0 — Phase 8  
**Status:** Draft for review by safety officers and plant management  
**Target Plant:** Bokaro Steel Limited (BSL), Bokaro Steel City, Jharkhand  
**Pilot Duration:** 2–4 weeks  

> **Important:** This is a pilot to learn what works in your specific plant context —  
> not a performance evaluation of workers. All data collected is used to improve the  
> system, not to assess or discipline anyone.

---

## 1. Pilot Objectives

| # | Objective | Success Metric |
|---|-----------|---------------|
| 1 | Reduce time from hazard observation to emergency team dispatch | Time-to-first-dispatch ≤ 3 minutes for critical incidents |
| 2 | Increase near-miss reporting frequency | Reports per 100 workers per month ≥ 5 by week 4 |
| 3 | Close the loop: workers see what happened to their reports | ≥ 80% of reporters receive at least one lifecycle update |
| 4 | Validate offline resilience on the plant floor | ≥ 90% of reports submitted in low-connectivity areas complete successfully |
| 5 | Identify gaps in SOP coverage and AI accuracy | Document unhandled hazard types and low-confidence transcriptions |

---

## 2. Scope

### In Scope
- **Zones:** BF1, BF2, GHS (Blast Furnace complex + Gas Handling) as primary pilot zones  
  (highest hazard class, established shift structure, ~400 workers per shift)
- **Shift coverage:** All three shifts (A/B/C), 6 AM – 6 AM cycle
- **Report types:** Both `emergency` and `suspected` (near-miss) reports
- **Roles:** Workers (voice/text report), Supervisors (triage + assign), Safety Officer (oversight), Control Room (dispatch + ack)
- **Devices:** Shared kiosk at zone entrance + personal Android phones (optional)

### Out of Scope for Pilot
- Full-plant rollout across all 27 zones
- WhatsApp/SMS dispatch integration (will be tested in parallel, not as primary path)
- Vision / photo analysis (available but not required from workers during pilot)

---

## 3. Pre-Pilot Checklist

### Technical (IT/Safety Team)
- [ ] Server deployed on-prem (Docker Compose) or on plant intranet
- [ ] `BSL_DEMO_MODE=0` confirmed in production `.env`
- [ ] Plant config JSON updated: emergency team phone numbers, zone centroids, SOP documents uploaded
- [ ] Kiosk Android tablet set up at BF1 entry, WLAN connected, app installed
- [ ] Cloudflare / VPN tunnel or local IP accessible from plant floor devices
- [ ] Backup: offline queue tested — report survives 10 minutes of network loss and syncs on reconnect
- [ ] SOS fallback: verify `BSL_SOS_SMS_FALLBACK_NUMBER` points to control room
- [ ] TTS pre-cached Hindi/English prompts verified playable without internet
- [ ] Admin account created for Safety Officer (role: `safety_officer`)
- [ ] Demo seed run and cleared: `POST /admin/demo/seed` then `DELETE /admin/demo/clear`

### Organizational (Plant Management / Safety Dept)
- [ ] Safety Officer briefed on dashboard, dispatch ack workflow, and escalation rules
- [ ] Shift supervisors briefed on kiosk login (badge ID / PIN) and proxy reporting
- [ ] Union / worker representative informed: no individual surveillance, anonymous reporting option available
- [ ] "What happens to my report" poster printed in Hindi/English and posted at kiosk station
- [ ] Emergency response teams have control room number ready for SMS fallback
- [ ] Pilot scope communicated to all BF1/BF2/GHS workers in morning briefing

---

## 4. Week-by-Week Plan

### Week 1 — Calibration (Supervised)
**Goal:** Confirm technical setup works. All reports reviewed by safety officer before dispatch.

| Day | Activity |
|-----|----------|
| Day 1 | Safety officer and shift supervisor walkthrough with demo mode. Submit 3 test reports from kiosk. |
| Day 2–3 | Workers observe safety officer submitting sample reports. Q&A session. |
| Day 4–5 | Workers invited to submit near-miss reports. Safety officer reviews all before dispatch. |
| Day 6–7 | Fix any connectivity / transcription / language issues found. Collect feedback form #1. |

**What to observe:**
- Can workers complete a report in < 2 minutes without assistance?
- Are Hindi transcriptions accurate for local plant terminology (tuyere, LOTO, BF gas)?
- Does the kiosk work reliably at shift start (peak usage)?

### Week 2 — Live Near-Miss Reporting
**Goal:** Workers submit near-miss reports independently. Emergency path tested with simulated incident.

| Activity | Detail |
|----------|--------|
| Near-miss reports go live | Supervisors review within 1 hour of submission |
| Simulated emergency drill | One planned BF gas leak drill — test full dispatch + ACK + on-site lifecycle |
| Anonymous reporting enabled | Workers informed they can report without their name attached |
| SOP coverage audit | Safety officer reviews AI-generated guidance against actual plant SOPs |

**Metrics to track this week:**
- Total reports submitted
- % with audio vs. text
- % successfully transcribed (check `language_confidence` > 0.6)
- Time-to-ack on drill dispatch

### Week 3 — Full Pilot
**Goal:** All incident types handled through system without safety officer pre-review.

| Activity | Detail |
|----------|--------|
| Auto-dispatch enabled for emergencies | Human review still required for suspected incidents before corrective action |
| Safety officer monitors trend dashboard daily | Check for repeat hazards by zone/shift |
| Worker feedback session (mid-pilot) | Group session, 15 min, in Hindi — collect pain points |
| Escalation SLA tested | Verify auto-escalation fires correctly when dispatch unacknowledged > 60s |

### Week 4 — Review and Retrospective
**Goal:** Capture learnings and decide on full plant expansion.

| Activity | Detail |
|----------|--------|
| Download operational metrics | `GET /analytics/operational-metrics?window_days=28` |
| Export all dossiers for closed incidents | PDF export for 5 sample incidents |
| Worker feedback form #2 | Individual written form (anonymous option available) |
| Safety officer retrospective | What incidents would have been missed without the system? |
| Pilot sign-off meeting | Management + Safety Dept + IT — decision to expand or iterate |

---

## 5. Success Metrics

All metrics are read from `GET /analytics/operational-metrics` at end of pilot.

| Metric | Target | How Measured |
|--------|--------|--------------|
| Time-to-first-dispatch | ≤ 180 seconds median (emergency) | `avg_time_to_first_dispatch_s` |
| Time-to-acknowledge | ≤ 90 seconds median | `avg_time_to_acknowledge_s` |
| Near-miss reports / 100 workers / month | ≥ 5 by week 4 | `reports_per_100_workers_per_month` |
| Near-miss closure time | ≤ 72 hours median | `avg_near_miss_closure_time_h` |
| Transcription confidence | ≥ 0.70 average | `avg_transcription_confidence` |
| Offline completion rate | ≥ 90% | `pct_reports_completed_offline` (if tested) |
| False dispatch rate | ≤ 10% | `false_dispatch_rate` |
| Worker feedback sentiment | ≥ 3.5 / 5.0 | Paper feedback form aggregated manually |

> **Note:** These targets are indicative starting points for discussion with your safety team.  
> Adjust them based on your current baseline (if you have paper incident register data).  
> No artificial targets — if data shows a different realistic baseline, update this document.

---

## 6. Worker Feedback Form

### Form A — After First Use (Week 1, Kiosk)

*(Hindi version will be printed on kiosk; this is the English reference copy)*

1. Did you manage to submit your report without help?  
   ☐ Yes, easily  ☐ Yes, with some difficulty  ☐ No, needed help

2. Was the Hindi/English voice recognition accurate?  
   ☐ Yes, it understood me  ☐ Mostly yes  ☐ No, it missed important words

3. Did you feel comfortable reporting? (no fear of being blamed)  
   ☐ Yes, fully comfortable  ☐ Somewhat  ☐ No

4. How long did it take to submit your report?  
   ☐ Under 2 minutes  ☐ 2–5 minutes  ☐ More than 5 minutes

5. What was the most confusing part? *(write in)*: ___________

---

### Form B — End of Pilot (Week 4)

1. Did you receive an update about what happened to your report?  
   ☐ Yes, got a notification  ☐ Supervisor told me  ☐ Never heard back

2. Did any hazard get fixed because of a report through this system?  
   ☐ Yes  ☐ Not sure  ☐ No

3. Would you recommend this system to workers in other departments?  
   ☐ Definitely yes  ☐ Probably yes  ☐ Unsure  ☐ No

4. Rating overall: ⭐ ⭐ ⭐ ⭐ ⭐  (circle rating out of 5)

5. What would make you use this more often? *(write in)*: ___________

---

### Form C — Safety Officer Retrospective

1. How many incidents in this period do you estimate would NOT have been reported through paper channels?

2. Were there hazard categories the AI did not recognize or classify correctly?

3. Were any SOP citations wrong, unhelpful, or missing?

4. Was the dispatch ACK SLA (60 seconds) appropriate for your plant floor?

5. What would you change before expanding to the full plant?

---

## 7. On-Site Observation Checklist (for pilot coordinator)

### Day 1 Walk-Through
- [ ] Can worker reach kiosk within 2 minutes of any incident in BF1?
- [ ] Is audio quality acceptable near machinery noise? (test with and without headset)
- [ ] Does the "what happens to my report" poster answer workers' questions?
- [ ] Can the control room dashboard be viewed clearly on their existing monitor?
- [ ] Is there a fallback if kiosk is occupied? (phone app, supervisor proxy)

### Daily During Pilot
- [ ] Check `GET /analytics/operational-metrics` each morning — any metric degrading?
- [ ] Review any ticket with `flagged_for_human_review = true` — what triggered it?
- [ ] Check for escalations: any dispatch unacknowledged > 60s?
- [ ] Note any new plant-specific terminology that wasn't recognized by ASR

### End of Week 1
- [ ] Export 3 sample reports as PDF dossiers and review with safety officer
- [ ] Confirm all audit log entries are intact (`GET /admin/audit-logs/verify`)
- [ ] Check transcription confidence histogram — are low-confidence (<0.6) reports identifiable?

---

## 8. Degradation and Fallback Reference

**Warning:** The following functions degrade when offline or when external services are unavailable.  
Workers must know the manual fallback at all times.

| Function | Offline Behavior | Manual Fallback |
|----------|-----------------|-----------------|
| Voice transcription | Queued, synced when online | Worker types report text |
| AI hazard classification | "unclassified — human review required" | Safety officer classifies manually |
| SOP guidance | Last cached SOPs shown | Safety officer consults physical SOP binder |
| Emergency dispatch | Sends to outbox, retries every 30s | Worker calls control room directly: ext. 2800 |
| TTS audio prompts | Pre-cached Hindi/English prompts play locally | Worker reads on-screen text |
| Dashboard / reporting | No updates until connectivity restored | Supervisor reviews paper log |

---

## 9. Privacy and Data Governance Commitments

1. **No individual worker surveillance** — metrics are shift/zone/team level, never individual rankings.
2. **Anonymous near-miss reports** — worker name is never stored; only zone and shift.
3. **Data stays on-prem** — all incident data remains on plant intranet. No cloud upload unless explicitly configured.
4. **Right to see your report** — workers can track their own report using the anonymous tracking code on the kiosk receipt.
5. **Audit log immutability** — all dispatch and access events are SHA-256 chained. Nothing can be deleted silently.
6. **No AI auto-dismissal** — the system escalates; only humans can close a report.

---

## 10. Go / No-Go Decision Points

At the end of Week 2 and Week 4, the following decisions should be made with data:

| Decision | Criteria to Proceed | Criteria to Pause |
|----------|--------------------|--------------------|
| Continue to Week 3 | ≥ 10 reports submitted, 0 technical failures blocking emergency dispatch | Any emergency dispatch failure; connectivity < 80% |
| Expand to full plant | All week 4 metrics at ≥ 70% of target; positive safety officer sign-off | < 5 reports/100 workers; false alarm rate > 20%; negative worker feedback |
| Expand to SMS/WhatsApp dispatch | Control room confirms dispatch process; compliance team approved | IT network firewall blocks outbound; carrier integration not complete |

---

*Document maintained by: BSL AI Platform Team*  
*Next review: After Week 4 retrospective*
