import { useState, useRef } from 'react';
import Navbar from '../components/Navbar';

export default function UploadVideoPage() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('video/')) {
      setFile(droppedFile);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) setFile(selectedFile);
  };

  const formatSize = (bytes) => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + ' GB';
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(2) + ' MB';
    return (bytes / 1024).toFixed(2) + ' KB';
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    for (let i = 0; i <= 100; i += 2) {
      await new Promise(resolve => setTimeout(resolve, 50));
      setUploadProgress(i);
    }

    setIsUploading(false);
    setUploadComplete(true);
  };

  const resetUpload = () => {
    setFile(null);
    setUploadProgress(0);
    setIsUploading(false);
    setUploadComplete(false);
  };

  return (
    <div className="upload-video-page" id="upload-video-page">
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <div className="page-header-icon accent">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="7" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M23 12L29 8V22L23 18" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" fill="none"/>
              <path d="M10 18V12L15 15L10 18Z" fill="currentColor" opacity="0.4"/>
            </svg>
          </div>
          <div>
            <h1 className="page-title">Upload CCTV Video</h1>
            <p className="page-subtitle">Upload surveillance footage for AI-powered face detection and matching.</p>
          </div>
        </div>

        <div className="upload-card" id="upload-card">
          {!file && !uploadComplete && (
            <div
              className={`drop-zone ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              id="drop-zone"
            >
              <div className="drop-zone-content">
                <div className="drop-icon">
                  <svg viewBox="0 0 64 64" fill="none" width="64" height="64">
                    <path d="M32 44V20" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
                    <path d="M22 30L32 20L42 30" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M10 40C10 48 16 52 24 52H40C48 52 54 48 54 40" stroke="currentColor" strokeWidth="3" strokeLinecap="round" fill="none" opacity="0.4"/>
                  </svg>
                </div>
                <h3>Drag & Drop Video File</h3>
                <p>or click to browse from your computer</p>
                <span className="drop-formats">MP4, AVI, MOV, MKV — Max 500MB</span>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                style={{ display: 'none' }}
                id="video-file-input"
              />
            </div>
          )}

          {file && !uploadComplete && (
            <div className="file-preview" id="file-preview">
              <div className="file-info">
                <div className="file-icon-wrapper">
                  <svg viewBox="0 0 48 48" fill="none" width="40" height="40">
                    <rect x="8" y="4" width="32" height="40" rx="4" stroke="currentColor" strokeWidth="2" fill="none"/>
                    <path d="M20 24L28 28L20 32V24Z" fill="currentColor" opacity="0.6"/>
                  </svg>
                </div>
                <div className="file-details">
                  <p className="file-name">{file.name}</p>
                  <p className="file-size">{formatSize(file.size)}</p>
                </div>
                {!isUploading && (
                  <button className="btn btn-ghost btn-sm" onClick={resetUpload} id="remove-file-btn">✕</button>
                )}
              </div>

              {isUploading && (
                <div className="progress-section">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                  <span className="progress-text">{uploadProgress}%</span>
                </div>
              )}

              {!isUploading && (
                <div className="upload-actions">
                  <button className="btn btn-ghost" onClick={resetUpload} id="cancel-upload-btn">Cancel</button>
                  <button className="btn btn-primary" onClick={handleUpload} id="start-upload-btn">
                    Upload & Analyze
                  </button>
                </div>
              )}
            </div>
          )}

          {uploadComplete && (
            <div className="upload-success fade-in" id="upload-success">
              <div className="success-icon">
                <svg viewBox="0 0 64 64" fill="none" width="64" height="64">
                  <circle cx="32" cy="32" r="28" stroke="var(--color-success)" strokeWidth="3" fill="none"/>
                  <path d="M20 32L28 40L44 24" stroke="var(--color-success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Upload Complete!</h3>
              <p>Your video is being processed. You'll be notified when results are ready.</p>
              <button className="btn btn-primary" onClick={resetUpload} id="upload-another-btn">
                Upload Another
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
