import { useEffect } from "react";

export default function ReportTypeSelect({ onSelect }) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "1") onSelect("suspected");
      if (e.key === "2") onSelect("emergency");
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onSelect]);

  return (
    <div className="screen report-type-screen">
      <div className="report-type-header">
        <div className="plant-tag">
          <span className="plant-dot"></span>
          Bokaro Steel Limited · EHS AI Incident Triage
        </div>
        <h1 className="screen-title">Report Workplace Incident or Emergency</h1>
        <p className="subtitle">
          Select your reporting category below to dispatch plant safety officers immediately.
        </p>
      </div>

      <div className="choice-row">
        <button
          type="button"
          className="choice-card choice-suspected"
          onClick={() => onSelect("suspected")}
        >
          <div className="card-top-row">
            <span className="card-badge badge-suspected">Standard Triage</span>
            <span className="key-hint">Press 1</span>
          </div>
          <div className="card-main-content">
            <span className="card-icon" aria-hidden="true">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#FF9F0A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </span>
            <div className="card-text-block">
              <h2 className="card-heading">Report Suspected Incident</h2>
              <p className="card-explanation">
                Hazardous condition, near miss, machinery malfunction, minor gas odor, or safety non-compliance.
              </p>
            </div>
          </div>
          <div className="card-footer-cta">
            <span>Continue to Voice / Text Intake</span>
            <span className="arrow-icon">→</span>
          </div>
        </button>

        <button
          type="button"
          className="choice-card choice-emergency"
          onClick={() => onSelect("emergency")}
        >
          <div className="card-top-row">
            <span className="card-badge badge-emergency">
              <span className="pulse-dot" style={{ width: 6, height: 6, marginRight: 4 }}></span>
              Immediate Danger
            </span>
            <span className="key-hint">Press 2</span>
          </div>
          <div className="card-main-content">
            <span className="card-icon" aria-hidden="true">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#FF453A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
              </svg>
            </span>
            <div className="card-text-block">
              <h2 className="card-heading">Report Critical Emergency</h2>
              <p className="card-explanation">
                Active fire, molten metal breakout, toxic gas leak, explosion, structural collapse, or trapped worker requiring rescue.
              </p>
            </div>
          </div>
          <div className="card-footer-cta">
            <span>Immediate Siren & Emergency Dispatch</span>
            <span className="arrow-icon">→</span>
          </div>
        </button>
      </div>
    </div>
  );
}
