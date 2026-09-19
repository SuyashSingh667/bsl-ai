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
