import { getApiBaseUrl } from './config';
import * as FileSystem from 'expo-file-system/legacy';

export interface Ticket {
  id: string;
  report_type: 'suspected' | 'emergency';
  incident_description: string;
  incident_description_en?: string;
  language?: string;
  predicted_category?: string;
  category_confidence?: number;
  photo_proof_path?: string;
  photo_url?: string;
  media_url?: string;
  media_type?: 'image' | 'video';
  requires_photo_proof?: boolean;
  zone_id?: string;
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
  language?: string
): Promise<Ticket> {
  const base = await getApiBaseUrl();
  const filename = audioUri.split('/').pop() || 'recording.m4a';

  const parameters: Record<string, string> = {
    report_type: reportType,
  };
  if (language) {
    parameters.language = language;
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

