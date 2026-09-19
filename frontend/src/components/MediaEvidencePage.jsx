import { useRef, useState } from "react";
import { uploadMediaProof } from "../api";

export default function MediaEvidencePage({ ticket, onUploaded, onSkip }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [mediaType, setMediaType] = useState("image"); // "image" | "video"
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const photoInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const fileInputRef = useRef(null);

  const categoryName = (ticket?.predicted_category || "Incident").replace(/_/g, " ").toUpperCase();

  function handleFileSelect(selectedFile) {
    if (!selectedFile) return;
    const isImg = selectedFile.type.startsWith("image/");
    const isVid = selectedFile.type.startsWith("video/");
    if (!isImg && !isVid) {
      setError("Please select a valid photo (JPG, PNG, WEBP) or video (MP4, WEBM, MOV).");
      return;
    }
    setError(null);
    setFile(selectedFile);
    setMediaType(isVid ? "video" : "image");
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
      setError("Please capture or choose a photo or video before continuing.");
      return;
    }
    try {
      setUploading(true);
      setError(null);
      const updated = await uploadMediaProof(ticket.id, file);
      onUploaded(updated);
    } catch (err) {
      setError(err.message || "Failed to upload visual evidence. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  function handleReset() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setFile(null);
    setPreviewUrl(null);
    setError(null);
  }

  return (
    <div className="screen media-evidence-page">
      {/* 4-Step Progress Stepper */}
      <div className="flow-stepper-bar">
        <div className="step-node step-completed">
          <span className="step-num">✓</span>
          <span className="step-title">1. Incident Logged</span>
        </div>
        <div className="step-connector completed"></div>
        <div className="step-node step-active">
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

      <div className="media-evidence-container">
        {/* Header Alert Banner */}
        <div className="media-evidence-header">
          <div className="badge-mandatory">
            <span className="pulse-dot"></span>
            BSL Visual Evidence Protocol: BSL/SOP/EVID-02
          </div>
          <h1 className="media-evidence-title">📸🎥 Step 2: Visual Evidence (Photo or Video)</h1>
          <p className="media-evidence-subtitle">
            Visual field proof helps safety response units assess <strong>{categoryName}</strong> conditions rapidly.
            If you cannot capture media safely, use the skip button below to continue directly to questions.
          </p>
          <div className="incident-meta-chip">
            <span>Ticket ID: <code>{ticket?.id}</code></span>
            <span>Category: <strong>{categoryName}</strong></span>
            {ticket?.zone_id && <span>Zone: <strong>{ticket.zone_id}</strong></span>}
          </div>
        </div>

        {/* Hidden Inputs for Camera Photo, Camera Video, and File Picker */}
        <input
          ref={photoInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          style={{ display: "none" }}
          onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
        />
        <input
          ref={videoInputRef}
          type="file"
          accept="video/*"
          capture="environment"
          style={{ display: "none" }}
          onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
        />
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,video/*"
          style={{ display: "none" }}
          onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
        />

        {error && <div className="error-box">⚠ {error}</div>}

        {!file ? (
          /* Selection Mode: Photo vs Video vs Gallery */
          <div
            className={`media-dropzone ${isDragOver ? "dropzone-active" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
          >
            <div className="dropzone-icon">📷 / 🎥</div>
            <h3 className="dropzone-prompt">Choose Photo or Video to Upload</h3>
            <p className="dropzone-subtext">
              Capture or select a clear photo or short video recording of the hazard scene (flames, smoke, gas leak, molten metal, or damaged equipment).
            </p>

            <div className="media-choice-grid">
              <button
                type="button"
                className="btn-media-choice btn-camera-photo"
                onClick={() => photoInputRef.current?.click()}
              >
                <span className="choice-icon">📸</span>
                <div className="choice-text">
                  <span className="choice-title">Take Photo</span>
                  <span className="choice-desc">Snap live photo with camera</span>
                </div>
              </button>

              <button
                type="button"
                className="btn-media-choice btn-camera-video"
                onClick={() => videoInputRef.current?.click()}
              >
                <span className="choice-icon">🎥</span>
                <div className="choice-text">
                  <span className="choice-title">Record Video</span>
                  <span className="choice-desc">Capture live video clip</span>
                </div>
              </button>

              <button
                type="button"
                className="btn-media-choice btn-gallery-picker"
                onClick={() => fileInputRef.current?.click()}
              >
                <span className="choice-icon">🖼️ / 📁</span>
                <div className="choice-text">
                  <span className="choice-title">Gallery / Files</span>
                  <span className="choice-desc">Upload saved photo or video</span>
                </div>
              </button>
            </div>

            {/* Skip Button Below Camera & File Options */}
            <div className="camera-skip-container">
              <button
                type="button"
                className="btn-skip-camera-action"
                onClick={onSkip}
              >
                ⏭️ Skip Photo/Video & Proceed to Questions →
              </button>
              <p className="skip-subtext-note">
                In immediate danger, or unable to safely take photo/video? You can skip directly to verification questions.
              </p>
            </div>

            <span className="dropzone-drag-hint">or drag & drop any image (.jpg, .png, .webp) or video (.mp4, .webm, .mov) here</span>
          </div>
        ) : (
          /* Preview & Confirmation Mode */
          <div className="media-preview-card">
            <div className="preview-media-wrap">
              {mediaType === "video" ? (
                <div className="video-player-container">
                  <video
                    src={previewUrl}
                    controls
                    autoPlay
                    muted
                    loop
                    playsInline
                    className="preview-video-element"
                  />
                  <div className="preview-type-badge video-badge">🎥 Video Evidence Ready</div>
                </div>
              ) : (
                <div className="image-player-container">
                  <img src={previewUrl} alt="Visual field evidence" className="preview-img-element" />
                  <div className="preview-type-badge photo-badge">📸 Photo Evidence Ready</div>
                </div>
              )}
            </div>

            <div className="preview-meta">
              <div className="meta-row">
                <span className="meta-label">Evidence Type:</span>
                <span className="meta-value">
                  {mediaType === "video" ? "🎥 Video Recording" : "📸 Photographic Still"}
                </span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Selected File:</span>
                <span className="meta-value">{file.name || "field_evidence"}</span>
              </div>
              <div className="meta-row">
                <span className="meta-label">File Size:</span>
                <span className="meta-value">
                  {file.size > 1024 * 1024
                    ? `${(file.size / (1024 * 1024)).toFixed(2)} MB`
                    : `${(file.size / 1024).toFixed(1)} KB`}
                </span>
              </div>
              <div className="meta-row">
                <span className="meta-label">Location / Zone:</span>
                <span className="meta-value">{ticket?.zone_id || "Bokaro Steel Facility"}</span>
              </div>
            </div>

            <div className="preview-actions">
              <button
                type="button"
                className="retake-btn"
                onClick={handleReset}
                disabled={uploading}
              >
                🔄 Retake / Choose Different File
              </button>
              <button
                type="button"
                className="confirm-upload-btn"
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading
                  ? "Uploading Evidence & Loading Questions…"
                  : "Confirm Evidence & Proceed to Questions →"}
              </button>
              <button
                type="button"
                className="btn-skip-preview"
                onClick={onSkip}
                disabled={uploading}
              >
                Skip without Photo/Video →
              </button>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="media-evidence-footer">
          <div className="footer-info">
            <span className="shield-icon">🔒</span>
            <span>
              Visual Evidence Protocol: Media is secured and transmitted directly to BSL Emergency Units (Fire, HazMat, Casthouse, Medical)
              along with your verification answers.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
