import { useCallback, useEffect, useRef, useState } from "react";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import {
  audioUrl,
  finalizeVerification,
  getNextQuestion,
  getTicket,
  submitAnswer,
  transcribeAudio,
  updateTicket,
} from "../api";

const LANGUAGE_NAMES = {
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
  en: "English",
};

export default function VerificationInterview({ ticketId, onComplete, onRetry }) {
  const { isRecording, error: recError, start, stop } = useAudioRecorder();
  const [ticket, setTicket] = useState(null);
  const [question, setQuestion] = useState(null);
  const [progress, setProgress] = useState({ index: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [textAnswer, setTextAnswer] = useState("");
  const [useText, setUseText] = useState(false);
  const [error, setError] = useState(null);
  const [uncategorized, setUncategorized] = useState(false);
  const [isAudioSpeaking, setIsAudioSpeaking] = useState(false);
  const [autoPlayBlocked, setAutoPlayBlocked] = useState(false);

  const audioRef = useRef(null);
  const autoRecordTimerRef = useRef(null);
  const handledTurnKeyRef = useRef(null);
  const isFetchingRef = useRef(false);

  const isRecordingRef = useRef(false);
  isRecordingRef.current = isRecording;

  const submittingRef = useRef(false);
  submittingRef.current = submitting;

  const useTextRef = useRef(false);
  useTextRef.current = useText;

  const currentTurnKey = question ? `${ticketId}_${question.question_index}` : null;

  const loadNextQuestion = useCallback(async (langOverride) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    setLoading(true);
    setError(null);
    setUncategorized(false);
    setIsAudioSpeaking(false);
    setAutoPlayBlocked(false);
    clearTimeout(autoRecordTimerRef.current);

    try {
      const t = await getTicket(ticketId);
      setTicket(t);

      const targetLang = langOverride || t.language;
      const nq = await getNextQuestion(ticketId, targetLang);
      if (nq.done) {
        onComplete();
        return;
      }
      setQuestion(nq);
      setProgress({ index: (nq.question_index ?? 0) + 1, total: nq.total_questions || 1 });
    } catch (err) {
      if (err.message.includes("incident category could not be determined")) {
        setUncategorized(true);
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, [ticketId, onComplete]);

  useEffect(() => {
    loadNextQuestion();
  }, [loadNextQuestion]);

  async function handleLanguageChange(newLang) {
    if (!newLang || newLang === ticket?.language) return;
    try {
      handledTurnKeyRef.current = null;
      setAutoPlayBlocked(false);
      await updateTicket(ticketId, { language: newLang });
      await loadNextQuestion(newLang);
    } catch (err) {
      setError(err.message);
    }
  }

  function handlePlayAudio() {
    setAutoPlayBlocked(false);
    setIsAudioSpeaking(true);
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch((err) => {
        console.warn("Audio play error:", err);
        setIsAudioSpeaking(false);
      });
    }
  }

  // Hands-free voice flow: Play question audio once per question turn, then automatically activate recording
  useEffect(() => {
    if (!question || !currentTurnKey || useText) return;

    // Prevent duplicate restart triggers for the same question
    if (handledTurnKeyRef.current === currentTurnKey) {
      return;
    }
    handledTurnKeyRef.current = currentTurnKey;

    clearTimeout(autoRecordTimerRef.current);

    const audioEl = audioRef.current;
    if (question.question_audio_path && audioEl) {
      audioEl.currentTime = 0;
      setIsAudioSpeaking(true);
      setAutoPlayBlocked(false);
      const playPromise = audioEl.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            setIsAudioSpeaking(true);
            setAutoPlayBlocked(false);
          })
          .catch((err) => {
            console.warn("Audio autoplay blocked by browser policy:", err);
            setIsAudioSpeaking(false);
            setAutoPlayBlocked(true);
            // Crucial: DO NOT auto-record on timeout here — allows worker to click play without cutting off
          });
      }
    } else {
      setIsAudioSpeaking(false);
    }

    return () => {
      clearTimeout(autoRecordTimerRef.current);
    };
  }, [currentTurnKey, question?.question_audio_path, useText]);

  async function submitAnswerText(text, textEn) {
    if (!text || !text.trim()) {
      setError("Please provide an answer, select a quick option, or speak clearly.");
      setSubmitting(false);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitAnswer(ticketId, text.trim(), textEn ? textEn.trim() : null, question?.question || null);
      setTextAnswer("");
      await loadNextQuestion();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDone() {
    setSubmitting(true);
    setError(null);
    try {
      const blob = await stop();
      if (!blob || blob.size < 1000) {
        setError("Recording was too short (under 1 second). Please speak clearly or choose a quick option below.");
        setSubmitting(false);
        return;
      }
      const res = await transcribeAudio(blob, ticket?.language);
      const transcript = res?.transcript?.trim();
      const transcriptEn = res?.transcript_en?.trim();
      if (!transcript) {
        setError("No clear speech detected. Please speak again, or tap a quick option below.");
        setSubmitting(false);
        return;
      }
      await submitAnswerText(transcript, transcriptEn);
    } catch (err) {
      setError(err.message || "Failed to process audio recording.");
      setSubmitting(false);
    }
  }

  function handleInstantStart() {
    clearTimeout(autoRecordTimerRef.current);
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setIsAudioSpeaking(false);
    if (!isRecordingRef.current && !submittingRef.current) {
      start();
    }
  }

  async function handleFinishEarly() {
    if (isRecording) {
      await stop();
    }
    setSubmitting(true);
    setError(null);
    try {
      await finalizeVerification(ticketId);
      onComplete();
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  if (loading && !question && !uncategorized) {
    return (
      <div className="screen">
        <p>Loading question…</p>
      </div>
    );
  }

  if (uncategorized) {
    return (
      <div className="screen">
        <h1>Couldn't Identify Incident Type</h1>
        <p className="subtitle">
          {ticket
            ? `Captured: "${ticket.incident_description}"`
            : "The report wasn't clear enough to classify."}
        </p>
        <p>This can happen if the recording was unclear or too short. Please try reporting again with a bit more detail.</p>
        <button className="submit-btn" onClick={onRetry}>
          Report Again
        </button>
      </div>
    );
  }

  const answeredCount = ticket?.verification_answers?.length || 0;
  const langDisplay = LANGUAGE_NAMES[ticket?.language] || ticket?.language?.toUpperCase() || "Universal";

  return (
    <div className="screen verification-screen">
      {/* 4-Step Progress Stepper */}
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
        <div className="step-node step-active">
          <span className="step-num">3</span>
          <span className="step-title">3. Safety Questions</span>
        </div>
        <div className="step-connector"></div>
        <div className="step-node step-pending">
          <span className="step-num">4</span>
          <span className="step-title">4. Precautions & Report</span>
        </div>
      </div>

      <div className="interview-lang-bar">
        <label htmlFor="interview-lang-select" className="lang-label">
          🌐 Question Language:
        </label>
        <select
          id="interview-lang-select"
          className="lang-select-pill"
          value={ticket?.language || "en"}
          onChange={(e) => handleLanguageChange(e.target.value)}
          disabled={submitting || isRecording}
        >
          {Object.entries(LANGUAGE_NAMES).map(([code, name]) => (
            <option key={code} value={code}>
              {name}
            </option>
          ))}
        </select>
        <span className="lang-hint">Switch anytime to hear in your language</span>
      </div>

      <h1>Verification Interview</h1>
      {ticket && (
        <p className="subtitle">
          Reported: "{ticket.incident_description}" — identified as{" "}
          <strong>{ticket.predicted_category?.replaceAll("_", " ")}</strong> (
          {Math.round((ticket.category_confidence || 0) * 100)}% confidence)
        </p>
      )}
      <p className="subtitle">
        Question {progress.index} of {progress.total}
      </p>

      {question && (
        <div className="question-card">
          {question.is_personalized && (
            <div className="sop-grounded-badge">
              <span>🛡️</span>
              <span>
                <strong>BSL Procedure Guideline</strong> · {(question.sop_source || "BSL Safety SOP").replace(/—\s*Extracted Reference/gi, "").trim()}
              </span>
            </div>
          )}
          <p className="question-text">{question.question}</p>
          {question.question_audio_path && (
            <audio
              ref={audioRef}
              controls
              preload="auto"
              src={audioUrl(question.question_audio_path)}
              onPlay={() => {
                setIsAudioSpeaking(true);
                setAutoPlayBlocked(false);
              }}
              onPause={() => {
                setIsAudioSpeaking(false);
              }}
              onEnded={() => {
                setIsAudioSpeaking(false);
                if (!isRecordingRef.current && !submittingRef.current && !useTextRef.current) {
                  start();
                }
              }}
              onError={() => {
                setIsAudioSpeaking(false);
              }}
            />
          )}

          {/* Autoplay fallback prompt if browser blocked autoplay */}
          {autoPlayBlocked && !isAudioSpeaking && !useText && (
            <div className="autoplay-prompt-banner">
              <button
                type="button"
                className="play-question-btn"
                onClick={handlePlayAudio}
              >
                🔊 Tap to Listen to Question
              </button>
              <button
                type="button"
                className="instant-start-btn"
                onClick={() => {
                  setAutoPlayBlocked(false);
                  if (!isRecordingRef.current && !submittingRef.current) {
                    start();
                  }
                }}
              >
                🎙️ Speak Answer Directly →
              </button>
            </div>
          )}

          {/* Audio Speaking Banner with skip-to-record button */}
          {isAudioSpeaking && !useText && (
            <div className="audio-speaking-banner">
              <div className="speaking-text-group">
                <span className="speaking-icon">🔊</span>
                <span>
                  Asking question... (Microphone will automatically start when speaking completes)
                </span>
              </div>
              <button
                type="button"
                className="instant-start-btn"
                onClick={handleInstantStart}
              >
                Record now →
              </button>
            </div>
          )}

          {/* Quick Option Chips */}
          {question.options?.length > 0 && (
            <div className="quick-options-container">
              <span className="quick-options-label">
                ⚡ Quick Answer Options (or speak below in your language):
              </span>
              <div className="quick-options-grid">
                {question.options.map((opt, i) => (
                  <button
                    key={i}
                    type="button"
                    className="chip-btn"
                    onClick={() => {
                      if (audioRef.current) audioRef.current.pause();
                      submitAnswerText(opt);
                    }}
                    disabled={submitting}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Hands-free Voice Recording Panel */}
      {!useText && (
        <div>
          {isRecording ? (
            <div className="handsfree-recording-panel">
              <div className="live-mic-badge">
                <span className="live-dot"></span>
                <span>
                  🔴 Microphone LIVE — speak your answer in your language, then tap Stop below
                </span>
              </div>
              <button
                type="button"
                className="big-stop-btn"
                onClick={handleDone}
                disabled={submitting}
              >
                ⏹ Stop Recording & Submit Answer
              </button>
              <button
                type="button"
                className="link-btn"
                onClick={() => {
                  stop();
                  setUseText(true);
                }}
                disabled={submitting}
              >
                Type text instead
              </button>
            </div>
          ) : (
            <div className="recorder-panel">
              {submitting ? (
                <p className="status-text">
                  Processing your answer…
                </p>
              ) : (
                <>
                  {!isAudioSpeaking && (
                    <button
                      type="button"
                      className="record-btn"
                      onClick={() => {
                        start();
                      }}
                      disabled={submitting}
                    >
                      🎙 Record Answer
                    </button>
                  )}
                  <button
                    type="button"
                    className="link-btn"
                    onClick={() => setUseText(true)}
                    disabled={submitting}
                  >
                    Type text instead
                  </button>
                </>
              )}
            </div>
          )}

          {recError && <p className="error-text">{recError}</p>}
        </div>
      )}

      {/* Text Typing Panel */}
      {useText && (
        <div className="text-panel">
          <textarea
            value={textAnswer}
            onChange={(e) => setTextAnswer(e.target.value)}
            placeholder="Type your answer here in any language..."
            rows={3}
            disabled={submitting}
          />
          <button
            className="submit-btn"
            onClick={() => submitAnswerText(textAnswer)}
            disabled={submitting || !textAnswer.trim()}
          >
            {submitting ? "Submitting…" : "Submit Answer"}
          </button>
          <button
            className="link-btn"
            onClick={() => setUseText(false)}
            disabled={submitting}
          >
            Use voice instead
          </button>
        </div>
      )}

      {/* Auxiliary Actions: Skip or Finish Early */}
      <div className="interview-footer-actions">
        <button
          className="link-btn skip-btn"
          onClick={() => submitAnswerText("Not sure / skipped")}
          disabled={submitting || isRecording}
        >
          Skip this question →
        </button>
        {answeredCount >= 1 && (
          <button
            className="finish-early-btn"
            onClick={handleFinishEarly}
            disabled={submitting || isRecording}
          >
            ✓ Complete & Generate Report Now
          </button>
        )}
      </div>

      {error && <p className="error-text error-banner">{error}</p>}
    </div>
  );
}
