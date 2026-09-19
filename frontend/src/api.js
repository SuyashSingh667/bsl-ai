const BASE = "http://127.0.0.1:8000";

async function json(res) {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json();
}

export function audioUrl(path) {
  if (!path) return null;
  const filename = path.split("/").pop();
  return `${BASE}/audio/${filename}`;
}

export async function createIncidentFromText({ reportType, text, language, zoneId, employeeId }) {
  return json(
    await fetch(`${BASE}/incidents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        report_type: reportType,
        incident_description: text,
        language: language || "en",
        zone_id: zoneId || null,
        employee_id: employeeId || null,
      }),
    })
  );
}

export async function createIncidentFromAudio({ reportType, blob, zoneId, employeeId, language, photo }) {
  const form = new FormData();
  form.append("report_type", reportType);
  form.append("file", blob, "report.webm");
  if (photo) form.append("photo", photo);
  if (zoneId) form.append("zone_id", zoneId);
  if (employeeId) form.append("employee_id", employeeId);
  if (language) form.append("language", language);

  return json(await fetch(`${BASE}/incidents/audio`, { method: "POST", body: form }));
}

export async function transcribeAudio(blob, language) {
  const form = new FormData();
  form.append("file", blob, "answer.webm");
  if (language) form.append("language", language);
  return json(await fetch(`${BASE}/transcription`, { method: "POST", body: form }));
}

export async function getNextQuestion(ticketId, language) {
  const url = language
    ? `${BASE}/verification/${ticketId}/next-question?lang=${encodeURIComponent(language)}`
    : `${BASE}/verification/${ticketId}/next-question`;
  return json(await fetch(url));
}

export async function submitAnswer(ticketId, answerText, answerTextEn, questionText) {
  return json(
    await fetch(`${BASE}/verification/${ticketId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        answer_text: answerText,
        answer_text_en: answerTextEn || null,
        question_text: questionText || null,
      }),
    })
  );
}

export async function finalizeVerification(ticketId) {
  return json(await fetch(`${BASE}/verification/${ticketId}/finalize`, { method: "POST" }));
}

export async function generateGuidance(ticketId) {
  return json(await fetch(`${BASE}/guidance/${ticketId}`, { method: "POST" }));
}

export async function getTicket(ticketId) {
  return json(await fetch(`${BASE}/tickets/${ticketId}`));
}

export async function getTickets({ routingTier, status } = {}) {
  const params = new URLSearchParams();
  if (routingTier && routingTier !== "all") params.append("routing_tier", routingTier);
  if (status && status !== "all") params.append("status", status);
  const qs = params.toString();
  const url = qs ? `${BASE}/tickets?${qs}` : `${BASE}/tickets`;
  return json(await fetch(url));
}

export async function updateTicket(ticketId, updates) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    })
  );
}

export async function getSimilarIncidents(ticketId) {
  return json(await fetch(`${BASE}/tickets/${ticketId}/similar`));
}

export async function getPrecautions(ticketId) {
  return json(await fetch(`${BASE}/guidance/${ticketId}/precautions`));
}

export async function uploadPhotoProof(ticketId, file) {
  const formData = new FormData();
  formData.append("file", file);
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/photo`, {
      method: "POST",
      body: formData,
    })
  );
}

export const uploadMediaProof = uploadPhotoProof;

export function photoUrl(path) {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  if (path.startsWith("/photos/")) {
    return `${BASE}${path}`;
  }
  const filename = path.split("/").pop();
  return `${BASE}/photos/${filename}`;
}

export const mediaUrl = photoUrl;

export async function assignAction(ticketId, { assignedTo, correctiveAction, dueDate }) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/action/assign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assigned_to: assignedTo,
        corrective_action: correctiveAction,
        due_date: dueDate || null,
      }),
    })
  );
}

export async function closeAction(ticketId, { closureNotes, closureEvidencePath }) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/action/close`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        closure_notes: closureNotes,
        closure_evidence_path: closureEvidencePath || null,
      }),
    })
  );
}

export async function getSafetyTrends(plantId = "bsl_bokaro") {
  return json(await fetch(`${BASE}/analytics/trends?plant_id=${encodeURIComponent(plantId)}`));
}

export async function getCultureMetrics(plantId = "bsl_bokaro") {
  return json(await fetch(`${BASE}/analytics/culture?plant_id=${encodeURIComponent(plantId)}`));
}

export async function getIncidentTracker(identifier) {
  return json(await fetch(`${BASE}/analytics/tracker/${encodeURIComponent(identifier)}`));
}

export async function acknowledgeDispatch(ticketId, { acknowledgedBy, notes }) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/dispatch/ack`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        acknowledged_by: acknowledgedBy,
        notes: notes || null,
      }),
    })
  );
}

export async function markOnSite(ticketId, { onSiteBy, notes }) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/dispatch/on-site`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        on_site_by: onSiteBy,
        notes: notes || null,
      }),
    })
  );
}

export async function checkAllDispatches(timeoutSeconds = 60) {
  return json(
    await fetch(`${BASE}/tickets/dispatch/check-all?ack_timeout_seconds=${timeoutSeconds}`, {
      method: "POST",
    })
  );
}

export async function getSpatialHazardBands() {
  return json(await fetch(`${BASE}/admin/spatial/hazard-bands`));
}

export async function updateSpatialHazardBands(bands) {
  return json(
    await fetch(`${BASE}/admin/spatial/hazard-bands`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bands }),
    })
  );
}

export function getPdfDossierUrl(ticketId) {
  return `${BASE}/tickets/${ticketId}/export/pdf`;
}

export async function getPlantDetails(plantId = "bsl_bokaro") {
  return json(await fetch(`${BASE}/admin/plants/${encodeURIComponent(plantId)}`));
}

// ── Phase 8: Operational Metrics, False Alarm, Offline Sync ──────────────────

export async function getOperationalMetrics(plantId = "bsl_bokaro", windowDays = null) {
  const params = new URLSearchParams({ plant_id: plantId });
  if (windowDays !== null) params.append("window_days", windowDays);
  return json(await fetch(`${BASE}/analytics/operational-metrics?${params}`));
}

export async function markTicketFalseAlarm(ticketId, notes = null) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/mark-false-alarm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes }),
    })
  );
}

export async function markTicketCompletedOffline(ticketId) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/mark-completed-offline`, { method: "POST" })
  );
}

export async function seedDemoData(plantId = "bsl_bokaro") {
  return json(
    await fetch(`${BASE}/admin/demo/seed?plant_id=${encodeURIComponent(plantId)}`, {
      method: "POST",
    })
  );
}

export async function clearDemoData(plantId = "bsl_bokaro") {
  return json(
    await fetch(`${BASE}/admin/demo/clear?plant_id=${encodeURIComponent(plantId)}`, {
      method: "DELETE",
    })
  );
}

// ── Phase 5: RAG Question Rating & Feedback ──────────────────────────────────

export async function rateVerificationQuestion(ticketId, { questionText, targetSlot, rating, feedbackNotes, officerId }) {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/rate-question`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_text: questionText,
        target_slot: targetSlot || null,
        rating: rating,
        feedback_notes: feedbackNotes || null,
        officer_id: officerId || "SAFETY_OFFICER",
      }),
    })
  );
}

export async function exportRatedQuestions(plantId = "bsl_bokaro") {
  return json(await fetch(`${BASE}/tickets/export/rated-questions?plant_id=${encodeURIComponent(plantId)}`));
}

