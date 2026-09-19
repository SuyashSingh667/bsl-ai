import { useEffect, useState } from "react";
import { audioUrl, generateGuidance, getPrecautions, getTicket, photoUrl } from "../api";

const TIER_LABELS = {
  emergency_authority: "Emergency Authority",
  plant_safety_officer: "Plant Safety Officer",
  shift_supervisor: "Shift Supervisor",
  safety_team_queue: "Safety Team Queue",
};

export default function TicketResult({ ticketId, isEmergency }) {
  const [ticket, setTicket] = useState(null);
  const [guidance, setGuidance] = useState(null);
  const [precautions, setPrecautions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [checkedItems, setCheckedItems] = useState({});
  const [checkedPrecautionItems, setCheckedPrecautionItems] = useState({});

  useEffect(() => {
    async function load() {
      try {
        const t = await getTicket(ticketId);
        setTicket(t);
        if (t.precautionary_measures) {
          setPrecautions(t.precautionary_measures);
        } else {
          try {
            const p = await getPrecautions(ticketId);
            setPrecautions(p);
          } catch (pErr) {
            console.warn("Could not load precautions:", pErr);
          }
        }
        // If not already generated in verification finalize, invoke guidance
        if (!isEmergency && !t.safety_report && !t.guidance_text) {
          const g = await generateGuidance(ticketId);
          setGuidance(g);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [ticketId, isEmergency]);

  function toggleChecklist(index) {
    setCheckedItems((prev) => ({ ...prev, [index]: !prev[index] }));
  }

  function togglePrecautionCheck(id) {
    setCheckedPrecautionItems((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  if (loading) {
    return (
      <div className="screen">
        <p>Finalizing incident verification & synthesizing safety report…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="screen">
        <p className="error-text">{error}</p>
      </div>
    );
  }

  const report = ticket.safety_report;
  const verified = report?.verified_summary;
  const impact = ticket.impact_assessment;

  return (
    <div className="screen ticket-result-screen">
      {/* 4-Step Progress Stepper - All Completed */}
      <div className="flow-stepper-bar">
        <div className="step-node step-completed">
          <span className="step-num">✓</span>
          <span className="step-title">1. Incident Logged</span>
        </div>
        <div className="step-connector completed"></div>
        <div className="step-node step-completed">
          <span className="step-num">✓</span>
          <span className="step-title">2. Visual Proof</span>
        </div>
        <div className="step-connector completed"></div>
        <div className="step-node step-completed">
          <span className="step-num">✓</span>
          <span className="step-title">3. Safety Questions</span>
        </div>
        <div className="step-connector completed"></div>
        <div className="step-node step-completed">
          <span className="step-num">✓</span>
          <span className="step-title">4. Precautions & Report</span>
        </div>
      </div>

      <div className="result-header-block">
        <h1 className="screen-title">{isEmergency ? "🚨 Emergency Escalated" : "📋 Incident Safety Report"}</h1>
        <p className="subtitle">Official Bokaro Steel Plant Safety Log & SOP Compliance Record</p>
      </div>

      {/* Header Status Bar */}
      <div className="result-card">
        <div className="result-row">
          <span className="result-label">Ticket Reference</span>
          <span className="ticket-id-cell">{ticket.id}</span>
        </div>
        <div className="result-row">
          <span className="result-label">Assigned Authority</span>
          <span className="result-tier">{TIER_LABELS[ticket.routing_tier] || ticket.routing_tier}</span>
        </div>
        <div className="result-row">
          <span className="result-label">Threat Assessment</span>
          <span className="threat-pill">{report?.threat_level || "ELEVATED PRIORITY"}</span>
        </div>
        {!isEmergency && (
          <div className="result-row">
            <span className="result-label">Verification Status</span>
            <span>
              {ticket.verification_status?.replaceAll("_", " ").toUpperCase()} (
              {Math.round((ticket.verification_score || 0) * 100)}% evidence reliability)
            </span>
          </div>
        )}
      </div>

      {/* Audio Briefing Player */}
      {ticket.guidance_audio_path && (
        <div className="audio-briefing-card">
          <span className="audio-label">🔊 Safety Voice Briefing ({ticket.language?.toUpperCase()}):</span>
          <audio controls autoPlay src={audioUrl(ticket.guidance_audio_path)} />
          {ticket.guidance_text_native && (
            <p className="audio-transcript-native">"{ticket.guidance_text_native}"</p>
          )}
        </div>
      )}

      {/* Precautionary Safety Measures Grounded in BSL SOP */}
      {precautions && (
        <div className="report-card precautionary-result-card">
          <div className="precaution-header-banner">
            <div className="precaution-header-title">
              <h3>🛡️ Personal Safety Precautions (Worker Protection)</h3>
              <span className="sop-source-tag">Grounded in: {precautions.sop_source} ({precautions.sop_code})</span>
            </div>
            {precautions.audio_path && (
              <div className="precaution-audio-replay">
                <span className="replay-label">🔊 Listen to Precautions ({ticket.language?.toUpperCase()}):</span>
                <audio controls src={audioUrl(precautions.audio_path)} />
              </div>
            )}
          </div>

          <p className="subtitle prompt-quote">
            "{precautions.prompt_question_native || precautions.prompt_question}"
          </p>

          <div className="precaution-result-grid">
            {precautions.measures?.map((m) => {
              const isChecked = !!checkedPrecautionItems[m.id];
              return (
                <div key={m.id} className={isChecked ? "measure-card measure-card-checked" : "measure-card"}>
                  <div className="measure-card-header">
                    <span className="measure-icon">{m.icon}</span>
                    <div className="measure-titles">
                      <h4 className="measure-native-title">{m.title_native}</h4>
                      {m.title_native !== m.title && (
                        <span className="measure-en-title">{m.title}</span>
                      )}
                    </div>
                  </div>
                  <p className="measure-desc-native">{m.text_native}</p>
                  {m.text_native !== m.text && (
                    <p className="measure-desc-en">"{m.text}"</p>
                  )}
                  <div className="measure-checkbox-row">
                    <label className="measure-checkbox-label">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => togglePrecautionCheck(m.id)}
                      />
                      <span className="checkbox-text">
                        {m.checklist_label_native || m.checklist_label}
                      </span>
                    </label>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Visual Incident Field Evidence (Photo or Video) */}
      {(ticket.photo_url || ticket.media_url || ticket.photo_proof_path) && (() => {
        const evidenceSrc = ticket.media_url || ticket.photo_url || photoUrl(ticket.photo_proof_path);
        const isVideo = ticket.media_type === "video" || (evidenceSrc && /\.(mp4|webm|mov|mkv|avi)(\?.*)?$/i.test(evidenceSrc));
        return (
          <div className={`report-card photo-evidence-card ${isVideo ? "video-evidence-card" : ""}`}>
            <div className="photo-card-header">
              <h3>{isVideo ? "🎥 Visual Field Evidence (Video Recording)" : "📸 Photographic Field Evidence"}</h3>
              <span className="badge-verified-evidence">{isVideo ? "✓ VERIFIED VIDEO PROOF" : "✓ VERIFIED SCENE PROOF"}</span>
            </div>
            <p className="subtitle">
              {isVideo
                ? `Video recording captured on site in Zone ${ticket.zone_id || "Plant Area"} and attached to the incident dossier:`
                : `Visual proof captured on site in Zone ${ticket.zone_id || "Plant Area"} and attached to the incident dossier:`}
            </p>
            <div className="photo-display-wrap">
              {isVideo ? (
                <video
                  controls
                  playsInline
                  src={evidenceSrc}
                  className="incident-evidence-video"
                />
              ) : (
                <>
                  <img
                    src={evidenceSrc}
                    alt="Incident Scene Evidence"
                    className="incident-evidence-image"
                    onClick={() => window.open(evidenceSrc, "_blank")}
                  />
                  <span className="photo-caption">Click image to view full resolution in new tab</span>
                </>
              )}
            </div>
          </div>
        );
      })()}

      {/* Section 1: Verified Evidence Findings Matrix */}
      {verified && (
        <div className="report-card">
          <h3>1. Verified Evidence & Fact Identification</h3>
          <p className="subtitle">
            Structured analysis extracted from worker answers by the verification model:
          </p>
          <div className="findings-table-wrap">
            <table className="findings-table">
              <tbody>
                <tr>
                  <td className="finding-label">Visual Confirmation</td>
                  <td className="finding-value">{verified.observation_mode}</td>
                </tr>
                <tr>
                  <td className="finding-label">Hazard Activity State</td>
                  <td className="finding-value">{verified.active_state}</td>
                </tr>
                <tr>
                  <td className="finding-label">Source Equipment</td>
                  <td className="finding-value">
                    <strong>{verified.equipment}</strong>
                  </td>
                </tr>
                <tr>
                  <td className="finding-label">Personnel Exposed</td>
                  <td className="finding-value">{verified.exposed_personnel}</td>
                </tr>
                <tr>
                  <td className="finding-label">Reported Symptoms</td>
                  <td className="finding-value">{verified.symptoms}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Section 2: Spatial Consequence & Workforce Exposure */}
      {impact?.applicable && (
        <div className="report-card">
          <h3>2. Spatial Consequence & Dispersion</h3>
          <div className="impact-summary-row">
            <span>
              <strong>{impact.affected_zones.length}</strong> zone(s) inside hazard envelope
            </span>
            <span>
              <strong>
                {impact.estimated_persons_at_risk_range[0]}–{impact.estimated_persons_at_risk_range[1]}
              </strong>{" "}
              workforce modeled at risk
            </span>
          </div>
          {impact.civilian_exposure_alert && (
            <p className="civilian-alert">
              ⚠ <strong>CIVILIAN WARNING:</strong> Modeled hazard radius reaches plant perimeter!
            </p>
          )}
          <table className="sub-table">
            <thead>
              <tr>
                <th>Zone Name</th>
                <th>Code</th>
                <th>Hazard Band</th>
                <th>Distance</th>
                <th>Personnel at Risk</th>
              </tr>
            </thead>
            <tbody>
              {impact.affected_zones.map((az) => (
                <tr key={az.zone_id}>
                  <td>{az.name}</td>
                  <td>{az.zone_id}</td>
                  <td>
                    <span className={`band-pill band-${az.band}`}>{az.band}</span>
                  </td>
                  <td>{az.distance_m}m</td>
                  <td>
                    {az.estimated_persons_at_risk_range
                      ? `${az.estimated_persons_at_risk_range[0]}–${az.estimated_persons_at_risk_range[1]}`
                      : "Unmodeled"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Section 3: Grounded Standard Operating Procedures */}
      {report?.sop_directives?.length > 0 && (
        <div className="report-card">
          <h3>3. Grounded SOP Action Directives</h3>
          {report.sop_directives.map((directive, i) => (
            <div key={i} className="sop-directive-box">
              <h4>
                {directive.section}{" "}
                <span className="sop-source-tag">from {directive.sop_title}</span>
              </h4>
              <ul>
                {directive.instructions.map((inst, j) => (
                  <li key={j}>{inst}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {/* Section 4: Field Dispatcher & Response Checklist */}
      {report?.checklist?.length > 0 && (
        <div className="report-card checklist-card">
          <h3>4. Response & Field Inspection Checklist</h3>
          <p className="subtitle">
            Safety Officers and Emergency Dispatchers: check off items as completed:
          </p>
          <div className="checklist-items">
            {report.checklist.map((item, idx) => (
              <label key={idx} className={`checklist-label ${checkedItems[idx] ? "item-done" : ""}`}>
                <input
                  type="checkbox"
                  checked={!!checkedItems[idx]}
                  onChange={() => toggleChecklist(idx)}
                />
                <span>{item}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Section 5: Designated Report Recipients & Dispatch Log */}
      {report?.recipients?.length > 0 && (
        <div className="report-card recipients-dispatch-card">
          <div className="recipients-header">
            <h3>🚨 Designated Report Recipients & Transmission Log</h3>
            <span className="badge-transmitted">✓ DOSSIER TRANSMITTED</span>
          </div>
          <p className="subtitle">
            The formal safety incident dossier and emergency alerts have been transmitted to the following authorized Bokaro Steel units:
          </p>
          <div className="recipients-grid">
            {report.recipients.map((rec, idx) => (
              <div key={idx} className="recipient-item-card">
                <div className="recipient-top-row">
                  <span className={`recipient-priority-badge ${rec.priority.includes("CRITICAL") ? "priority-crit" : ""}`}>
                    {rec.priority}
                  </span>
                  <span className="recipient-status-tag">✓ {rec.status}</span>
                </div>
                <h4 className="recipient-dept">{rec.department}</h4>
                <p className="recipient-role"><strong>Role:</strong> {rec.role}</p>
                <div className="recipient-contact-row">
                  <span className="contact-icon">📞</span>
                  <span className="contact-text">{rec.contact}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
