import { useState } from "react";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { createIncidentFromAudio, createIncidentFromText } from "../api";

const INTAKE_LANGUAGES = [
  { code: "hi", label: "हिन्दी (Hindi)" },
  { code: "en", label: "English" },
  { code: "bn", label: "বাংলা (Bengali)" },
  { code: "ta", label: "தமிழ் (Tamil)" },
  { code: "te", label: "తెలుగు (Telugu)" },
  { code: "mr", label: "मराठी (Marathi)" },
  { code: "gu", label: "ગુજરાતી (Gujarati)" },
  { code: "kn", label: "ಕನ್ನಡ (Kannada)" },
  { code: "ml", label: "മലയാളം (Malayalam)" },
  { code: "pa", label: "ਪੰਜਾਬੀ (Punjabi)" },
  { code: "or", label: "ଓଡ଼ିଆ (Odia)" },
];

export default function IncidentRecorder({ reportType, onCreated }) {
  const { isRecording, error: recError, start, stop } = useAudioRecorder();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [textInput, setTextInput] = useState("");
  const [useText, setUseText] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState("hi");

  const isEmergency = reportType === "emergency";

  async function handleDone() {
    setSubmitting(true);
    setError(null);
    try {
      const blob = await stop();
      if (!blob || blob.size === 0) {
        setError("No audio captured — please tap to speak again, or switch to typing.");
        setSubmitting(false);
        return;
      }
      const ticket = await createIncidentFromAudio({
        reportType,
        blob,
      });
      onCreated(ticket);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  async function handleTextSubmit() {
    if (!textInput.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const ticket = await createIncidentFromText({
        reportType,
        text: textInput,
        language: selectedLanguage,
      });
      onCreated(ticket);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className={`screen incident-recorder-screen ${isEmergency ? "emergency-theme" : ""}`}>
      {/* Plant Header */}
      <div className="incident-header-block">
        <div className="plant-tag">
          <span className="plant-dot"></span>
          {isEmergency ? "🚨 BSL CRITICAL EMERGENCY DISPATCH" : "🏭 BOKARO STEEL LIMITED · SAFETY DESK"}
        </div>
        <h1 className="screen-title">
          {isEmergency ? "Emergency Incident Report" : "Report Safety Incident"}
        </h1>
        <p className="subtitle">
          {isEmergency
            ? "Speak or type the emergency immediately. AI detects your language and alerts response teams instantly."
            : "Describe what you observed or suspect. Universal intake supports Hindi, Bengali, Tamil, Telugu, English and more."}
        </p>
      </div>

      {/* 4-Step Progress Stepper */}
      <div className="flow-stepper-bar initial-stepper-bar">
        <div className="step-node step-active">
          <span className="step-num">1</span>
          <span className="step-title">1. Describe Incident</span>
        </div>
        <div className="step-connector"></div>
        <div className="step-node step-pending">
          <span className="step-num">2</span>
          <span className="step-title">2. Visual Proof</span>
        </div>
        <div className="step-connector"></div>
        <div className="step-node step-pending">
          <span className="step-num">3</span>
          <span className="step-title">3. Safety Questions</span>
        </div>
        <div className="step-connector"></div>
        <div className="step-node step-pending">
          <span className="step-num">4</span>
          <span className="step-title">4. Precautions & Report</span>
        </div>
      </div>

      {/* Main Intake Card */}
      <div className="intake-main-card">
        {/* Mode Switcher Tabs - Apple Segmented Control */}
        <div className="intake-mode-switcher" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={!useText}
            className={`mode-tab ${!useText ? "active" : ""}`}
            onClick={() => setUseText(false)}
            disabled={submitting}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="22" />
            </svg>
            <span>Voice Recording (Any Language)</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={useText}
            className={`mode-tab ${useText ? "active" : ""}`}
            onClick={() => setUseText(true)}
            disabled={submitting || isRecording}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
            </svg>
            <span>Type Incident Text</span>
          </button>
        </div>

        {!useText ? (
          /* Voice Intake Panel */
          <div className="voice-intake-panel">
            {!isRecording ? (
              <div className="voice-idle-state">
                <button
                  type="button"
                  className="btn-hero-mic"
                  onClick={start}
                  disabled={submitting}
                >
                  <div className="mic-pulse-ring"></div>
                  <span className="hero-mic-icon" aria-hidden="true">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                      <line x1="12" y1="19" x2="12" y2="22" />
                    </svg>
                  </span>
                  <span className="hero-mic-title">Tap to Speak</span>
                  <span className="hero-mic-sub">Universal Voice Recognition</span>
                </button>

                <div className="supported-languages-box">
                  <div className="lang-box-header">
                    <span className="globe-icon" aria-hidden="true">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="2" y1="12" x2="22" y2="12" />
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                      </svg>
                    </span>
                    <span>Speak naturally in any Indian language or English:</span>
                  </div>
                  <div className="lang-chip-wrap">
                    <span className="lang-chip">हिन्दी</span>
                    <span className="lang-chip">বাংলা</span>
                    <span className="lang-chip">தமிழ்</span>
                    <span className="lang-chip">తెలుగు</span>
                    <span className="lang-chip">मराठी</span>
                    <span className="lang-chip">ગુજરાતી</span>
                    <span className="lang-chip">ಕನ್ನಡ</span>
                    <span className="lang-chip">മലയാളം</span>
                    <span className="lang-chip">ਪੰਜਾਬੀ</span>
                    <span className="lang-chip">ଓଡ଼ିଆ</span>
                    <span className="lang-chip">English</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="voice-recording-state">
                <div className="recording-wave-visualizer">
                  <div className="wave-bar bar1"></div>
                  <div className="wave-bar bar2"></div>
                  <div className="wave-bar bar3"></div>
                  <div className="wave-bar bar4"></div>
                  <div className="wave-bar bar5"></div>
                </div>
                <div className="live-rec-badge">
                  <span className="pulse-red-dot"></span>
                  Listening... Speak clearly in your language
                </div>
                <button
                  type="button"
                  className="btn-done-speaking"
                  onClick={handleDone}
                  disabled={submitting}
                >
                  Done Speaking (Analyze Incident)
                </button>
              </div>
            )}

            {submitting && (
              <div className="intake-processing-banner">
                <div className="processing-spinner"></div>
                <span>Analyzing audio & classifying incident with BSL Safety SOPs…</span>
              </div>
            )}

            {recError && <div className="error-box">⚠ {recError}</div>}
          </div>
        ) : (
          /* Text Intake Panel */
          <div className="text-intake-panel">
            <div className="intake-lang-picker">
              <label htmlFor="text-lang-select" className="intake-lang-label">
                ✍️ Language you are writing in:
              </label>
              <select
                id="text-lang-select"
                className="intake-lang-select"
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                disabled={submitting}
              >
                {INTAKE_LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            <textarea
              className="intake-textarea"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Describe what happened, where you saw it, any smoke, heat, flames, injured workers, or chemical/gas leak..."
              rows={5}
              disabled={submitting}
            />

            <div className="text-panel-actions">
              <button
                type="button"
                className="btn-submit-report"
                onClick={handleTextSubmit}
                disabled={submitting || !textInput.trim()}
              >
                {submitting ? "Analyzing Incident…" : "Submit Report →"}
              </button>
            </div>
          </div>
        )}

        {error && <div className="error-box">⚠ {error}</div>}
      </div>
    </div>
  );
}
