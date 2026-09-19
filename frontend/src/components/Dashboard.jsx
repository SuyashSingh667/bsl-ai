import { useEffect, useState } from "react";
import {
  audioUrl,
  getSimilarIncidents,
  getTickets,
  updateTicket,
  photoUrl,
  assignAction,
  closeAction,
  getSafetyTrends,
  getCultureMetrics,
  acknowledgeDispatch,
  markOnSite,
  checkAllDispatches,
  getPdfDossierUrl,
} from "../api";
import PlantMap from "./PlantMap";

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

const LIFECYCLE_STAGES = [
  { key: "received", label: "Received", icon: "📥" },
  { key: "under_review", label: "Under Review", icon: "🔍" },
  { key: "action_assigned", label: "Action Assigned", icon: "🛠️" },
  { key: "action_taken", label: "Action Taken", icon: "🚧" },
  { key: "resolved", label: "Resolved", icon: "✅" },
];

export default function Dashboard() {
  const [dashboardView, setDashboardView] = useState("queue"); // "queue" | "map" | "trends" | "culture"
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterTier, setFilterTier] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortMode, setSortMode] = useState("priority"); // "priority" | "oldest" | "newest"
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [similarData, setSimilarData] = useState(null);
  const [updating, setUpdating] = useState(false);
  const [editStatus, setEditStatus] = useState("");
  const [editTier, setEditTier] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Phase 7: Dispatch ACK & On-Site Responder State
  const [ackResponder, setAckResponder] = useState("");
  const [ackNotes, setAckNotes] = useState("");
  const [onSiteLead, setOnSiteLead] = useState("");
  const [onSiteNotes, setOnSiteNotes] = useState("");
  const [dispatchActionLoading, setDispatchActionLoading] = useState(false);
  const [dispatchActionMsg, setDispatchActionMsg] = useState(null);
  const [escalationNotice, setEscalationNotice] = useState(null);

  // Corrective Action assignment & closure state
  const [assignedTo, setAssignedTo] = useState("");
  const [correctiveAction, setCorrectiveAction] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [closureNotes, setClosureNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);

  // Trends & Culture views state
  const [trendsData, setTrendsData] = useState(null);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [cultureData, setCultureData] = useState(null);
  const [cultureLoading, setCultureLoading] = useState(false);

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

  async function loadTrends() {
    setTrendsLoading(true);
    try {
      const data = await getSafetyTrends("bsl_bokaro");
      setTrendsData(data);
    } catch (err) {
      console.warn("Failed to load safety trends:", err);
    } finally {
      setTrendsLoading(false);
    }
  }

  async function loadCulture() {
    setCultureLoading(true);
    try {
      const data = await getCultureMetrics("bsl_bokaro");
      setCultureData(data);
    } catch (err) {
      console.warn("Failed to load culture metrics:", err);
    } finally {
      setCultureLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
  }, [filterTier, filterStatus]);

  useEffect(() => {
    if (dashboardView === "trends") loadTrends();
    if (dashboardView === "culture") loadCulture();
  }, [dashboardView]);

  async function handleSelectTicket(t) {
    setSelectedTicket(t);
    setEditStatus(t.status || "open");
    setEditTier(t.routing_tier || "safety_team_queue");
    setEditNotes(t.resolution_notes || "");
    setAssignedTo(t.assigned_to || "");
    setCorrectiveAction(t.corrective_action || "");
    setDueDate(t.due_date ? t.due_date.slice(0, 10) : "");
    setClosureNotes(t.closure_notes || "");
    setAckResponder(t.acknowledged_by || "");
    setAckNotes("");
    setOnSiteLead(t.on_site_by || "");
    setOnSiteNotes("");
    setDispatchActionMsg(null);
    setSaveSuccess(false);
    setActionMsg(null);
    setSimilarData(null);
    try {
      const sim = await getSimilarIncidents(t.id);
      setSimilarData(sim);
    } catch {
      // similar endpoint non-critical
    }
  }

  async function handleAcknowledgeDispatch(e) {
    e.preventDefault();
    if (!selectedTicket || !ackResponder.trim()) {
      alert("Please enter the responder or team name acknowledging receipt.");
      return;
    }
    setDispatchActionLoading(true);
    setDispatchActionMsg(null);
    try {
      const updated = await acknowledgeDispatch(selectedTicket.id, {
        acknowledgedBy: ackResponder.trim(),
        notes: ackNotes.trim(),
      });
      setSelectedTicket(updated);
      setDispatchActionMsg(`✓ Dispatch receipt acknowledged by ${updated.acknowledged_by}!`);
      setTickets((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      alert("Failed to acknowledge dispatch: " + err.message);
    } finally {
      setDispatchActionLoading(false);
    }
  }

  async function handleMarkOnSite(e) {
    e.preventDefault();
    if (!selectedTicket || !onSiteLead.trim()) {
      alert("Please enter the on-site responder or team lead name.");
      return;
    }
    setDispatchActionLoading(true);
    setDispatchActionMsg(null);
    try {
      const updated = await markOnSite(selectedTicket.id, {
        onSiteBy: onSiteLead.trim(),
        notes: onSiteNotes.trim(),
      });
      setSelectedTicket(updated);
      setDispatchActionMsg(`✓ Responders confirmed on-site in Zone ${updated.zone_id}!`);
      setTickets((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      alert("Failed to mark responders on-site: " + err.message);
    } finally {
      setDispatchActionLoading(false);
    }
  }

  async function handleCheckEscalations() {
    try {
      const res = await checkAllDispatches(60);
      if (res.escalated_count > 0) {
        setEscalationNotice(`⚠️ Auto-escalated ${res.escalated_count} unacknowledged dispatch(es) to secondary emergency authorities!`);
        loadTickets();
      } else {
        setEscalationNotice("✓ All dispatches acknowledged within SLA.");
        setTimeout(() => setEscalationNotice(null), 4000);
      }
    } catch (err) {
      console.warn("Escalation check error:", err);
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
      setTickets((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      alert("Failed to save updates: " + err.message);
    } finally {
      setUpdating(false);
    }
  }

  async function handleAssignAction(e) {
    e.preventDefault();
    if (!selectedTicket || !assignedTo.trim() || !correctiveAction.trim()) {
      alert("Please provide both assignee name and corrective action description.");
      return;
    }
    setActionLoading(true);
    setActionMsg(null);
    try {
      const updated = await assignAction(selectedTicket.id, {
        assignedTo: assignedTo.trim(),
        correctiveAction: correctiveAction.trim(),
        dueDate: dueDate ? new Date(dueDate).toISOString() : null,
      });
      setSelectedTicket(updated);
      setActionMsg("Corrective action assigned successfully!");
      setTickets((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      alert("Failed to assign action: " + err.message);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCloseAction(e) {
    e.preventDefault();
    if (!selectedTicket || !closureNotes.trim()) {
      alert("Please provide verification closure notes or work order ID.");
      return;
    }
    setActionLoading(true);
    setActionMsg(null);
    try {
      const updated = await closeAction(selectedTicket.id, {
        closureNotes: closureNotes.trim(),
      });
      setSelectedTicket(updated);
      setEditStatus("resolved");
      setActionMsg(`Hazard resolved and closed! SLA Turnaround: ${updated.closure_time_hours} hrs.`);
      setTickets((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      alert("Failed to close action: " + err.message);
    } finally {
      setActionLoading(false);
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
      (t.incident_description_en && t.incident_description_en.toLowerCase().includes(q)) ||
      (t.anonymous_tracking_code && t.anonymous_tracking_code.toLowerCase().includes(q))
    );
  });

  const sortedTickets = [...filteredTickets].sort((a, b) => {
    if (sortMode === "priority") {
      // 1. Emergency Primacy
      const aEmerg = a.report_type === "emergency" || a.routing_tier === "emergency_authority" ? 1 : 0;
      const bEmerg = b.report_type === "emergency" || b.routing_tier === "emergency_authority" ? 1 : 0;
      if (aEmerg !== bEmerg) return bEmerg - aEmerg;

      // 2. Risk Score
      const aRisk = a.risk_score != null ? a.risk_score : 0;
      const bRisk = b.risk_score != null ? b.risk_score : 0;
      if (Math.abs(bRisk - aRisk) > 0.05) return bRisk - aRisk;

      // 3. Dispatch Status urgency
      const statusWeights = { dispatched: 5, acknowledged: 4, pending: 3, on_site: 2, closed: 1 };
      const aWeight = statusWeights[a.dispatch_status] || 0;
      const bWeight = statusWeights[b.dispatch_status] || 0;
      if (aWeight !== bWeight) return bWeight - aWeight;

      // 4. Age (oldest first for unhandled)
      return new Date(a.created_at) - new Date(b.created_at);
    } else if (sortMode === "oldest") {
      return new Date(a.created_at) - new Date(b.created_at);
    } else {
      return new Date(b.created_at) - new Date(a.created_at);
    }
  });

  const emergencyCount = tickets.filter(
    (t) => t.report_type === "emergency" || t.routing_tier === "emergency_authority"
  ).length;
  const highRiskCount = tickets.filter((t) => (t.risk_score || 0) >= 0.7).length;
  const inProgressCount = tickets.filter((t) => t.status === "in_progress" || t.dispatch_status === "dispatched").length;
  const openCount = tickets.filter((t) => t.status === "open").length;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2>Safety Intelligence Command Center</h2>
          <p className="subtitle">Real-time incident triage, spatial verification & decision support</p>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            className="refresh-btn"
            style={{ background: "#f59e0b", color: "#070d18", fontWeight: "800" }}
            onClick={handleCheckEscalations}
            title="Evaluate SLA deadlines and auto-escalate unacknowledged dispatches"
          >
            ⚡ Check SLA Escalations
          </button>
          <button className="refresh-btn" onClick={loadTickets} disabled={loading}>
            🔄 {loading ? "Refreshing..." : "Refresh Queue"}
          </button>
        </div>
      </div>

      {/* Escalation SLA Notification Banner */}
      {escalationNotice && (
        <div style={{
          background: escalationNotice.startsWith("⚠️") ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
          border: `1px solid ${escalationNotice.startsWith("⚠️") ? "#ef4444" : "#10b981"}`,
          color: escalationNotice.startsWith("⚠️") ? "#fca5a5" : "#34d399",
          padding: "10px 16px",
          borderRadius: "8px",
          marginBottom: "1rem",
          fontWeight: "700",
          fontSize: "0.85rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <span>{escalationNotice}</span>
          <button onClick={() => setEscalationNotice(null)} style={{ background: "transparent", border: "none", color: "inherit", cursor: "pointer", fontWeight: "bold" }}>✕</button>
        </div>
      )}

      {/* View Switcher Sub-Navigation */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "1.25rem", borderBottom: "1px solid #334155", paddingBottom: "10px" }}>
        <button
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            fontWeight: "700",
            fontSize: "0.85rem",
            background: dashboardView === "queue" ? "#38bdf8" : "#1e293b",
            color: dashboardView === "queue" ? "#070d18" : "#cbd5e1",
          }}
          onClick={() => setDashboardView("queue")}
        >
          📋 Incident Triage Queue ({tickets.length})
        </button>
        <button
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            fontWeight: "700",
            fontSize: "0.85rem",
            background: dashboardView === "map" ? "#38bdf8" : "#1e293b",
            color: dashboardView === "map" ? "#070d18" : "#cbd5e1",
          }}
          onClick={() => setDashboardView("map")}
        >
          🗺️ Plant Layout & Zones
        </button>
        <button
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            fontWeight: "700",
            fontSize: "0.85rem",
            background: dashboardView === "trends" ? "#38bdf8" : "#1e293b",
            color: dashboardView === "trends" ? "#070d18" : "#cbd5e1",
          }}
          onClick={() => setDashboardView("trends")}
        >
          📈 Safety Trends & Hotspots
        </button>
        <button
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            fontWeight: "700",
            fontSize: "0.85rem",
            background: dashboardView === "culture" ? "#38bdf8" : "#1e293b",
            color: dashboardView === "culture" ? "#070d18" : "#cbd5e1",
          }}
          onClick={() => setDashboardView("culture")}
        >
          🤝 Team Recognition & Culture
        </button>
      </div>

      {/* VIEW 1: INCIDENT TRIAGE QUEUE */}
      {dashboardView === "queue" && (
        <>
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
              <div className="metric-label">Active Response</div>
            </div>
          </div>

          {/* Filters & Sorting Bar */}
          <div className="filters-bar" style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center" }}>
            <div className="filter-group">
              <label>Sort By:</label>
              <select value={sortMode} onChange={(e) => setSortMode(e.target.value)} style={{ fontWeight: "700", color: "#38bdf8" }}>
                <option value="priority">🔥 Priority & Urgency First</option>
                <option value="oldest">⏱️ Longest Awaiting Response</option>
                <option value="newest">🆕 Newest First</option>
              </select>
            </div>

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

            <div className="filter-group search-group" style={{ flex: 1, minWidth: "220px" }}>
              <input
                type="text"
                placeholder="Search ID, Zone, Category, Text, Tracking Code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {error && <p className="error-text">{error}</p>}

          {/* Tickets Table */}
          <div className="tickets-table-container">
            <table className="tickets-table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Logged</th>
                  <th>Type / Mode</th>
                  <th>Category</th>
                  <th>Zone / Shift</th>
                  <th>Severity</th>
                  <th>Dispatch Status & ACK</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedTickets.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: "center", padding: "2rem", color: "#888" }}>
                      {loading ? "Loading incidents..." : "No incidents found matching current filters."}
                    </td>
                  </tr>
                ) : (
                  sortedTickets.map((t) => {
                    const isEmerg = t.report_type === "emergency" || t.routing_tier === "emergency_authority";
                    const risk = t.risk_score != null ? t.risk_score : 0;
                    let riskClass = "risk-low";
                    if (risk >= 0.7) riskClass = "risk-high";
                    else if (risk >= 0.4) riskClass = "risk-med";

                    // One-Glance Dispatch Status calculation
                    const dStatus = t.dispatch_status || "pending";
                    let dispatchBadge = (
                      <span className="status-pill" style={{ background: "#334155", color: "#94a3b8" }}>
                        ⏳ Pending
                      </span>
                    );

                    if (dStatus === "dispatched") {
                      dispatchBadge = (
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          <span className="status-pill status-escalated" style={{ animation: "pulse 2s infinite" }}>
                            🚨 DISPATCHED
                          </span>
                          {t.escalation_level > 0 && (
                            <span style={{ fontSize: "0.68rem", color: "#f87171", fontWeight: "800" }}>
                              ⚠️ Escalated (L{t.escalation_level})
                            </span>
                          )}
                        </div>
                      );
                    } else if (dStatus === "acknowledged") {
                      dispatchBadge = (
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          <span className="status-pill" style={{ background: "rgba(14, 165, 233, 0.2)", color: "#38bdf8", border: "1px solid #0ea5e9" }}>
                            ✓ ACKNOWLEDGED
                          </span>
                          {t.acknowledged_by && (
                            <span style={{ fontSize: "0.68rem", color: "#bae6fd" }}>
                              by {t.acknowledged_by}
                            </span>
                          )}
                        </div>
                      );
                    } else if (dStatus === "on_site") {
                      dispatchBadge = (
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          <span className="status-pill" style={{ background: "rgba(16, 185, 129, 0.2)", color: "#34d399", border: "1px solid #10b981" }}>
                            🚒 ON-SITE
                          </span>
                          {t.on_site_by && (
                            <span style={{ fontSize: "0.68rem", color: "#a7f3d0" }}>
                              Lead: {t.on_site_by}
                            </span>
                          )}
                        </div>
                      );
                    } else if (dStatus === "closed" || t.status === "resolved") {
                      dispatchBadge = (
                        <span className="status-pill status-resolved">
                          ✅ RESOLVED
                        </span>
                      );
                    }

                    return (
                      <tr key={t.id} className={isEmerg ? "row-emergency" : ""}>
                        <td className="ticket-id-cell">
                          {t.id.slice(0, 8)}
                          {t.anonymous_tracking_code && (
                            <div style={{ fontSize: "0.72rem", color: "#a78bfa", fontWeight: "700" }}>
                              {t.anonymous_tracking_code}
                            </div>
                          )}
                        </td>
                        <td className="date-cell">
                          {new Date(t.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </td>
                        <td>
                          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                            <span className={`pill ${t.report_type === "emergency" ? "pill-emergency" : "pill-suspected"}`}>
                              {t.report_type}
                            </span>
                            {t.is_anonymous && (
                              <span style={{ fontSize: "0.68rem", color: "#c084fc", fontWeight: "700" }}>
                                🔒 Anonymous
                              </span>
                            )}
                          </div>
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
                        <td>
                          <div><strong>{t.zone_id || "—"}</strong></div>
                          {t.shift && <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{t.shift}</div>}
                        </td>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span className={`risk-pill ${riskClass}`}>{t.risk_score != null ? t.risk_score : "—"}</span>
                            <span style={{ fontSize: "0.65rem", color: "#94a3b8" }}>ADVISORY</span>
                          </div>
                        </td>
                        <td>
                          {dispatchBadge}
                        </td>
                        <td>
                          <div style={{ display: "flex", gap: "4px" }}>
                            <button className="inspect-btn" onClick={() => handleSelectTicket(t)} title="Inspect incident details">
                              Inspect
                            </button>
                            <a
                              href={getPdfDossierUrl(t.id)}
                              target="_blank"
                              rel="noreferrer"
                              className="inspect-btn"
                              style={{ background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "3px", padding: "4px 8px" }}
                              title="Download official PDF incident dossier"
                            >
                              📄 PDF
                            </a>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* VIEW 2: FULL PLANT MAP VIEW */}
      {dashboardView === "map" && (
        <div style={{ marginTop: "1rem" }}>
          <PlantMap plantId="bsl_bokaro" />
        </div>
      )}

      {/* VIEW 3: SAFETY TRENDS & HOTSPOTS */}
      {dashboardView === "trends" && (
        <div style={{ color: "#f8fafc" }}>
          {trendsLoading ? (
            <p style={{ textAlign: "center", padding: "2rem", color: "#94a3b8" }}>Loading trend analytics...</p>
          ) : trendsData ? (
            <div>
              {/* Trends KPI cards */}
              <div className="metrics-row" style={{ marginBottom: "1.5rem" }}>
                <div className="metric-card">
                  <div className="metric-value">{trendsData.total_incidents}</div>
                  <div className="metric-label">Total Reports</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value" style={{ color: "#38bdf8" }}>{trendsData.total_near_misses}</div>
                  <div className="metric-label">Near-Misses Logged</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value" style={{ color: "#34d399" }}>{trendsData.closed_near_misses}</div>
                  <div className="metric-label">Hazards Closed</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value" style={{ color: "#fbbf24" }}>{trendsData.avg_closure_time_hours}h</div>
                  <div className="metric-label">Avg Turnaround SLA</div>
                </div>
              </div>

              {/* Grid: Zone Hotspots & Shift Breakdown */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
                <div style={{ background: "#0c1524", border: "1px solid #1e293b", borderRadius: "10px", padding: "1rem" }}>
                  <h3 style={{ fontSize: "1rem", color: "#38bdf8", marginBottom: "0.75rem" }}>📍 Repeat Hazard Hotspots by Zone</h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {Object.entries(trendsData.hazards_by_zone || {}).map(([zone, count]) => (
                      <div key={zone} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0f1d32", padding: "8px 12px", borderRadius: "6px" }}>
                        <span style={{ fontWeight: "700", color: "#e2e8f0" }}>{zone}</span>
                        <span style={{ background: "rgba(56, 189, 248, 0.2)", color: "#38bdf8", padding: "2px 8px", borderRadius: "4px", fontWeight: "800", fontSize: "0.8rem" }}>
                          {count} incidents
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ background: "#0c1524", border: "1px solid #1e293b", borderRadius: "10px", padding: "1rem" }}>
                  <h3 style={{ fontSize: "1rem", color: "#38bdf8", marginBottom: "0.75rem" }}>🕒 Incidents by Operational Shift</h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {Object.entries(trendsData.hazards_by_shift || {}).map(([shift, count]) => (
                      <div key={shift} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0f1d32", padding: "8px 12px", borderRadius: "6px" }}>
                        <span style={{ fontWeight: "700", color: "#e2e8f0" }}>{shift}</span>
                        <span style={{ background: "rgba(16, 185, 129, 0.2)", color: "#34d399", padding: "2px 8px", borderRadius: "4px", fontWeight: "800", fontSize: "0.8rem" }}>
                          {count} logged
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Repeat Equipment Hazards Table */}
              <div style={{ background: "#0c1524", border: "1px solid #1e293b", borderRadius: "10px", padding: "1rem" }}>
                <h3 style={{ fontSize: "1rem", color: "#fbbf24", marginBottom: "0.75rem" }}>⚙️ Repeat Equipment Vulnerabilities</h3>
                <table className="tickets-table" style={{ margin: 0 }}>
                  <thead>
                    <tr>
                      <th>Equipment Tag</th>
                      <th>Occurrences</th>
                      <th>Primary Hazard</th>
                      <th>Primary Zone</th>
                      <th>Maintenance Recommendation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trendsData.repeat_equipment_hazards?.length > 0 ? (
                      trendsData.repeat_equipment_hazards.map((eq, idx) => (
                        <tr key={idx}>
                          <td><strong>{eq.equipment}</strong></td>
                          <td><span style={{ color: "#ef4444", fontWeight: "800" }}>{eq.occurrences}x</span></td>
                          <td>{eq.most_common_hazard}</td>
                          <td>{eq.zone}</td>
                          <td style={{ color: "#94a3b8" }}>Requires scheduled engineering overhaul & PM check</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" style={{ textAlign: "center", padding: "1rem", color: "#64748b" }}>
                          No repeat equipment anomalies identified yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* VIEW 3: TEAM CULTURE & POSITIVE REINFORCEMENT */}
      {dashboardView === "culture" && (
        <div style={{ color: "#f8fafc" }}>
          {cultureLoading ? (
            <p style={{ textAlign: "center", padding: "2rem", color: "#94a3b8" }}>Loading culture metrics...</p>
          ) : cultureData ? (
            <div>
              {/* Anti-Surveillance Guarantee Callout */}
              <div style={{
                background: "#1c1c1e",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: "12px",
                padding: "1rem 1.25rem",
                marginBottom: "1.5rem",
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}>
                <div style={{ fontSize: "1.8rem" }}>🛡️</div>
                <div>
                  <strong style={{ color: "#ffffff", fontSize: "0.95rem" }}>BSL Anti-Surveillance & Psychological Safety Policy:</strong>
                  <p style={{ margin: "4px 0 0 0", color: "rgba(235, 235, 245, 0.7)", fontSize: "0.85rem", lineHeight: "1.4" }}>
                    Under SAIL / Bokaro Steel Plant guidelines, safety reporting is collaborative problem-solving. No worker rankings, leaderboards, or disciplinary consequences exist for near-misses. Recognition is awarded collectively to plant shifts.
                  </p>
                </div>
              </div>

              {/* Shift Collaboration Breakdown */}
              <div style={{ background: "#0c1524", border: "1px solid #1e293b", borderRadius: "10px", padding: "1.25rem", marginBottom: "1.5rem" }}>
                <h3 style={{ fontSize: "1rem", color: "#38bdf8", marginBottom: "1rem" }}>
                  👥 Shift Safety Participation (Collective Team Metrics)
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
                  {cultureData.shift_participation?.map((sp) => (
                    <div key={sp.shift} style={{ background: "#0f1d32", border: "1px solid #334155", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
                      <div style={{ fontSize: "1.1rem", fontWeight: "800", color: "#f8fafc", marginBottom: "4px" }}>{sp.shift}</div>
                      <div style={{ fontSize: "1.75rem", fontWeight: "900", color: "#34d399", marginBottom: "4px" }}>{sp.pct}%</div>
                      <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>{sp.count} Reports Logged</div>
                      <div style={{ fontSize: "0.8rem", color: "#38bdf8", fontWeight: "700", marginTop: "2px" }}>{sp.resolved} Hazards Permanently Fixed</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

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
                {selectedTicket.anonymous_tracking_code && (
                  <span style={{ marginLeft: "8px", background: "rgba(139, 92, 246, 0.2)", color: "#c084fc", border: "1px solid #7c3aed", padding: "2px 8px", borderRadius: "6px", fontSize: "0.75rem", fontWeight: "800" }}>
                    🔒 Code: {selectedTicket.anonymous_tracking_code}
                  </span>
                )}
              </div>
              <button className="close-btn" onClick={() => setSelectedTicket(null)}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              {/* Official Action Bar: PDF Dossier Export */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0b1329", border: "1px solid #1e293b", borderRadius: "8px", padding: "10px 14px", marginBottom: "1rem" }}>
                <div>
                  <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#f8fafc" }}>
                    📄 Heavy Industrial Safety Incident Dossier
                  </span>
                  <p style={{ margin: "2px 0 0 0", fontSize: "0.75rem", color: "#94a3b8" }}>
                    Includes universal transcript, audio link, advisory AI tags, SOP citations, dispatch timeline & SHA-256 seal.
                  </p>
                </div>
                <a
                  href={getPdfDossierUrl(selectedTicket.id)}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    background: "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
                    color: "#ffffff",
                    fontWeight: "800",
                    fontSize: "0.85rem",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    textDecoration: "none",
                    boxShadow: "0 2px 8px rgba(37,99,235,0.3)",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>📥 Download Official PDF Dossier</span>
                </a>
              </div>

              {/* Emergency Dispatch, Acknowledgment & On-Site Response Tracking Card */}
              <div style={{ background: "#0f172a", border: "1.5px solid #334155", borderRadius: "10px", padding: "1rem", marginBottom: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <h4 style={{ margin: 0, color: "#38bdf8", fontSize: "0.95rem" }}>
                    🚨 Emergency Dispatch & Response Tracking
                  </h4>
                  <span style={{
                    fontSize: "0.75rem",
                    fontWeight: "800",
                    padding: "3px 10px",
                    borderRadius: "6px",
                    background: selectedTicket.dispatch_status === "dispatched" ? "rgba(239, 68, 68, 0.2)" : selectedTicket.dispatch_status === "acknowledged" ? "rgba(14, 165, 233, 0.2)" : selectedTicket.dispatch_status === "on_site" ? "rgba(16, 185, 129, 0.2)" : "rgba(100, 116, 139, 0.2)",
                    color: selectedTicket.dispatch_status === "dispatched" ? "#f87171" : selectedTicket.dispatch_status === "acknowledged" ? "#38bdf8" : selectedTicket.dispatch_status === "on_site" ? "#34d399" : "#94a3b8",
                    border: `1px solid ${selectedTicket.dispatch_status === "dispatched" ? "#ef4444" : selectedTicket.dispatch_status === "acknowledged" ? "#0ea5e9" : selectedTicket.dispatch_status === "on_site" ? "#10b981" : "#475569"}`,
                  }}>
                    STATUS: {selectedTicket.dispatch_status ? selectedTicket.dispatch_status.toUpperCase() : "PENDING"}
                  </span>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", fontSize: "0.8rem", color: "#94a3b8", background: "#090d16", padding: "10px", borderRadius: "6px", border: "1px solid #1e293b", marginBottom: "10px" }}>
                  <div>
                    <span style={{ color: "#64748b", display: "block", fontSize: "0.7rem", textTransform: "uppercase" }}>Dispatched At</span>
                    <strong style={{ color: "#f8fafc" }}>{selectedTicket.dispatched_at ? new Date(selectedTicket.dispatched_at).toLocaleTimeString() : "Pending"}</strong>
                  </div>
                  <div>
                    <span style={{ color: "#64748b", display: "block", fontSize: "0.7rem", textTransform: "uppercase" }}>ACK Received</span>
                    <strong style={{ color: selectedTicket.acknowledged_at ? "#38bdf8" : "#f59e0b" }}>
                      {selectedTicket.acknowledged_at ? `${new Date(selectedTicket.acknowledged_at).toLocaleTimeString()} (${selectedTicket.acknowledged_by || "Team"})` : "Awaiting ACK"}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: "#64748b", display: "block", fontSize: "0.7rem", textTransform: "uppercase" }}>Responders On-Site</span>
                    <strong style={{ color: selectedTicket.on_site_at ? "#34d399" : "#64748b" }}>
                      {selectedTicket.on_site_at ? `${new Date(selectedTicket.on_site_at).toLocaleTimeString()} (${selectedTicket.on_site_by || "Lead"})` : "Not Arrived"}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: "#64748b", display: "block", fontSize: "0.7rem", textTransform: "uppercase" }}>Escalation Level</span>
                    <strong style={{ color: selectedTicket.escalation_level > 0 ? "#ef4444" : "#94a3b8" }}>
                      {selectedTicket.escalation_level > 0 ? `Level ${selectedTicket.escalation_level} (Overdue)` : "Normal"}
                    </strong>
                  </div>
                </div>

                {/* Dispatch Action Form: ACK receipt if dispatched */}
                {selectedTicket.dispatch_status === "dispatched" && (
                  <form onSubmit={handleAcknowledgeDispatch} style={{ background: "rgba(14, 165, 233, 0.08)", border: "1px solid #0ea5e9", borderRadius: "6px", padding: "10px", marginTop: "8px" }}>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <input
                        type="text"
                        placeholder="Responder Name / Unit (e.g. Officer Raman / Fire Unit 2)"
                        value={ackResponder}
                        onChange={(e) => setAckResponder(e.target.value)}
                        style={{ flex: 1, padding: "8px", background: "#070d18", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem" }}
                      />
                      <button
                        type="submit"
                        disabled={dispatchActionLoading}
                        style={{ background: "#0ea5e9", color: "#070d18", fontWeight: "800", padding: "8px 16px", borderRadius: "6px", border: "none", cursor: "pointer", whiteSpace: "nowrap" }}
                      >
                        {dispatchActionLoading ? "Submitting..." : "✅ Acknowledge Receipt"}
                      </button>
                    </div>
                  </form>
                )}

                {/* Dispatch Action Form: Mark On-Site if acknowledged */}
                {selectedTicket.dispatch_status === "acknowledged" && (
                  <form onSubmit={handleMarkOnSite} style={{ background: "rgba(16, 185, 129, 0.08)", border: "1px solid #10b981", borderRadius: "6px", padding: "10px", marginTop: "8px" }}>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <input
                        type="text"
                        placeholder="On-Site Lead Name (e.g. Lead Engineer Mukherjee)"
                        value={onSiteLead}
                        onChange={(e) => setOnSiteLead(e.target.value)}
                        style={{ flex: 1, padding: "8px", background: "#070d18", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem" }}
                      />
                      <button
                        type="submit"
                        disabled={dispatchActionLoading}
                        style={{ background: "#10b981", color: "#070d18", fontWeight: "800", padding: "8px 16px", borderRadius: "6px", border: "none", cursor: "pointer", whiteSpace: "nowrap" }}
                      >
                        {dispatchActionLoading ? "Submitting..." : "🚒 Mark Responders On-Site"}
                      </button>
                    </div>
                  </form>
                )}

                {dispatchActionMsg && (
                  <div style={{ marginTop: "8px", color: "#38bdf8", fontSize: "0.85rem", fontWeight: "700" }}>
                    {dispatchActionMsg}
                  </div>
                )}
              </div>

              {/* Lifecycle Stage Progress Bar */}
              <div style={{ background: "#070d18", border: "1px solid #1e293b", borderRadius: "10px", padding: "10px 14px", marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase", marginBottom: "8px" }}>
                  Near-Miss Lifecycle Milestone:
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  {LIFECYCLE_STAGES.map((st, idx) => {
                    const currentIdx = LIFECYCLE_STAGES.findIndex((s) => s.key === (selectedTicket.lifecycle_stage || "received"));
                    const isPassed = idx <= currentIdx;
                    const isCurrent = idx === currentIdx;
                    return (
                      <div key={st.key} style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
                        <div style={{
                          width: "30px",
                          height: "30px",
                          borderRadius: "15px",
                          display: "flex",
                          justifyContent: "center",
                          alignItems: "center",
                          fontSize: "0.85rem",
                          background: isPassed ? "rgba(16, 185, 129, 0.2)" : "#1e293b",
                          border: isCurrent ? "2px solid #38bdf8" : isPassed ? "1px solid #10b981" : "1px solid #334155",
                          color: isPassed ? "#34d399" : "#64748b",
                          marginBottom: "4px",
                        }}>
                          {st.icon}
                        </div>
                        <div style={{ fontSize: "0.68rem", fontWeight: isCurrent ? "800" : "600", color: isCurrent ? "#38bdf8" : isPassed ? "#e2e8f0" : "#64748b", textAlign: "center" }}>
                          {st.label}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Anonymous Report Notice */}
              {selectedTicket.is_anonymous && (
                <div style={{ background: "rgba(124, 58, 237, 0.12)", border: "1px solid #7c3aed", borderRadius: "8px", padding: "10px 14px", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "1.25rem" }}>🔒</span>
                  <div style={{ fontSize: "0.82rem", color: "#e9d5ff", lineHeight: "1.4" }}>
                    <strong>Protected Anonymous Near-Miss:</strong> Attributed to Shift {selectedTicket.shift || "General"} & Zone {selectedTicket.zone_id || "Plant"}. Reporter identity is strictly unrecorded.
                  </div>
                </div>
              )}

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
                    <strong>Employee / Badge:</strong> {selectedTicket.is_anonymous ? "🔒 Protected (Anonymous)" : (selectedTicket.worker_badge_id || selectedTicket.employee_id || "Not Provided")}
                  </div>
                  <div>
                    <strong>Reporting Mode:</strong>{" "}
                    <span style={{
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontSize: "0.75rem",
                      fontWeight: "700",
                      background: selectedTicket.reporting_mode === "kiosk" ? "rgba(56, 189, 248, 0.2)" : selectedTicket.reporting_mode === "supervisor_proxy" ? "rgba(245, 158, 11, 0.2)" : "rgba(100, 116, 139, 0.2)",
                      color: selectedTicket.reporting_mode === "kiosk" ? "#38bdf8" : selectedTicket.reporting_mode === "supervisor_proxy" ? "#f59e0b" : "#cbd5e1",
                    }}>
                      {selectedTicket.reporting_mode === "kiosk" ? `🏢 Kiosk (${selectedTicket.kiosk_station_id || "Station"})` : selectedTicket.reporting_mode === "supervisor_proxy" ? `🛡️ Supervisor Proxy (${selectedTicket.reporter_supervisor_id || "Supervisor"})` : selectedTicket.is_anonymous ? "🔒 Anonymous Near-Miss" : "📱 Personal Device"}
                    </span>
                  </div>
                  <div>
                    <strong>Language:</strong> {LANGUAGE_NAMES[selectedTicket.language] || selectedTicket.language?.toUpperCase()}{" "}
                    {selectedTicket.language_confidence && `(${Math.round(selectedTicket.language_confidence * 100)}%)`}
                  </div>
                  <div>
                    <strong>Reported Zone:</strong> {selectedTicket.zone_id || "Unspecified"}
                  </div>
                  {selectedTicket.shift && (
                    <div>
                      <strong>Operational Shift:</strong> {selectedTicket.shift}
                    </div>
                  )}
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
                        </div>
                      </div>
                    )}
                  </div>
                );
              })() : null}

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

              {/* Phase 7: Indicative Spatial Footprint & Simple Plant Map (Advisory) */}
              <div className="inspector-section" style={{ marginTop: "1rem" }}>
                <PlantMap
                  incidentZoneId={selectedTicket.zone_id}
                  impactAssessment={selectedTicket.impact_assessment}
                  plantId={selectedTicket.plant_id || "bsl_bokaro"}
                />
              </div>

              {/* Phase 6: Supervisor & Safety Officer Corrective Action Workflow */}
              <div className="inspector-section" style={{ background: "#0b1528", border: "1.5px solid #38bdf8", borderRadius: "8px", padding: "1rem" }}>
                <h4 style={{ color: "#38bdf8", margin: "0 0 0.5rem 0" }}>🛠️ Corrective Action Assignment</h4>
                <p style={{ fontSize: "0.8rem", color: "#94a3b8", margin: "0 0 1rem 0" }}>
                  Assign physical remediation work order with owner and due date. Never leave reports in a black hole.
                </p>

                <form onSubmit={handleAssignAction}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
                    <div>
                      <label style={{ fontSize: "0.75rem", color: "#cbd5e1", fontWeight: "700", display: "block", marginBottom: "4px" }}>
                        Assigned Remediator / Maintenance Team:
                      </label>
                      <input
                        type="text"
                        style={{ width: "100%", padding: "8px", background: "#070d18", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem" }}
                        placeholder="e.g. Mechanical Maint Team B / A. Verma"
                        value={assignedTo}
                        onChange={(e) => setAssignedTo(e.target.value)}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: "0.75rem", color: "#cbd5e1", fontWeight: "700", display: "block", marginBottom: "4px" }}>
                        Remediation Due Date:
                      </label>
                      <input
                        type="date"
                        style={{ width: "100%", padding: "8px", background: "#070d18", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem" }}
                        value={dueDate}
                        onChange={(e) => setDueDate(e.target.value)}
                      />
                    </div>
                  </div>

                  <div style={{ marginBottom: "10px" }}>
                    <label style={{ fontSize: "0.75rem", color: "#cbd5e1", fontWeight: "700", display: "block", marginBottom: "4px" }}>
                      Corrective Action Task Description:
                    </label>
                    <textarea
                      rows={2}
                      style={{ width: "100%", padding: "8px", background: "#070d18", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem" }}
                      placeholder="e.g. Replace damaged hydraulic valve seal and test line pressure under LOTO."
                      value={correctiveAction}
                      onChange={(e) => setCorrectiveAction(e.target.value)}
                    />
                  </div>

                  <button
                    type="submit"
                    style={{ background: "#38bdf8", color: "#070d18", fontWeight: "800", padding: "8px 16px", borderRadius: "6px", border: "none", cursor: "pointer" }}
                    disabled={actionLoading}
                  >
                    {actionLoading ? "Assigning..." : "Assign Corrective Action"}
                  </button>
                </form>

                {/* Verification & Closure SLA Section */}
                <div style={{ marginTop: "1.25rem", borderTop: "1px solid #1e293b", paddingTop: "1rem" }}>
                  <h4 style={{ color: "#34d399", margin: "0 0 0.5rem 0" }}>✅ Hazard Verification & Closure</h4>
                  {selectedTicket.closure_notes ? (
                    <div style={{ background: "rgba(16, 185, 129, 0.12)", border: "1px solid #10b981", borderRadius: "6px", padding: "10px", marginTop: "8px" }}>
                      <strong style={{ color: "#10b981", fontSize: "0.85rem" }}>Permanently Resolved:</strong>
                      <p style={{ margin: "4px 0 0 0", color: "#e2e8f0", fontSize: "0.85rem" }}>{selectedTicket.closure_notes}</p>
                      {selectedTicket.closure_time_hours != null && (
                        <div style={{ marginTop: "6px", color: "#34d399", fontWeight: "800", fontSize: "0.8rem" }}>
                          ⚡ Turnaround SLA: Resolved in {selectedTicket.closure_time_hours} hours from report intake
                        </div>
                      )}
                    </div>
                  ) : (
                    <form onSubmit={handleCloseAction}>
                      <div style={{ marginBottom: "10px" }}>
                        <label style={{ fontSize: "0.75rem", color: "#cbd5e1", fontWeight: "700", display: "block", marginBottom: "4px" }}>
                          Verification Notes & Resolution Evidence:
                        </label>
                        <textarea
                          rows={2}
                          style={{ width: "100%", padding: "8px", background: "#070d18", border: "1px solid #334155", borderRadius: "6px", color: "#fff", fontSize: "0.85rem" }}
                          placeholder="e.g. Work Order #WO-8891 complete. Valve replaced and pressure test passed at 14:30."
                          value={closureNotes}
                          onChange={(e) => setClosureNotes(e.target.value)}
                        />
                      </div>
                      <button
                        type="submit"
                        style={{ background: "#10b981", color: "#070d18", fontWeight: "800", padding: "8px 16px", borderRadius: "6px", border: "none", cursor: "pointer" }}
                        disabled={actionLoading}
                      >
                        {actionLoading ? "Closing..." : "Verify & Close Hazard"}
                      </button>
                    </form>
                  )}
                  {actionMsg && (
                    <div style={{ marginTop: "8px", color: "#38bdf8", fontSize: "0.85rem", fontWeight: "700" }}>
                      ✓ {actionMsg}
                    </div>
                  )}
                </div>
              </div>

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
                  </div>
                </div>
              )}

              {/* Resolution & Officer Actions */}
              <div className="inspector-section resolution-section">
                <h4>Safety Officer Actions & Routing</h4>
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
