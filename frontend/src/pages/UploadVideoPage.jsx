import { useState, useRef, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

export default function UploadVideoPage() {
  const [file, setFile] = useState(null);
  const [uploadMode, setUploadMode] = useState('local'); // 'local' or 'cloud'
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState(null);
  const [persons, setPersons] = useState([]);
  const [targetPersonId, setTargetPersonId] = useState('');
  const fileInputRef = useRef(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchPersons = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = { 'Authorization': `Bearer ${token}` };
        const res = await fetch('http://localhost:8000/api/persons', { headers });
        const data = await res.json();
        setPersons(data.data || []);
      } catch (err) {
        console.error("Failed to fetch persons:", err);
      }
    };
    fetchPersons();
  }, []);

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
    setUploadProgress(10);
    setStatusMessage('Uploading video...');
    setError(null);

    const formData = new FormData();
    formData.append('video', file);

    try {
      // 1. Upload Video
      const uploadRes = await fetch('http://localhost:8000/api/upload-video', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.token}`,
        },
        body: formData,
      });

      const uploadData = await uploadRes.json();
      
      if (!uploadRes.ok || uploadData.status !== 'success') {
        throw new Error(uploadData.message || 'Video upload failed');
      }

      setUploadProgress(50);
      setStatusMessage('Running AI face detection...');

      // 2. Run Detection
      const detectionFormData = new FormData();
      detectionFormData.append('video_path', uploadData.data.video_path);
      
      if (targetPersonId) {
        detectionFormData.append('target_person_id', targetPersonId);
      }

      const detectionRes = await fetch('http://localhost:8000/api/run-detection', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.token}`,
        },
        body: detectionFormData,
      });

      const detectionData = await detectionRes.json();
      
      if (!detectionRes.ok || detectionData.status !== 'success') {
        throw new Error(detectionData.message || 'Detection failed');
      }

      setUploadProgress(100);
      setIsUploading(false);
      setUploadComplete(true);
      setStatusMessage(`${detectionData.message}`);
    } catch (err) {
      setIsUploading(false);
      setError(err.message || 'An error occurred during processing');
    }
  };

  const resetUpload = () => {
    setFile(null);
    setUploadProgress(0);
    setIsUploading(false);
    setUploadComplete(false);
    setStatusMessage('');
    setError(null);
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
          {/* Upload Mode Tabs */}
          {!file && !uploadComplete && (
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
              <button 
                onClick={() => setUploadMode('local')}
                style={{
                  padding: '8px 16px',
                  fontWeight: uploadMode === 'local' ? '600' : '400',
                  color: uploadMode === 'local' ? 'var(--color-primary)' : 'var(--text-secondary)',
                  borderBottom: uploadMode === 'local' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  background: 'none',
                  borderTop: 'none',
                  borderLeft: 'none',
                  borderRight: 'none',
                  cursor: 'pointer'
                }}
              >
                Local Upload
              </button>
              <button 
                onClick={() => setUploadMode('cloud')}
                style={{
                  padding: '8px 16px',
                  fontWeight: uploadMode === 'cloud' ? '600' : '400',
                  color: uploadMode === 'cloud' ? 'var(--color-primary)' : 'var(--text-secondary)',
                  borderBottom: uploadMode === 'cloud' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  background: 'none',
                  borderTop: 'none',
                  borderLeft: 'none',
                  borderRight: 'none',
                  cursor: 'pointer'
                }}
              >
                Import from Drive
              </button>
            </div>
          )}

          {/* Local Upload UI */}
          {uploadMode === 'local' && !file && !uploadComplete && (
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

          {/* Cloud Drive UI */}
          {uploadMode === 'cloud' && !file && !uploadComplete && (
            <div className="drop-zone" style={{ flexDirection: 'column', gap: '1rem', padding: '3rem' }}>
              <div style={{ color: 'var(--color-primary)' }}>
                <svg viewBox="0 0 24 24" fill="none" width="60" height="60" stroke="currentColor" strokeWidth="1.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
                </svg>
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '500', color: 'var(--text-primary)' }}>Connect Cloud Storage</h3>
              <p style={{ color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '400px' }}>
                Securely browse and select surveillance footage directly from your connected government cloud drives.
              </p>
              <button 
                className="btn btn-primary" 
                style={{ marginTop: '1rem' }}
                onClick={() => alert("Cloud Drive integration requires OAuth configuration with Google Workspace or Microsoft Azure. Please contact the IT Administration Department.")}
              >
                Connect to Drive
              </button>
            </div>
          )}

          {/* Target Person Selection */}
          {!uploadComplete && (
            <div className="person-selection" style={{ marginTop: '1.5rem', marginBottom: file ? '1.5rem' : '0', textAlign: 'left' }}>
              <label htmlFor="target-person" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: 'var(--text-secondary)' }}>
                Target Person to Find (Optional)
              </label>
              <select 
                id="target-person"
                value={targetPersonId}
                onChange={(e) => setTargetPersonId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'transparent',
                  color: 'inherit',
                  fontSize: '1rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="">All Missing Persons (Default)</option>
                {persons.filter(p => p.status === 'missing').map(p => (
                  <option key={p.id} value={p.id}>{p.name} (ID: {p.id})</option>
                ))}
              </select>
            </div>
          )}

          {/* File Selected & Processing UI */}
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
                  <button className="btn btn-ghost btn-sm" onClick={resetUpload} id="remove-file-btn"></button>
                )}
              </div>

              {isUploading && (
                <div className="progress-section">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                  <div style={{display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem'}}>
                    <span className="progress-text">{statusMessage}</span>
                    <span className="progress-text">{uploadProgress}%</span>
                  </div>
                </div>
              )}

              {error && (
                <div className="alert alert-error" style={{marginTop: '1rem'}}>
                  <span className="alert-icon"></span>
                  {error}
                </div>
              )}

              {!isUploading && !error && (
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
              <h3>Processing Complete!</h3>
              <p>{statusMessage || 'Your video has been processed.'}</p>
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
