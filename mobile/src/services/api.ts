import { getApiBaseUrl } from './config';
import * as FileSystem from 'expo-file-system/legacy';

export interface Ticket {
  id: string;
  report_type: 'suspected' | 'emergency';
  incident_description: string;
  incident_description_en?: string;
  language?: string;
  language_confidence?: number;
  predicted_category?: string;
  category_confidence?: number;
  photo_proof_path?: string;
  photo_url?: string;
  media_url?: string;
  media_type?: 'image' | 'video';
  requires_photo_proof?: boolean;
  zone_id?: string;
  reporting_mode?: string;
  reporter_supervisor_id?: string;
  worker_badge_id?: string;
  kiosk_station_id?: string;
  clarification_prompt?: string;
  needs_clarification?: boolean;
  verification_questions?: string[];
  verification_answers?: string[];
  verification_answers_en?: string[];
  verification_status?: string;
  verification_score?: number;
  routing_tier?: string;
  risk_score?: number;
  safety_report?: any;
  guidance_text?: string;
  guidance_text_native?: string;
  guidance_audio_path?: string;
  precautionary_measures?: any;
  flagged_for_human_review?: boolean;
  review_reason?: string;
  sop_gap_detected?: boolean;
  severity_factors?: any;
  ai_audit_trail?: any;
  is_anonymous?: boolean;
  shift?: string;
  anonymous_tracking_code?: string;
  lifecycle_stage?: string;
  corrective_action?: string;
  assigned_to?: string;
  due_date?: string;
  closed_at?: string;
  closure_time_hours?: number;
  closure_notes?: string;
  visual_analysis?: {
    detected_event: string;
    confidence: number;
    is_valid_evidence: boolean;
    visual_summary: string;
    visual_status?: string;
    risk_score_impact?: string;
    flagged_for_human_review?: boolean;
    human_review_reason?: string;
    tags?: string[];
    evidence_boxes?: any[];
    advisory_notice?: string;
    probabilities?: Record<string, number>;
  };
  status?: string;
}

export interface NextQuestionResponse {
  done: boolean;
  question: string | null;
  question_index: number | null;
  total_questions: number;
  question_audio_path: string | null;
  options: string[];
  sop_source: string | null;
  is_personalized: boolean;
}

export async function createIncidentFromText(payload: {
  report_type: string;
  incident_description: string;
  language?: string;
  zone_id?: string;
  is_anonymous?: boolean;
  shift?: string;
  worker_badge_id?: string;
  reporter_supervisor_id?: string;
  kiosk_station_id?: string;
  reporting_mode?: string;
  plant_id?: string;
}): Promise<Ticket> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to report incident: ${txt}`);
  }
  return res.json();
}

export async function createIncidentFromAudio(
  audioUri: string,
  reportType: string,
  language?: string,
  extraOptions?: {
    is_anonymous?: boolean;
    shift?: string;
    worker_badge_id?: string;
    reporter_supervisor_id?: string;
    kiosk_station_id?: string;
    reporting_mode?: string;
    zone_id?: string;
    plant_id?: string;
  }
): Promise<Ticket> {
  const base = await getApiBaseUrl();
  const filename = audioUri.split('/').pop() || 'recording.m4a';

  const parameters: Record<string, string> = {
    report_type: reportType,
  };
  if (language) {
    parameters.language = language;
  }
  if (extraOptions?.is_anonymous !== undefined) {
    parameters.is_anonymous = extraOptions.is_anonymous ? 'true' : 'false';
  }
  if (extraOptions?.shift) {
    parameters.shift = extraOptions.shift;
  }
  if (extraOptions?.zone_id) {
    parameters.zone_id = extraOptions.zone_id;
  }
  if (extraOptions?.worker_badge_id) {
    parameters.worker_badge_id = extraOptions.worker_badge_id;
  }
  if (extraOptions?.reporter_supervisor_id) {
    parameters.reporter_supervisor_id = extraOptions.reporter_supervisor_id;
  }
  if (extraOptions?.kiosk_station_id) {
    parameters.kiosk_station_id = extraOptions.kiosk_station_id;
  }
  if (extraOptions?.reporting_mode) {
    parameters.reporting_mode = extraOptions.reporting_mode;
  }
  if (extraOptions?.plant_id) {
    parameters.plant_id = extraOptions.plant_id;
  }

  const response = await FileSystem.uploadAsync(`${base}/incidents/audio`, audioUri, {
    httpMethod: 'POST',
    uploadType: FileSystem.FileSystemUploadType.MULTIPART,
    fieldName: 'file',
    mimeType: 'audio/m4a',
    parameters,
  });

  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Audio upload failed (${response.status}): ${response.body}`);
  }
  return JSON.parse(response.body);
}

