import { useState } from "react";
import ReportTypeSelect from "./components/ReportTypeSelect";
import IncidentRecorder from "./components/IncidentRecorder";
import MediaEvidencePage from "./components/MediaEvidencePage";
import VerificationInterview from "./components/VerificationInterview";
import PrecautionaryMeasuresModal from "./components/PrecautionaryMeasuresModal";
import TicketResult from "./components/TicketResult";
import Dashboard from "./components/Dashboard";
import AdminOnboarding from "./components/AdminOnboarding";
import "./App.css";

export default function App() {
  const [view, setView] = useState("worker"); // "worker" | "dashboard" | "admin"
  const [activePlantId, setActivePlantId] = useState("bsl_bokaro");
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
      {/* Top Navigation - Apple Liquid Glass Bar */}
      <header className="navbar">
        <div className="nav-brand">
          <span className="brand-logo" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
          <div className="brand-text">
            <span className="brand-title">BSL Safety Intelligence</span>
            <span className="brand-subtitle">AI Incident Triage & Decision Support</span>
          </div>
        </div>

        <nav className="nav-links" role="tablist" aria-label="Main Navigation">
          <button
            role="tab"
            aria-selected={view === "worker"}
            className={`nav-tab ${view === "worker" ? "active" : ""}`}
            onClick={() => setView("worker")}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>Worker Reporting</span>
          </button>
          <button
            role="tab"
            aria-selected={view === "dashboard"}
            className={`nav-tab ${view === "dashboard" ? "active" : ""}`}
            onClick={() => setView("dashboard")}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
            <span>Safety Dashboard</span>
          </button>
          <button
            role="tab"
            aria-selected={view === "admin"}
            className={`nav-tab ${view === "admin" ? "active" : ""}`}
            onClick={() => setView("admin")}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            <span>Plant Admin</span>
          </button>
        </nav>
      </header>

      {/* Main Container */}
      <main className="main-content">
        {view === "admin" && (
          <AdminOnboarding
            activePlantId={activePlantId}
            onSelectPlant={(pId) => setActivePlantId(pId)}
          />
        )}
        {view === "dashboard" && <Dashboard plantId={activePlantId} />}

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
