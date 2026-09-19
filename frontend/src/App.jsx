import { useState } from "react";
import ReportTypeSelect from "./components/ReportTypeSelect";
import IncidentRecorder from "./components/IncidentRecorder";
import MediaEvidencePage from "./components/MediaEvidencePage";
import VerificationInterview from "./components/VerificationInterview";
import PrecautionaryMeasuresModal from "./components/PrecautionaryMeasuresModal";
import TicketResult from "./components/TicketResult";
import Dashboard from "./components/Dashboard";
import "./App.css";

export default function App() {
  const [view, setView] = useState("worker"); // "worker" | "dashboard"
  const [step, setStep] = useState("select");
  const [reportType, setReportType] = useState(null);
  const [ticketId, setTicketId] = useState(null);
  const [currentTicket, setCurrentTicket] = useState(null);

  function handleSelect(type) {
    setReportType(type);
    setStep("report");
  }

  function handleIncidentCreated(ticket) {
    setTicketId(ticket.id);
    setCurrentTicket(ticket);
    // In necessary cases (requires_photo_proof == true), navigate to dedicated photo/video upload page
    if (ticket.requires_photo_proof && !ticket.photo_proof_path) {
      setStep("media_proof");
    } else {
      // Non-necessary cases proceed straight to verification questions
      setStep("verification");
    }
  }

  function handleMediaUploaded(updatedTicket) {
    setCurrentTicket(updatedTicket);
    // After uploading the photo or video, proceed directly to asking questions
    setStep("verification");
  }

  function handleVerificationComplete() {
    setStep("precautions");
  }

  function handleProceedToReport() {
    setStep("result");
  }

  function handleReset() {
    setStep("select");
    setReportType(null);
    setTicketId(null);
  }

  return (
    <div className="app-shell">
      {/* Top Navigation */}
      <header className="navbar">
        <div className="nav-brand">
          <span className="brand-logo">🛡️</span>
          <div className="brand-text">
            <span className="brand-title">BSL Safety Intelligence</span>
            <span className="brand-subtitle">AI Incident Triage & Decision Support</span>
          </div>
        </div>

        <nav className="nav-links">
          <button
            className={`nav-tab ${view === "worker" ? "active" : ""}`}
            onClick={() => setView("worker")}
          >
            👷 Worker Reporting
          </button>
          <button
            className={`nav-tab ${view === "dashboard" ? "active" : ""}`}
            onClick={() => setView("dashboard")}
          >
            📋 Safety Officer Dashboard
          </button>
        </nav>
      </header>

      {/* Main Container */}
      <main className="main-content">
        {view === "dashboard" && <Dashboard />}

        {view === "worker" && (
          <div className="app">
            {step === "select" && <ReportTypeSelect onSelect={handleSelect} />}
            {step === "report" && (
              <IncidentRecorder reportType={reportType} onCreated={handleIncidentCreated} />
            )}
            {(step === "media_proof" || step === "photo_proof") && (
              <MediaEvidencePage
                ticket={currentTicket}
                onUploaded={handleMediaUploaded}
                onSkip={() => setStep("verification")}
              />
            )}
            {step === "verification" && (
              <VerificationInterview
                ticketId={ticketId}
                onComplete={handleVerificationComplete}
                onRetry={() => setStep("report")}
              />
            )}
            {step === "precautions" && (
              <PrecautionaryMeasuresModal
                ticketId={ticketId}
                onProceedToReport={handleProceedToReport}
              />
            )}
            {step === "result" && (
              <>
                <TicketResult ticketId={ticketId} isEmergency={reportType === "emergency"} />
                <div className="result-actions">
                  <button className="link-btn reset-btn" onClick={handleReset}>
                    Report another incident
                  </button>
                  <button
                    className="link-btn secondary-btn"
                    onClick={() => setView("dashboard")}
                  >
                    View in Safety Dashboard →
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