export async function uploadTicketMedia(
  ticketId: string,
  mediaUri: string,
  mediaType: 'image' | 'video' = 'image'
): Promise<Ticket> {
  const base = await getApiBaseUrl();
  const mimeType = mediaType === 'video' ? 'video/mp4' : 'image/jpeg';

  const response = await FileSystem.uploadAsync(`${base}/tickets/${ticketId}/photo`, mediaUri, {
    httpMethod: 'POST',
    uploadType: FileSystem.FileSystemUploadType.MULTIPART,
    fieldName: 'file',
    mimeType,
  });

  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Media proof upload failed (${response.status}): ${response.body}`);
  }
  return JSON.parse(response.body);
}

export async function getNextQuestion(ticketId: string, lang?: string): Promise<NextQuestionResponse> {
  const base = await getApiBaseUrl();
  const url = lang
    ? `${base}/verification/${ticketId}/next-question?lang=${encodeURIComponent(lang)}`
    : `${base}/verification/${ticketId}/next-question`;
  const res = await fetch(url);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to fetch next question: ${txt}`);
  }
  return res.json();
}

export async function transcribeAudioFile(
  audioUri: string,
  language?: string
): Promise<{ transcript: string; transcript_en: string; language: string }> {
  const base = await getApiBaseUrl();
  const parameters: Record<string, string> = {};
  if (language) parameters.language = language;

  const response = await FileSystem.uploadAsync(`${base}/transcription`, audioUri, {
    httpMethod: 'POST',
    uploadType: FileSystem.FileSystemUploadType.MULTIPART,
    fieldName: 'file',
    mimeType: 'audio/m4a',
    parameters,
  });

  if (response.status < 200 || response.status >= 300) {
    throw new Error(`Voice transcription failed (${response.status}): ${response.body}`);
  }
  return JSON.parse(response.body);
}

export async function submitVerificationAnswer(
  ticketId: string,
  answerText: string,
  questionText?: string,
  answerTextEn?: string
): Promise<Ticket> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/verification/${ticketId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      answer_text: answerText,
      question_text: questionText,
      answer_text_en: answerTextEn,
    }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to submit answer: ${txt}`);
  }
  return res.json();
}

export async function getTicket(ticketId: string): Promise<Ticket> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/tickets/${ticketId}`);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to fetch ticket: ${txt}`);
  }
  return res.json();
}

export async function synthesizeSpeech(text: string, language: string = 'hi'): Promise<string> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`TTS synthesis failed: ${txt}`);
  }
  const data = await res.json();
  const path = data.audio_path;
  return path.startsWith('http') ? path : `${base}${path}`;
}

export async function getPrecautionaryMeasures(ticketId: string): Promise<any> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/guidance/${ticketId}/precautions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to fetch precautionary measures: ${txt}`);
  }
  return res.json();
}

/**
 * Synchronizes an individual item from the offline outbox queue to the server.
 */
export async function syncQueuedOutboxItem(item: any): Promise<boolean> {
  try {
    if (item.type === 'incident_report') {
      await createIncidentFromText(item.payload);
      return true;
    } else if (item.type === 'incident_audio') {
      await createIncidentFromAudio(
        item.payload.audioUri,
        item.payload.reportType,
        item.payload.language,
        item.payload.extraOptions
      );
      return true;
    } else if (item.type === 'verification_answer') {
      await submitVerificationAnswer(item.payload.ticketId, item.payload.answerText);
      return true;
    } else if (item.type === 'sos_emergency') {
      await createIncidentFromText({
        report_type: 'emergency',
        incident_description: `[OFFLINE SOS EMERGENCY] ${item.payload.description || 'Worker pressed emergency SOS button'}`,
        zone_id: item.payload.zone_id,
        language: item.payload.language || 'hi',
      });
      return true;
    }
    return true;
  } catch (err) {
    console.warn(`[API] Failed to sync outbox item ${item.id}:`, err);
    return false;
  }
}

export interface IncidentTrackerData {
  ticket_id: string;
  plant_id: string;
  anonymous_tracking_code?: string;
  is_anonymous: boolean;
  created_at: string;
  status: string;
  lifecycle_stage: string;
  zone_id?: string;
  shift?: string;
  predicted_category?: string;
  description: string;
  assigned_to?: string;
  corrective_action?: string;
  due_date?: string;
  closed_at?: string;
  closure_time_hours?: number;
  closure_notes?: string;
  history_events: Array<{
    id: string;
    timestamp: string;
    action: string;
    actor_id: string;
    actor_role: string;
    details: any;
  }>;
}

export interface CultureMetricsData {
  plant_id: string;
  total_hazards_fixed: number;
  shift_participation: Array<{
    shift: string;
    count: number;
    resolved: number;
    pct: number;
  }>;
  proactive_near_miss_ratio: number;
  impact_statement_en: string;
  impact_statement_hi: string;
}

export async function getIncidentTracker(identifier: string): Promise<IncidentTrackerData> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/analytics/tracker/${encodeURIComponent(identifier)}`);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Report not found (${res.status}): ${txt}`);
  }
  return res.json();
}

export async function getCultureMetrics(plantId: string = 'bsl_bokaro'): Promise<CultureMetricsData> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/analytics/culture?plant_id=${encodeURIComponent(plantId)}`);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to fetch culture metrics: ${txt}`);
  }
  return res.json();
}

export async function getReportExplainer(): Promise<{
  title_en: string;
  title_hi: string;
  steps: Array<{
    stage: string;
    step_number: number;
    title_en: string;
    title_hi: string;
    description_en: string;
    description_hi: string;
    guarantee_en: string;
    guarantee_hi: string;
  }>;
}> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}/analytics/explainer`);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Failed to fetch explainer: ${txt}`);
  }
  return res.json();
}

