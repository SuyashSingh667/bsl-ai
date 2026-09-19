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
            <span className="key-hint">[Press 1]</span>
          </div>
          <div className="card-main-content">
            <span className="card-icon">⚠️</span>
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
            <span className="card-badge badge-emergency">🚨 Immediate Danger</span>
            <span className="key-hint">[Press 2]</span>
          </div>
          <div className="card-main-content">
            <span className="card-icon">🔥</span>
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
