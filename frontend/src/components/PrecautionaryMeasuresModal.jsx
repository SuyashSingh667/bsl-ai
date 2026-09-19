import { useEffect, useRef, useState } from "react";
import { audioUrl, getPrecautions } from "../api";

export default function PrecautionaryMeasuresModal({ ticketId, onProceedToReport }) {
  const [precautions, setPrecautions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showChecklist, setShowChecklist] = useState(false);
  const [checkedItems, setCheckedItems] = useState({});
  const audioRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    async function fetchPrecautions() {
      try {
        setLoading(true);
        const data = await getPrecautions(ticketId);
        if (mounted) {
          setPrecautions(data);
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || "Could not load precautionary measures");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    fetchPrecautions();
    return () => {
      mounted = false;
    };
  }, [ticketId]);

  function handleToggleAudio() {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      setShowChecklist(true);
      audioRef.current.currentTime = 0;
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch((err) => {
          console.warn("Audio play failed:", err);
          setIsPlaying(false);
        });
    }
  }

  function handleAudioEnded() {
    setIsPlaying(false);
  }

  function toggleCheck(id) {
    setCheckedItems((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  if (loading) {
    return (
      <div className="screen precautionary-screen">
        <div className="loading-box">
          <div className="loading-spinner">⏳</div>
          <h2>Preparing Your Personal Safety Precautions…</h2>
          <p className="subtitle">Grounded in Bokaro Steel Plant Standard Operating Procedures (SOPs)</p>
        </div>
      </div>
    );
  }

  if (error || !precautions) {
    return (
      <div className="screen precautionary-screen">
        <div className="error-box">
          <p className="error-text">{error || "Failed to load precautions."}</p>
          <button className="primary-btn" onClick={onProceedToReport}>
            Proceed to Incident Report →
          </button>
        </div>
      </div>
    );
  }

  const promptNative = precautions.prompt_question_native || precautions.prompt_question;
  const promptEn = precautions.prompt_question;
  const isDifferentLang = promptNative !== promptEn;

  return (
    <div className="screen precautionary-screen">
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
        <div className="step-node step-completed">
          <span className="step-num">✓</span>
          <span className="step-title">3. Safety Questions</span>
        </div>
        <div className="step-connector completed"></div>
        <div className="step-node step-active">
          <span className="step-num">4</span>
          <span className="step-title">4. Precautions & Report</span>
        </div>
      </div>

      <div className="precautionary-container">
        {/* Safety Header */}
        <div className="precautionary-header">
          <div className="badge-urgent">
            <span className="pulse-dot"></span>
            BSL Worker Life-Safety Protection Protocol
          </div>
          <h1 className="precautionary-title">🛡️ Worker Safety Precautions</h1>
          <p className="sop-reference-tag">
            Grounded in: <strong>{precautions.sop_source}</strong> ({precautions.sop_code})
          </p>
        </div>

        {/* Audio element */}
        {precautions.audio_path && (
          <audio
            ref={audioRef}
            src={audioUrl(precautions.audio_path)}
            onEnded={handleAudioEnded}
            onPause={() => setIsPlaying(false)}
            onPlay={() => setIsPlaying(true)}
            preload="auto"
          />
        )}

        {/* Primary Prompt Card */}
        <div className="prompt-card">
          <div className="prompt-icon">📢</div>
          <div className="prompt-content">
            <h2 className="prompt-text-native">{promptNative}</h2>
            {isDifferentLang && (
              <p className="prompt-text-en">"{promptEn}"</p>
            )}
            <p className="prompt-hint">
              Please review these life-safety actions immediately before checking the technical report.
            </p>
          </div>
        </div>

        {/* Main Action Buttons */}
        <div className="precaution-actions">
          {precautions.audio_path && (
            <button
              className={isPlaying ? "action-btn-listen playing" : "action-btn-listen"}
              onClick={handleToggleAudio}
            >
              <span className="btn-icon">{isPlaying ? "⏸️" : "🔊"}</span>
              <div className="btn-text-block">
                <span className="btn-title">
                  {isPlaying ? "Pause Voice Precautions" : "Listen to Safety Precautions"}
                </span>
                <span className="btn-subtitle">Clear spoken instructions in your language</span>
              </div>
            </button>
          )}

          <button
            className={showChecklist ? "action-btn-view active" : "action-btn-view"}
            onClick={() => setShowChecklist((prev) => !prev)}
          >
            <span className="btn-icon">📋</span>
            <div className="btn-text-block">
              <span className="btn-title">
                {showChecklist ? "Hide Checklist" : "View Safety Checklist"}
              </span>
              <span className="btn-subtitle">Interactive action verification</span>
            </div>
          </button>
        </div>

        {/* Audio Transcript Banner if playing */}
        {isPlaying && (
          <div className="audio-live-banner">
            <div className="audio-wave-anim">
              <span></span><span></span><span></span><span></span><span></span>
            </div>
            <p className="audio-live-text">"{precautions.spoken_summary_native}"</p>
          </div>
        )}

        {/* Actionable Measures & Checklist */}
        {showChecklist && (
          <div className="measures-checklist-section">
            <div className="section-heading-row">
              <h3>4 Immediate Protection Steps:</h3>
              <span className="checklist-progress">
                {Object.values(checkedItems).filter(Boolean).length} of {precautions.measures?.length || 4} verified
              </span>
            </div>

            <div className="measures-grid">
              {precautions.measures?.map((measure, idx) => {
                const isChecked = !!checkedItems[measure.id];
                return (
                  <div
                    key={measure.id}
                    className={isChecked ? "measure-card measure-card-checked" : "measure-card"}
                  >
                    <div className="measure-card-header">
                      <span className="measure-icon">{measure.icon}</span>
                      <div className="measure-titles">
                        <h4 className="measure-native-title">
                          {idx + 1}. {measure.title_native}
                        </h4>
                        {measure.title_native !== measure.title && (
                          <span className="measure-en-title">{measure.title}</span>
                        )}
                      </div>
                    </div>

                      <p className="measure-desc-native">{measure.text_native}</p>
                      {measure.text_native !== measure.text && (
                        <p className="measure-desc-en">"{measure.text}"</p>
                      )}

                    <div className="measure-checkbox-row">
                      <label className="measure-checkbox-label">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleCheck(measure.id)}
                        />
                        <span className="custom-check"></span>
                        <span className="checkbox-text">
                          {measure.checklist_label_native || measure.checklist_label}
                        </span>
                      </label>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Footer Navigation */}
        <div className="precautionary-footer">
          <button className="primary-btn proceed-btn" onClick={onProceedToReport}>
            <span>I am in a Safe Position — View Incident Report</span>
            <span className="arrow">→</span>
          </button>
        </div>
      </div>
    </div>
  );
}
