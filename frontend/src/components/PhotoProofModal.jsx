import { useRef, useState } from "react";
import { uploadPhotoProof } from "../api";

export default function PhotoProofModal({ ticket, onUploaded }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const cameraInputRef = useRef(null);
  const galleryInputRef = useRef(null);

  const categoryName = (ticket?.predicted_category || "incident").replace(/_/g, " ").toUpperCase();

  function handleFileSelect(selectedFile) {
    if (!selectedFile) return;
    if (!selectedFile.type.startsWith("image/")) {
      setError("Please select a valid image file (JPG, PNG, WEBP).");
      return;
    }
    setError(null);
    setFile(selectedFile);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(URL.createObjectURL(selectedFile));
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }

  async function handleUpload() {
    if (!file) {
      setError("Please capture or select a photo before continuing.");
      return;
    }
    try {
      setUploading(true);
      setError(null);
      const updated = await uploadPhotoProof(ticket.id, file);
      onUploaded(updated);
    } catch (err) {
      setError(err.message || "Failed to upload photo proof. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  function handleResetPhoto() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setFile(null);
    setPreviewUrl(null);
    setError(null);
  }

  return (
    <div className="screen photo-proof-page">
      {/* Reporting Workflow Progress Stepper */}
      <div className="flow-stepper-bar">
        <div className="step-node step-completed">
          <span className="step-num">✓</span>
          <span className="step-title">1. Incident Logged</span>
        </div>
        <div className="step-connector completed"></div>
        <div className="step-node step-active">
          <span className="step-num">2</span>
          <span className="step-title">2. Photo Proof (Mandatory)</span>
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

      <div className="photo-proof-container">
        {/* Header Alert Banner */}
        <div className="photo-proof-header">
          <div className="badge-mandatory">
            <span className="pulse-dot"></span>
            BSL Mandatory Standard: Photo Evidence Required
          </div>
          <h1 className="photo-proof-title">📸 Step 2: Upload Incident Photo Proof</h1>
          <p className="photo-proof-subtitle">
            Every incident reported at Bokaro Steel mandates photographic scene verification.
            <strong> Uploading a photo is compulsory</strong> — after uploading, you will immediately answer short verification questions about the incident.
          </p>
          <div className="incident-meta-chip">
            <span>Ticket ID: <code>{ticket?.id}</code></span>
            <span>Category: <strong>{categoryName}</strong></span>
            {ticket?.zone_id && <span>Zone: <strong>{ticket.zone_id}</strong></span>}
          </div>
        </div>

        {/* Hidden File Inputs */}
        {/* Native Camera Trigger */}
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />
        {/* Gallery / File Picker Trigger */}
        <input
          ref={galleryInputRef}
          type="file"
          accept="image/*"
          style={{ display: "none" }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />

        {error && <div className="error-box">⚠ {error}</div>}

        {!file ? (
          /* Selection Mode: Camera & Gallery options */
          <div
            className={`photo-dropzone ${isDragOver ? "dropzone-active" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
          >
            <div className="dropzone-icon">📷</div>
            <h3 className="dropzone-prompt">Choose Photo Source</h3>
            <p className="dropzone-subtext">
              Capture or select a clear picture of the hazard area (flames, smoke, leak, broken equipment, or damaged machinery).
            </p>

            <div className="photo-choice-actions">
              <button
                type="button"
                className="btn-camera-trigger"
                onClick={() => cameraInputRef.current?.click()}
              >
                <span className="btn-icon">📸</span>
                <div className="btn-text-block">
                  <span className="btn-title">Open Camera</span>
                  <span className="btn-subtitle">Snap live photo from your phone or device</span>
                </div>
              </button>

              <button
                type="button"
                className="btn-gallery-trigger"
                onClick={() => galleryInputRef.current?.click()}
              >
                <span className="btn-icon">🖼️</span>
                <div className="btn-text-block">
                  <span className="btn-title">Choose from Gallery / Files</span>
                  <span className="btn-subtitle">Select saved picture or screenshot from device</span>
                </div>
              </button>
            </div>

            <span className="dropzone-drag-hint">or drag and drop an image file into this box</span>
          </div>
        ) : (
          /* Preview & Confirmation Mode */
          <div className="photo-preview-card">
            <div className="preview-image-wrap">
              <img src={previewUrl} alt="Incident field evidence" className="preview-img" />
              <div className="preview-badge">✓ Photo Ready for Upload</div>
            </div>

            <div className="preview-meta">
              <div className="meta-row">
                <span className="meta-label">Selected File:</span>
                <span className="meta-value">{file.name || "incident_photo.jpg"}</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">File Size:</span>
                <span className="meta-value">{(file.size / 1024).toFixed(1)} KB</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Location / Zone:</span>
                <span className="meta-value">{ticket?.zone_id || "Bokaro Plant Facility"}</span>
              </div>
            </div>

            <div className="preview-actions">
              <button
                type="button"
                className="retake-btn"
                onClick={handleResetPhoto}
                disabled={uploading}
              >
                🔄 Retake / Choose Different Photo
              </button>
              <button
                type="button"
                className="confirm-upload-btn"
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading
                  ? "Uploading Photo & Loading Questions…"
                  : "Confirm Photo & Proceed to Questions →"}
              </button>
            </div>
          </div>
        )}

        {/* Security & Compliance Footer */}
        <div className="photo-proof-footer">
          <span className="shield-icon">🔒</span>
          <span>
            Compulsory Verification: Photographs are timestamped and transmitted directly to BSL
            emergency units and safety investigation squads along with your answers to follow.
          </span>
        </div>
      </div>
    </div>
  );
}
