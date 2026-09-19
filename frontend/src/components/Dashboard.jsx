import { useEffect, useState } from "react";
import { audioUrl, getSimilarIncidents, getTickets, updateTicket, photoUrl } from "../api";

const TIER_LABELS = {
  emergency_authority: "Emergency Authority",
  plant_safety_officer: "Plant Safety Officer",
  shift_supervisor: "Shift Supervisor",
  safety_team_queue: "Safety Team Queue",
};

const LANGUAGE_NAMES = {
  en: "English",
  hi: "हिन्दी (Hindi)",
  bn: "বাংলা (Bengali)",
  ta: "தமிழ் (Tamil)",
  te: "తెలుగు (Telugu)",
  mr: "मराठी (Marathi)",
  gu: "ગુજરાતી (Gujarati)",
  kn: "ಕನ್ನಡ (Kannada)",
  ml: "മലയാളം (Malayalam)",
  pa: "ਪੰਜਾਬੀ (Punjabi)",
  or: "ଓଡ଼ିଆ (Odia)",
};

export default function Dashboard() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterTier, setFilterTier] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [similarData, setSimilarData] = useState(null);
  const [updating, setUpdating] = useState(false);
  const [editStatus, setEditStatus] = useState("");
  const [editTier, setEditTier] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  async function loadTickets() {
    setLoading(true);
    setError(null);
    try {
      const list = await getTickets({ routingTier: filterTier, status: filterStatus });
      setTickets(list);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
  }, [filterTier, filterStatus]);

  async function handleSelectTicket(t) {
    setSelectedTicket(t);
    setEditStatus(t.status || "open");
    setEditTier(t.routing_tier || "safety_team_queue");
    setEditNotes(t.resolution_notes || "");
    setSaveSuccess(false);
    setSimilarData(null);
    try {
      const sim = await getSimilarIncidents(t.id);
      setSimilarData(sim);
    } catch {
      // similar endpoint non-critical
    }
  }

  async function handleSaveUpdates(e) {
    e.preventDefault();
    if (!selectedTicket) return;
    setUpdating(true);
    setSaveSuccess(false);
    try {
      const updated = await updateTicket(selectedTicket.id, {
        status: editStatus,
        routing_tier: editTier,
        resolution_notes: editNotes,
      });
      setSelectedTicket(updated);
      setSaveSuccess(true);
      // update ticket in list
      setTickets((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      alert("Failed to save updates: " + err.message);
    } finally {
      setUpdating(false);
    }
  }

  const filteredTickets = tickets.filter((t) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.id.toLowerCase().includes(q) ||
      (t.zone_id && t.zone_id.toLowerCase().includes(q)) ||
      (t.predicted_category && t.predicted_category.toLowerCase().includes(q)) ||
      (t.incident_description && t.incident_description.toLowerCase().includes(q)) ||
      (t.incident_description_en && t.incident_description_en.toLowerCase().includes(q))
    );
  });

  const emergencyCount = tickets.filter(
    (t) => t.report_type === "emergency" || t.routing_tier === "emergency_authority"
  ).length;
  const highRiskCount = tickets.filter((t) => (t.risk_score || 0) >= 0.7).length;
  const inProgressCount = tickets.filter((t) => t.status === "in_progress").length;
  const openCount = tickets.filter((t) => t.status === "open").length;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2>Safety Intelligence Command Center</h2>
          <p className="subtitle">Real-time incident triage, spatial verification & decision support</p>
        </div>
        <button className="refresh-btn" onClick={loadTickets} disabled={loading}>
          🔄 {loading ? "Refreshing..." : "Refresh Queue"}
        </button>
      </div>

      {/* Metrics Row */}
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-value">{tickets.length}</div>
          <div className="metric-label">Total Logged</div>
        </div>
        <div className="metric-card emergency">
          <div className="metric-value">{emergencyCount}</div>
          <div className="metric-label">Emergency / Escalated</div>
        </div>
        <div className="metric-card high-risk">
          <div className="metric-value">{highRiskCount}</div>
          <div className="metric-label">High Risk (≥0.70)</div>
        </div>
        <div className="metric-card active">
          <div className="metric-value">{openCount + inProgressCount}</div>
          <div className="metric-label">Open / In Progress</div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="filters-bar">
        <div className="filter-group">
          <label>Status:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="escalated">Escalated</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Routing Tier:</label>
          <select value={filterTier} onChange={(e) => setFilterTier(e.target.value)}>
            <option value="all">All Tiers</option>
            <option value="emergency_authority">Emergency Authority</option>
            <option value="plant_safety_officer">Plant Safety Officer</option>
            <option value="shift_supervisor">Shift Supervisor</option>
            <option value="safety_team_queue">Safety Team Queue</option>
          </select>
        </div>

        <div className="filter-group search-group">
          <input
            type="text"
            placeholder="Search ID, Zone, Category, Text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}

      {/* Tickets Table */}
      <div className="table-container">
        <table className="tickets-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>Type</th>
              <th>Category</th>
              <th>Zone</th>
              <th>Risk Score</th>
              <th>Routing Tier</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredTickets.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ textAlign: "center", padding: "2rem", color: "#888" }}>
                  {loading ? "Loading incidents..." : "No incidents found matching current filters."}
                </td>
              </tr>
            ) : (
              filteredTickets.map((t) => {
                const isEmerg = t.report_type === "emergency" || t.routing_tier === "emergency_authority";
                const risk = t.risk_score != null ? t.risk_score : 0;
                let riskClass = "risk-low";
                if (risk >= 0.7) riskClass = "risk-high";
                else if (risk >= 0.4) riskClass = "risk-med";

                return (
                  <tr key={t.id} className={isEmerg ? "row-emergency" : ""}>
                    <td className="ticket-id-cell">{t.id}</td>
                    <td className="date-cell">
                      {new Date(t.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td>
                      <span className={`pill ${t.report_type === "emergency" ? "pill-emergency" : "pill-suspected"}`}>
                        {t.report_type}
                      </span>
                    </td>
                    <td>
                      <div>
                        <strong>{(t.predicted_category || "Unclassified").replaceAll("_", " ")}</strong>
                        {Boolean(t.photo_url || t.photo_proof_path) && (() => {
                          const src = t.photo_url || t.photo_proof_path || "";
                          const isVid = t.media_type === "video" || /\.(mp4|webm|mov|mkv|avi)(\?.*)?$/i.test(src);
                          return (
                            <span className="table-photo-badge" title={isVid ? "Video field evidence attached" : "Photographic evidence attached"}>
                              {isVid ? "🎥" : "📷"}
                            </span>
                          );
                        })()}
                        {t.flagged_for_human_review && (
                          <span className="table-review-flag" title={t.review_reason || "Flagged for safety officer inspection"}>
                            🔍 Review
                          </span>
                        )}
                      </div>
                    </td>
                    <td>{t.zone_id || "—"}</td>
                    <td>
                      <span className={`risk-pill ${riskClass}`}>{t.risk_score != null ? t.risk_score : "—"}</span>
                    </td>
                    <td className="tier-cell">{TIER_LABELS[t.routing_tier] || t.routing_tier || "—"}</td>
                    <td>
                      <span className={`status-pill status-${t.status}`}>{t.status}</span>
                    </td>
                    <td>
                      <button className="inspect-btn" onClick={() => handleSelectTicket(t)}>
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Ticket Inspector Modal / Drawer */}
      {selectedTicket && (
        <div className="modal-backdrop" onClick={() => setSelectedTicket(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>Incident Ticket #{selectedTicket.id}</h3>
                <span className={`pill ${selectedTicket.report_type === "emergency" ? "pill-emergency" : "pill-suspected"}`}>
                  {selectedTicket.report_type.toUpperCase()}
                </span>
                <span className={`status-pill status-${selectedTicket.status}`} style={{ marginLeft: "8px" }}>
                  {selectedTicket.status}
                </span>
              </div>
              <button className="close-btn" onClick={() => setSelectedTicket(null)}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              {/* Recurring Hazard Alert */}
              {similarData?.recurring_hazard && (
                <div className="hazard-alert-banner">
                  ⚠ <strong>RECURRING HAZARD ALERT:</strong> {similarData.recurrence_note}
                </div>
              )}

              {/* Human Review Physical Inspection Flag */}
              {selectedTicket.flagged_for_human_review && (
                <div className="human-review-alert-banner">
                  🔍 <strong>FLAGGED FOR SAFETY OFFICER PHYSICAL INSPECTION:</strong>{" "}
                  {selectedTicket.review_reason || "Visual evidence uncorroborated or procedure gap; on-site inspection required (never auto-dismissed)."}
                </div>
              )}

              {/* Core Information Section */}
              <div className="inspector-section">
                <h4>Reporter & Narrative</h4>
                <div className="info-grid">
                  <div>
                    <strong>Reported At:</strong> {new Date(selectedTicket.created_at).toLocaleString()}
                  </div>
                  <div>
                    <strong>Employee ID:</strong> {selectedTicket.employee_id || "Anonymous"}
                  </div>
                  <div>
                    <strong>Language:</strong> {LANGUAGE_NAMES[selectedTicket.language] || selectedTicket.language?.toUpperCase()}{" "}
                    {selectedTicket.language_confidence && `(${Math.round(selectedTicket.language_confidence * 100)}%)`}
                  </div>
                  <div>
                    <strong>Reported Zone:</strong> {selectedTicket.zone_id || "Unspecified"}
                  </div>
                </div>

                <div className="narrative-box">
                  <p>
                    <strong>Original Statement ({selectedTicket.language}):</strong>
                    <br />
                    "{selectedTicket.incident_description}"
                  </p>
                  {selectedTicket.incident_description_en &&
                    selectedTicket.incident_description_en !== selectedTicket.incident_description && (
                      <p>
                        <strong>English Translation:</strong>
                        <br />
                        "{selectedTicket.incident_description_en}"
                      </p>
                    )}
                </div>

                {selectedTicket.audio_path && (
                  <div className="audio-player-row">
                    <span className="audio-label">Original Audio Recording:</span>
                    <audio controls src={audioUrl(selectedTicket.audio_path)} />
                  </div>
                )}
              </div>

              {/* Photographic or Video Field Evidence & AI Vision Dossier */}
              {(selectedTicket.photo_url || selectedTicket.media_url || selectedTicket.photo_proof_path) ? (() => {
                const src = photoUrl(selectedTicket.media_url || selectedTicket.photo_url || selectedTicket.photo_proof_path);
                const isVid = selectedTicket.media_type === "video" || /\.(mp4|webm|mov|mkv|avi)(\?.*)?$/i.test(src || "");
                const vAnalysis = selectedTicket.visual_analysis || selectedTicket.safety_report?.visual_analysis;
                return (
                  <div className="inspector-section photo-inspector-section">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                      <h4>{isVid ? "🎥 Visual Field Evidence (Video Recording)" : "📸 Photographic Field Evidence"}</h4>
                      <span className="badge-verified-photo">{isVid ? "✓ Video Attached" : "✓ Photo Attached"}</span>
                    </div>
                    <div className="inspector-photo-container">
                      {isVid ? (
                        <video
                          controls
                          playsInline
                          src={src}
                          className="inspector-video-img"
                        />
                      ) : (
                        <img
                          src={src}
                          alt={`Photographic evidence for incident #${selectedTicket.id}`}
                          className="inspector-photo-img"
                          onClick={() => window.open(src, "_blank")}
                        />
                      )}
                      <p className="photo-caption-sub">
                        File: <code>{selectedTicket.photo_proof_path?.split("/").pop() || "evidence_file"}</code> ({isVid ? "Recorded field video" : "Click image to view full resolution"})
                      </p>
                    </div>

                    {/* AI Visual Detection & Localization Dossier */}
                    {vAnalysis && (
                      <div style={{ marginTop: "1rem", padding: "0.85rem", background: "#0b1329", borderRadius: "8px", border: "1px solid #1e293b" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                          <span style={{ fontWeight: "700", color: "#e2e8f0", fontSize: "0.9rem" }}>🤖 AI Visual Hazard Localization</span>
                          <span style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: "800",
                            background: vAnalysis.is_valid_evidence ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                            color: vAnalysis.is_valid_evidence ? "#34d399" : "#fbbf24",
                            border: `1px solid ${vAnalysis.is_valid_evidence ? "#10b981" : "#f59e0b"}`,
                          }}>
                            {vAnalysis.is_valid_evidence ? "✓ CORROBORATED" : "⚠️ NO VISUAL CORROBORATION"}
                          </span>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.5rem" }}>
                          <div><strong>Detected Event:</strong> <span style={{ color: "#f8fafc", textTransform: "capitalize" }}>{vAnalysis.detected_event?.replace(/_/g, " ")}</span></div>
                          <div><strong>Confidence:</strong> <span style={{ color: "#38bdf8", fontWeight: "700" }}>{Math.round((vAnalysis.confidence || 0) * 100)}%</span></div>
                          <div><strong>Detector Model:</strong> <span style={{ color: "#cbd5e1" }}>{vAnalysis.model_version || "BSL-Vision-v2.5"}</span></div>
                          <div><strong>License:</strong> <span style={{ color: "#34d399", fontWeight: "700" }}>{vAnalysis.detector_license || "Apache-2.0"}</span></div>
                          {vAnalysis.image_sha256 && (
                            <div style={{ gridColumn: "span 2" }}>
                              <strong>SHA-256 Fingerprint:</strong> <code style={{ color: "#93c5fd", fontSize: "0.72rem" }}>{vAnalysis.image_sha256}</code>
                            </div>
                          )}
                          {vAnalysis.video_metadata && (
                            <div style={{ gridColumn: "span 2", color: "#a5b4fc" }}>
                              <strong>Video Sampling:</strong> {vAnalysis.video_metadata.sampled_frames_count} frames sampled across duration (Keyframe @ {vAnalysis.video_metadata.key_frame_timestamp_s}s)
                            </div>
                          )}
                        </div>

                        {/* Localized Detection Boxes */}
                        {vAnalysis.evidence_boxes && vAnalysis.evidence_boxes.length > 0 && (
                          <div style={{ marginTop: "0.5rem", paddingTop: "0.5rem", borderTop: "1px solid #1e293b" }}>
                            <span style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase", fontWeight: "700", display: "block", marginBottom: "0.3rem" }}>
                              Localized Detections & PPE:
                            </span>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                              {vAnalysis.evidence_boxes.map((b, idx) => (
                                <span key={idx} style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  padding: "2px 8px",
                                  borderRadius: "4px",
                                  fontSize: "0.75rem",
                                  background: "#1e293b",
                                  color: "#f8fafc",
                                  border: `1px solid ${b.color || "#3b82f6"}`,
                                }}>
                                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: b.color || "#3b82f6", marginRight: "6px" }}></span>
                                  {b.label} ({Math.round((b.confidence || 0) * 100)}%)
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Experimental Warning */}
                        {vAnalysis.is_experimental && (
                          <div style={{
                            marginTop: "0.5rem",
                            padding: "0.5rem 0.75rem",
                            borderRadius: "6px",
                            background: "rgba(239, 68, 68, 0.15)",
                            border: "1px solid #ef4444",
                            color: "#fca5a5",
                            fontSize: "0.75rem",
                            fontWeight: "600",
                          }}>
                            ⚠️ EXPERIMENTAL / NO VERIFIED PLANT TRAINING DATA: Detection for '{vAnalysis.detected_event}' is unvalidated. Do not rely on AI for this hazard class.
                          </div>
                        )}

                        <p style={{ margin: "0.5rem 0 0", fontSize: "0.78rem", color: "#cbd5e1", lineHeight: "1.3" }}>
                          {vAnalysis.visual_summary}
                        </p>
                        <p style={{ margin: "0.3rem 0 0", fontSize: "0.7rem", color: "#64748b", fontStyle: "italic" }}>
                          {vAnalysis.advisory_notice || "AI Vision output is evidence-only under Apache-2.0 license."}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })() : (
                <div className="inspector-section photo-inspector-section" style={{ opacity: 0.75 }}>
                  <h4>📸 Visual Field Evidence</h4>
                  <p style={{ fontSize: "0.85rem", color: "#94a3b8", margin: "0.25rem 0" }}>
                    <em>Optional evidence: No photo or video proof attached to this report. Incident processed via verbal interview findings.</em>
                  </p>
                </div>
              )}

              {/* Spatial Impact Assessment */}
              {selectedTicket.impact_assessment?.applicable && (
                <div className="inspector-section">
                  <h4>Spatial Impact Assessment</h4>
                  <div className="impact-box">
                    <p>
                      <strong>Affected Zones:</strong> {selectedTicket.impact_assessment.affected_zones.length} zone(s)
                      within hazard radius
                    </p>
                    <p>
                      <strong>Estimated Workforce at Risk:</strong>{" "}
                      {selectedTicket.impact_assessment.estimated_persons_at_risk_range[0]} –{" "}
                      {selectedTicket.impact_assessment.estimated_persons_at_risk_range[1]} persons
                    </p>
                    {selectedTicket.impact_assessment.civilian_exposure_alert && (
                      <p className="civilian-alert">
                        ⚠ <strong>CIVILIAN EXPOSURE WARNING:</strong> Blast or toxic plume envelope extends near plant perimeter!
                      </p>
                    )}
                    <table className="sub-table">
                      <thead>
                        <tr>
                          <th>Zone</th>
                          <th>Zone ID</th>
                          <th>Band</th>
                          <th>Distance</th>
                          <th>Modeled At Risk</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedTicket.impact_assessment.affected_zones.map((az) => (
                          <tr key={az.zone_id}>
                            <td>{az.name}</td>
                            <td>{az.zone_id}</td>
                            <td>
                              <span className={`band-pill band-${az.band}`}>{az.band}</span>
                            </td>
                            <td>{az.distance_m} m</td>
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
                </div>
              )}

              {/* Statutory Rule-Based Severity Matrix Breakdown */}
              <div className="inspector-section">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <h4>Transparent Severity Matrix</h4>
                  <span className="advisory-pill">ADVISORY ONLY</span>
                </div>
                <p className="subtitle" style={{ fontSize: "12px", color: "#94a3b8", marginTop: "-4px", marginBottom: "10px" }}>
                  Formula: min(1.0, max(Base, Base × Likelihood × Consequence × Proximity))
                </p>
                {selectedTicket.severity_factors ? (
                  <div className="matrix-factors-grid" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", marginBottom: "10px" }}>
                    <div className="matrix-factor-card" style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", padding: "8px", textAlign: "center" }}>
                      <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase", fontWeight: "700" }}>Base Hazard</div>
                      <div style={{ fontSize: "15px", color: "#38bdf8", fontWeight: "800", marginTop: "2px" }}>{selectedTicket.severity_factors.hazard_base_severity || 0.70}</div>
                    </div>
                    <div className="matrix-factor-card" style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", padding: "8px", textAlign: "center" }}>
                      <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase", fontWeight: "700" }}>Likelihood</div>
                      <div style={{ fontSize: "15px", color: "#38bdf8", fontWeight: "800", marginTop: "2px" }}>
                        {selectedTicket.severity_factors.likelihood?.multiplier ? `×${selectedTicket.severity_factors.likelihood.multiplier}` : "×1.0"}
                      </div>
                    </div>
                    <div className="matrix-factor-card" style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", padding: "8px", textAlign: "center" }}>
                      <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase", fontWeight: "700" }}>Consequence</div>
                      <div style={{ fontSize: "15px", color: "#38bdf8", fontWeight: "800", marginTop: "2px" }}>
                        {selectedTicket.severity_factors.consequence?.multiplier ? `×${selectedTicket.severity_factors.consequence.multiplier}` : "×1.0"}
                      </div>
                    </div>
                    <div className="matrix-factor-card" style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", padding: "8px", textAlign: "center" }}>
                      <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase", fontWeight: "700" }}>Asset Proximity</div>
                      <div style={{ fontSize: "15px", color: "#38bdf8", fontWeight: "800", marginTop: "2px" }}>
                        {selectedTicket.severity_factors.asset_proximity?.multiplier ? `×${selectedTicket.severity_factors.asset_proximity.multiplier}` : "×1.0"}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p style={{ color: "#94a3b8", fontSize: "12px" }}>Calculated Statutory Score: <strong>{selectedTicket.risk_score || "0.75"}</strong></p>
                )}
              </div>

              {/* Verified Evidence Findings Matrix */}
              {selectedTicket.safety_report?.verified_summary && (
                <div className="inspector-section">
                  <h4>Verified Evidence & Fact Findings</h4>
                  <table className="findings-table">
                    <tbody>
                      <tr>
                        <td className="finding-label">Visual Confirmation:</td>
                        <td className="finding-value">{selectedTicket.safety_report.verified_summary.observation_mode}</td>
                      </tr>
                      <tr>
                        <td className="finding-label">Hazard Activity:</td>
                        <td className="finding-value">{selectedTicket.safety_report.verified_summary.active_state}</td>
                      </tr>
                      <tr>
                        <td className="finding-label">Identified Equipment:</td>
                        <td className="finding-value"><strong>{selectedTicket.safety_report.verified_summary.equipment}</strong></td>
                      </tr>
                      <tr>
                        <td className="finding-label">Personnel Exposed:</td>
                        <td className="finding-value">{selectedTicket.safety_report.verified_summary.exposed_personnel}</td>
                      </tr>
                      <tr>
                        <td className="finding-label">Reported Symptoms:</td>
                        <td className="finding-value">{selectedTicket.safety_report.verified_summary.symptoms}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* Verification Interview Transcript */}
              {selectedTicket.verification_questions?.length > 0 && (
                <div className="inspector-section">
                  <h4>Verification Interview Q&A ({selectedTicket.verification_status?.replaceAll("_", " ")})</h4>
                  <p className="subtitle">
                    Verification Score:{" "}
                    <strong>
                      {selectedTicket.verification_score != null
                        ? `${Math.round(selectedTicket.verification_score * 100)}%`
                        : "N/A"}
                    </strong>
                  </p>
                  <div className="qa-list">
                    {selectedTicket.verification_questions.map((q, idx) => (
                      <div key={idx} className="qa-item">
                        <p className="qa-question">
                          <strong>Q{idx + 1}:</strong> {q}
                        </p>
                        <p className="qa-answer">
                          <strong>A:</strong> {selectedTicket.verification_answers?.[idx] || "—"}
                          {selectedTicket.verification_answers_en?.[idx] &&
                            selectedTicket.verification_answers_en[idx] !== selectedTicket.verification_answers[idx] && (
                              <span className="translated-note">
                                {" "}
                                (EN: "{selectedTicket.verification_answers_en[idx]}")
                              </span>
                            )}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* RAG Guidance & Citations */}
              {selectedTicket.guidance_text && (
                <div className="inspector-section">
                  <h4>Grounded SOP Guidance</h4>
                  <div style={{ background: "#451a03", border: "1px solid #f59e0b", borderRadius: "6px", padding: "8px 12px", marginBottom: "10px", fontSize: "12px", color: "#fef3c7" }}>
                    ⚠️ <strong>AI-Generated Guidance — Verify with Supervisor:</strong> Retrieve-and-quote citations from approved SOPs. Shift in-charge orders take statutory precedence.
                  </div>
                  {selectedTicket.sop_gap_detected && (
                    <div style={{ background: "#4c0519", border: "1px solid #e11d48", borderRadius: "6px", padding: "8px 12px", marginBottom: "10px", fontSize: "12px", color: "#ffe4e6" }}>
                      🚨 <strong>SOP GAP DETECTED:</strong> No approved SOP procedure available for this specific incident. Universal safe evacuation protocol active.
                    </div>
                  )}
                  <div className="guidance-box">
                    <pre className="guidance-pre">{selectedTicket.guidance_text}</pre>
                    {selectedTicket.guidance_sources?.length > 0 && (
                      <div className="sources-list">
                        <strong>Referenced Standard Operating Procedures:</strong>
                        <ul>
                          {selectedTicket.guidance_sources.map((s, i) => (
                            <li key={i}>
                              {s.title} — <em>{s.section}</em> ({s.path})
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Similar Historical Incidents */}
              {similarData?.similar_tickets?.length > 0 && (
                <div className="inspector-section">
                  <h4>Similar Past Incidents</h4>
                  <table className="sub-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Date</th>
                        <th>Zone</th>
                        <th>Category</th>
                        <th>Similarity</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {similarData.similar_tickets.map((st) => (
                        <tr key={st.id}>
                          <td>{st.id}</td>
                          <td>{new Date(st.created_at).toLocaleDateString()}</td>
                          <td>
                            {st.zone_id}{" "}
                            {st.is_same_zone && <span className="same-zone-tag">Same Zone</span>}
                          </td>
                          <td>{st.predicted_category?.replaceAll("_", " ")}</td>
                          <td>{Math.round(st.similarity * 100)}%</td>
                          <td>{st.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Designated Emergency Dispatch Recipients */}
              {selectedTicket.safety_report?.recipients?.length > 0 && (
                <div className="inspector-section recipients-inspector-section">
                  <h4>🚨 Designated Bokaro Emergency Dispatch Recipients</h4>
                  <p className="subtitle" style={{ marginBottom: "0.75rem" }}>
                    Automated safety authority dispatch routing based on hazard category, spatial zone, and risk score:
                  </p>
                  <div className="recipients-grid">
                    {selectedTicket.safety_report.recipients.map((rec, idx) => (
                      <div key={idx} className="recipient-row-card">
                        <div className="recipient-row-header">
                          <strong>{rec.department || rec.dept}</strong>
                          <span className="recipient-unit-badge">{rec.priority || rec.unit}</span>
                        </div>
                        <div className="recipient-row-details">
                          <div><span className="rec-label">Role:</span> {rec.role}</div>
                          <div><span className="rec-label">Contact / Ext:</span> <code>{rec.contact || rec.hotline}</code></div>
                          <div><span className="rec-label">Status:</span> <span className="channel-pill">{rec.status || rec.dispatch_channel}</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Resolution & Officer Actions */}
              <div className="inspector-section resolution-section">
                <h4>Safety Officer Actions & Resolution</h4>
                <form onSubmit={handleSaveUpdates} className="resolution-form">
                  <div className="form-row">
                    <div className="form-field">
                      <label>Update Status:</label>
                      <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="escalated">Escalated</option>
                      </select>
                    </div>

                    <div className="form-field">
                      <label>Reassign Routing Tier:</label>
                      <select value={editTier} onChange={(e) => setEditTier(e.target.value)}>
                        <option value="emergency_authority">Emergency Authority</option>
                        <option value="plant_safety_officer">Plant Safety Officer</option>
                        <option value="shift_supervisor">Shift Supervisor</option>
                        <option value="safety_team_queue">Safety Team Queue</option>
                      </select>
                    </div>
                  </div>

                  <div className="form-field">
                    <label>Resolution / Investigation Notes:</label>
                    <textarea
                      rows={3}
                      value={editNotes}
                      onChange={(e) => setEditNotes(e.target.value)}
                      placeholder="Add official findings, dispatch notes, corrective actions..."
                    />
                  </div>

                  <div className="form-actions">
                    <button type="submit" className="save-btn" disabled={updating}>
                      {updating ? "Saving..." : "Save Ticket Updates"}
                    </button>
                    {saveSuccess && <span className="success-msg">✓ Updates saved successfully</span>}
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
