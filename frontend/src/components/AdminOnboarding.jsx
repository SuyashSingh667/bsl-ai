import React, { useState, useEffect } from "react";

export default function AdminOnboarding({ activePlantId, onSelectPlant }) {
  const [plants, setPlants] = useState([]);
  const [selectedPlant, setSelectedPlant] = useState(activePlantId || "bsl_bokaro");
  const [plantDetail, setPlantDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview"); // overview | zones | sops | emergency | audit

  // SOP Upload state
  const [sopFile, setSopFile] = useState(null);
  const [sopId, setSopId] = useState("");
  const [sopTitle, setSopTitle] = useState("");
  const [sopVersion, setSopVersion] = useState("1.0");
  const [sopCategories, setSopCategories] = useState("gas_leak, fire");
  const [sopReviewer, setSopReviewer] = useState("Safety Officer Command");
  const [sopUploadStatus, setSopUploadStatus] = useState(null);

  // Audit state
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditVerification, setAuditVerification] = useState(null);

  // New plant JSON modal/state
  const [plantJsonInput, setPlantJsonInput] = useState("");
  const [jsonImportError, setJsonImportError] = useState(null);

  useEffect(() => {
    fetchPlants();
  }, []);

  useEffect(() => {
    if (selectedPlant) {
      fetchPlantDetail(selectedPlant);
      fetchAuditLogs(selectedPlant);
    }
  }, [selectedPlant]);

  async function fetchPlants() {
    try {
      const res = await fetch("/api/admin/plants");
      if (res.ok) {
        const data = await res.json();
        setPlants(data);
        if (!selectedPlant && data.length > 0) {
          setSelectedPlant(data[0].plant_id);
        }
      }
    } catch (err) {
      console.error("Error fetching plants:", err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchPlantDetail(pId) {
    try {
      const res = await fetch(`/api/admin/plants/${pId}`);
      if (res.ok) {
        const data = await res.json();
        setPlantDetail(data);
      }
    } catch (err) {
      console.error("Error fetching plant details:", err);
    }
  }

  async function fetchAuditLogs(pId) {
    try {
      const res = await fetch(`/api/admin/audit-logs?plant_id=${pId}&limit=30`, {
        headers: { "x-user-role": "admin" },
      });
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (err) {
      console.error("Error fetching audit logs:", err);
    }
  }

  async function handleVerifyLedger() {
    try {
      const res = await fetch(`/api/admin/audit-logs/verify?plant_id=${selectedPlant}`, {
        headers: { "x-user-role": "admin" },
      });
      if (res.ok) {
        const data = await res.json();
        setAuditVerification(data);
      }
    } catch (err) {
      console.error("Error verifying audit ledger:", err);
    }
  }

  async function handleUploadSop(e) {
    e.preventDefault();
    if (!sopFile || !sopId || !sopTitle) {
      alert("Please select a file and provide SOP ID and Title.");
      return;
    }

    const formData = new FormData();
    formData.append("file", sopFile);
    formData.append("sop_id", sopId);
    formData.append("title", sopTitle);
    formData.append("version", sopVersion);
    formData.append("incident_types", sopCategories);
    formData.append("reviewer", sopReviewer);
    formData.append("reviewed_by_safety_officer", "true");

    try {
      setSopUploadStatus("uploading");
      const res = await fetch(`/api/admin/plants/${selectedPlant}/sops/upload`, {
        method: "POST",
        headers: { "x-user-role": "admin" },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setSopUploadStatus("success");
        alert(`SOP '${data.sop.title}' successfully parsed and indexed! (${data.sop.section_count} sections created)`);
        setSopFile(null);
        setSopId("");
        setSopTitle("");
        fetchAuditLogs(selectedPlant);
      } else {
        setSopUploadStatus("error");
        alert("Failed to upload SOP document.");
      }
    } catch (err) {
      console.error("SOP upload failed:", err);
      setSopUploadStatus("error");
    }
  }

  async function handleImportPlantJson() {
    setJsonImportError(null);
    try {
      const parsed = JSON.parse(plantJsonInput);
      if (!parsed.plant_id) {
        setJsonImportError("JSON must contain a 'plant_id' string.");
        return;
      }
      const res = await fetch("/api/admin/plants", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-user-role": "admin",
        },
        body: JSON.stringify(parsed),
      });

      if (res.ok) {
        alert(`Plant '${parsed.plant_id}' successfully imported!`);
        setPlantJsonInput("");
        fetchPlants();
        setSelectedPlant(parsed.plant_id);
      } else {
        const errData = await res.json();
        setJsonImportError(errData.detail || "Failed to register plant.");
      }
    } catch (e) {
      setJsonImportError("Invalid JSON syntax: " + e.message);
    }
  }

  return (
    <div className="admin-container" style={{ padding: "24px", color: "#e2e8f0" }}>
      {/* Header & Plant Selector */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div>
          <h1 style={{ fontSize: "22px", fontWeight: "800", color: "#f8fafc", margin: 0 }}>
            ⚙️ Plant Administration & Onboarding
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px" }}>
            Configure multi-tenant industrial sites, zones, SOP procedures, emergency dispatch squads, and audit ledgers.
          </p>
        </div>

        {/* Plant Switcher */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <label style={{ fontSize: "12px", color: "#94a3b8", fontWeight: "600" }}>Active Plant Tenant:</label>
          <select
            value={selectedPlant}
            onChange={(e) => {
              setSelectedPlant(e.target.value);
              if (onSelectPlant) onSelectPlant(e.target.value);
            }}
            style={{
              backgroundColor: "#1e293b",
              color: "#38bdf8",
              borderColor: "#334155",
              padding: "8px 14px",
              borderRadius: "8px",
              fontWeight: "700",
              fontSize: "13px",
            }}
          >
            {plants.map((p) => (
              <option key={p.plant_id} value={p.plant_id}>
                {p.short_name} — {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid #334155", paddingBottom: "12px", marginBottom: "20px" }}>
        {[
          { id: "overview", label: "🏭 Plant Overview & Import" },
          { id: "zones", label: `📍 Zones (${plantDetail?.zones?.length || 0})` },
          { id: "sops", label: "📄 SOP Document Ingestion" },
          { id: "emergency", label: `🚨 Emergency Teams (${plantDetail?.emergency_teams?.length || 0})` },
          { id: "audit", label: "🔒 Immutable Audit Ledger" },
          { id: "export", label: "📊 Data Export & Integration" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              fontWeight: "700",
              fontSize: "12px",
              backgroundColor: activeTab === tab.id ? "#38bdf8" : "#1e293b",
              color: activeTab === tab.id ? "#0f172a" : "#94a3b8",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: Plant Overview & JSON Import */}
      {activeTab === "overview" && plantDetail && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <h3 style={{ fontSize: "16px", color: "#f8fafc", marginBottom: "16px" }}>🏭 Active Plant Profile</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px" }}>
              <div><strong style={{ color: "#94a3b8" }}>Tenant ID:</strong> <code>{plantDetail.plant_id}</code></div>
              <div><strong style={{ color: "#94a3b8" }}>Plant Name:</strong> {plantDetail.name} ({plantDetail.short_name})</div>
              <div><strong style={{ color: "#94a3b8" }}>Organization:</strong> {plantDetail.organization || "N/A"}</div>
              <div><strong style={{ color: "#94a3b8" }}>Location:</strong> {plantDetail.location}</div>
              <div><strong style={{ color: "#94a3b8" }}>Emergency Hotline:</strong> <code style={{ color: "#f87171" }}>{plantDetail.emergency_hotline}</code></div>
              <div><strong style={{ color: "#94a3b8" }}>Data Retention:</strong> {plantDetail.data_retention_days || 180} days</div>
              <div><strong style={{ color: "#94a3b8" }}>Critical Pipelines:</strong> {plantDetail.gas_pipelines?.length || 0} networks</div>
              <div><strong style={{ color: "#94a3b8" }}>Substation Transformers:</strong> {plantDetail.transformers?.length || 0} units</div>
            </div>
          </div>

          <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <h3 style={{ fontSize: "16px", color: "#f8fafc", marginBottom: "8px" }}>📥 Onboard New Plant via JSON</h3>
            <p style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "12px" }}>
              Paste a complete plant configuration JSON to add a new industrial site without code modifications.
            </p>
            <textarea
              rows={8}
              value={plantJsonInput}
              onChange={(e) => setPlantJsonInput(e.target.value)}
              placeholder='{"plant_id": "new_site", "name": "New Plant Works", "short_name": "NPW", "emergency_hotline": "+91...", "zones": []}'
              style={{
                width: "100%",
                backgroundColor: "#020617",
                color: "#e2e8f0",
                fontFamily: "monospace",
                fontSize: "11px",
                padding: "10px",
                borderRadius: "8px",
                border: "1px solid #334155",
                marginBottom: "10px",
              }}
            />
            {jsonImportError && <div style={{ color: "#f87171", fontSize: "12px", marginBottom: "8px" }}>⚠️ {jsonImportError}</div>}
            <button
              onClick={handleImportPlantJson}
              style={{
                padding: "10px 18px",
                backgroundColor: "#10b981",
                color: "#0f172a",
                fontWeight: "800",
                fontSize: "13px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
              }}
            >
              ✓ Register & Import Plant
            </button>
          </div>
        </div>
      )}

      {/* TAB 2: Zones */}
      {activeTab === "zones" && plantDetail && (
        <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
          <h3 style={{ fontSize: "16px", color: "#f8fafc", marginBottom: "16px" }}>
            📍 Plant Zones & Hardware Restrictions ({plantDetail.zones?.length || 0})
          </h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
                <th style={{ padding: "8px" }}>Zone ID</th>
                <th style={{ padding: "8px" }}>Name</th>
                <th style={{ padding: "8px" }}>Category</th>
                <th style={{ padding: "8px" }}>Radius</th>
                <th style={{ padding: "8px" }}>Phone Restricted</th>
                <th style={{ padding: "8px" }}>Intrinsically Safe Only</th>
                <th style={{ padding: "8px" }}>Safe Alternative Intercom/Kiosk</th>
              </tr>
            </thead>
            <tbody>
              {plantDetail.zones?.map((z) => (
                <tr key={z.zone_id} style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "10px 8px" }}><code>{z.zone_id}</code></td>
                  <td style={{ padding: "10px 8px", fontWeight: "700" }}>{z.name}</td>
                  <td style={{ padding: "10px 8px" }}>{z.category}</td>
                  <td style={{ padding: "10px 8px" }}>{z.footprint_radius_m}m</td>
                  <td style={{ padding: "10px 8px" }}>
                    {z.phone_restricted ? <span style={{ color: "#f87171" }}>📵 RESTRICTED</span> : <span style={{ color: "#10b981" }}>ALLOW</span>}
                  </td>
                  <td style={{ padding: "10px 8px" }}>
                    {z.intrinsically_safe_only ? <span style={{ color: "#f59e0b" }}>⚡ ATEX/IS</span> : "Standard"}
                  </td>
                  <td style={{ padding: "10px 8px", color: "#94a3b8" }}>{z.safe_alternative || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 3: SOP Ingestion */}
      {activeTab === "sops" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <h3 style={{ fontSize: "16px", color: "#f8fafc", marginBottom: "12px" }}>📄 Upload Approved Plant SOP</h3>
            <p style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "16px" }}>
              Upload standard operating procedures in <strong>DOCX</strong>, <strong>PDF</strong>, <strong>Markdown</strong>, or <strong>TXT</strong>.
              The parser automatically chunks, validates safety review, and embeds into the operational RAG index.
            </p>
            <form onSubmit={handleUploadSop} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "700" }}>SOP Identifier:</label>
                <input
                  type="text"
                  placeholder="e.g. BSL/SOP/GAS-02 or RSP/SOP/FIRE-01"
                  value={sopId}
                  onChange={(e) => setSopId(e.target.value)}
                  style={{ width: "100%", padding: "8px", borderRadius: "6px", backgroundColor: "#020617", color: "#f8fafc", border: "1px solid #334155" }}
                  required
                />
              </div>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "700" }}>Procedure Title:</label>
                <input
                  type="text"
                  placeholder="e.g. Blast Furnace Tuyere Burnout Emergency Response"
                  value={sopTitle}
                  onChange={(e) => setSopTitle(e.target.value)}
                  style={{ width: "100%", padding: "8px", borderRadius: "6px", backgroundColor: "#020617", color: "#f8fafc", border: "1px solid #334155" }}
                  required
                />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "700" }}>Version:</label>
                  <input
                    type="text"
                    value={sopVersion}
                    onChange={(e) => setSopVersion(e.target.value)}
                    style={{ width: "100%", padding: "8px", borderRadius: "6px", backgroundColor: "#020617", color: "#f8fafc", border: "1px solid #334155" }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "700" }}>Reviewer:</label>
                  <input
                    type="text"
                    value={sopReviewer}
                    onChange={(e) => setSopReviewer(e.target.value)}
                    style={{ width: "100%", padding: "8px", borderRadius: "6px", backgroundColor: "#020617", color: "#f8fafc", border: "1px solid #334155" }}
                  />
                </div>
              </div>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "700" }}>Incident Categories (comma-separated):</label>
                <input
                  type="text"
                  value={sopCategories}
                  onChange={(e) => setSopCategories(e.target.value)}
                  style={{ width: "100%", padding: "8px", borderRadius: "6px", backgroundColor: "#020617", color: "#f8fafc", border: "1px solid #334155" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "700" }}>Select Document File (.docx, .pdf, .md, .txt):</label>
                <input
                  type="file"
                  accept=".docx,.pdf,.md,.txt"
                  onChange={(e) => setSopFile(e.target.files[0])}
                  style={{ marginTop: "4px", color: "#94a3b8", fontSize: "12px" }}
                  required
                />
              </div>
              <button
                type="submit"
                style={{
                  marginTop: "8px",
                  padding: "10px",
                  backgroundColor: "#38bdf8",
                  color: "#0f172a",
                  fontWeight: "800",
                  borderRadius: "8px",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                {sopUploadStatus === "uploading" ? "Parsing & Embedding..." : "Upload & Ingest into RAG"}
              </button>
            </form>
          </div>

          <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <h3 style={{ fontSize: "16px", color: "#f8fafc", marginBottom: "12px" }}>🛡️ Strict Governance Invariants</h3>
            <ul style={{ fontSize: "12px", color: "#94a3b8", lineHeight: "1.8", paddingLeft: "18px" }}>
              <li><strong>Zero-Hallucination Policy:</strong> RAG retrieval operates exclusively on approved procedures. LLMs are prohibited from inventing safety steps.</li>
              <li><strong>Mandatory Safety Review:</strong> Procedures missing <code>reviewed_by_safety_officer: true</code> are blocked by RAG indexers.</li>
              <li><strong>Tenant Scoping:</strong> Ingested procedures are mapped specifically to tenant <code>{selectedPlant}</code>.</li>
              <li><strong>Native Standard Library Parsing:</strong> DOCX archives are parsed natively with zero external dependencies.</li>
            </ul>
          </div>
        </div>
      )}

      {/* TAB 4: Emergency Teams */}
      {activeTab === "emergency" && plantDetail && (
        <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
          <h3 style={{ fontSize: "16px", color: "#f8fafc", marginBottom: "16px" }}>
            🚨 Emergency Response Squads ({plantDetail.emergency_teams?.length || 0})
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
            {plantDetail.emergency_teams?.map((team) => (
              <div key={team.team_id} style={{ backgroundColor: "#020617", padding: "16px", borderRadius: "10px", border: "1px solid #334155" }}>
                <h4 style={{ color: "#38bdf8", fontSize: "14px", margin: "0 0 8px 0" }}>{team.name}</h4>
                <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.6" }}>
                  <div>📞 <strong>Phone:</strong> {team.phone}</div>
                  <div>💬 <strong>SMS:</strong> {team.sms || "Same"}</div>
                  <div>📱 <strong>WhatsApp:</strong> {team.whatsapp || "None"}</div>
                  <div>📻 <strong>Radio Channel:</strong> {team.radio_channel || "VHF Primary"}</div>
                  <div style={{ marginTop: "6px" }}>
                    <span style={{ fontSize: "10px", padding: "2px 6px", backgroundColor: "#1e293b", borderRadius: "4px", color: "#94a3b8" }}>
                      Zones: {team.coverage_zones?.join(", ")}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: Immutable Audit Ledger */}
      {activeTab === "audit" && (
        <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h3 style={{ fontSize: "16px", color: "#f8fafc", margin: 0 }}>🔒 Immutable SHA-256 Audit Ledger</h3>
              <p style={{ fontSize: "12px", color: "#94a3b8", margin: "4px 0 0 0" }}>
                Cryptographically backlinked event chain for legal, statutory, and factory inspectorate compliance.
              </p>
            </div>
            <button
              onClick={handleVerifyLedger}
              style={{
                padding: "8px 16px",
                backgroundColor: "#10b981",
                color: "#0f172a",
                fontWeight: "800",
                fontSize: "12px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
              }}
            >
              🛡️ Verify Ledger Integrity
            </button>
          </div>

          {auditVerification && (
            <div
              style={{
                padding: "12px",
                borderRadius: "8px",
                marginBottom: "16px",
                backgroundColor: auditVerification.is_valid ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
                border: `1px solid ${auditVerification.is_valid ? "#10b981" : "#ef4444"}`,
                fontSize: "12px",
              }}
            >
              {auditVerification.is_valid ? (
                <span style={{ color: "#10b981", fontWeight: "700" }}>
                  ✅ Cryptographic Chain Intact: Verified {auditVerification.records_verified} sequential events. Zero tampering detected.
                </span>
              ) : (
                <span style={{ color: "#ef4444", fontWeight: "700" }}>
                  ❌ TAMPERING DETECTED: {auditVerification.error_details}
                </span>
              )}
            </div>
          )}

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
                <th style={{ padding: "6px" }}>Timestamp (UTC)</th>
                <th style={{ padding: "6px" }}>Actor</th>
                <th style={{ padding: "6px" }}>Action</th>
                <th style={{ padding: "6px" }}>Ticket ID</th>
                <th style={{ padding: "6px" }}>SHA-256 Hash</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id} style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "8px 6px", color: "#94a3b8" }}>{new Date(log.created_at).toLocaleString()}</td>
                  <td style={{ padding: "8px 6px" }}><strong>{log.actor_id}</strong> ({log.actor_role})</td>
                  <td style={{ padding: "8px 6px" }}><code style={{ color: "#38bdf8" }}>{log.action}</code></td>
                  <td style={{ padding: "8px 6px" }}>{log.ticket_id || "—"}</td>
                  <td style={{ padding: "8px 6px" }}><code style={{ fontSize: "10px", color: "#64748b" }}>{log.entry_hash?.slice(0, 16)}...</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 6: Data Export & Integration */}
      {activeTab === "export" && (
        <div style={{ backgroundColor: "#0f172a", padding: "20px", borderRadius: "12px", border: "1px solid #1e293b" }}>
          <h3 style={{ fontSize: "16px", color: "#f8fafc", marginBottom: "8px" }}>📊 Data Export & Enterprise Integrations</h3>
          <p style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "20px" }}>
            Export safety incident datasets compatible with SAP EHS, Enablon, Cority, or corporate business intelligence systems.
          </p>

          <div style={{ display: "flex", gap: "16px" }}>
            <a
              href={`/api/integrations/export/csv?plant_id=${selectedPlant}`}
              download
              style={{
                padding: "12px 20px",
                backgroundColor: "#38bdf8",
                color: "#0f172a",
                fontWeight: "800",
                fontSize: "13px",
                borderRadius: "8px",
                textDecoration: "none",
                display: "inline-block",
              }}
            >
              📥 Download CSV Export (SAP EHS Schema)
            </a>

            <a
              href={`/api/integrations/export/json?plant_id=${selectedPlant}`}
              download
              style={{
                padding: "12px 20px",
                backgroundColor: "#1e293b",
                color: "#f8fafc",
                fontWeight: "800",
                fontSize: "13px",
                borderRadius: "8px",
                textDecoration: "none",
                display: "inline-block",
                border: "1px solid #334155",
              }}
            >
              📥 Download Complete JSON Dataset
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
