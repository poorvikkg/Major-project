import { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

const API = 'http://localhost:8000';

export default function LiveMonitoringPage() {
  const { user } = useAuth();
  const [rtspUrl, setRtspUrl]         = useState('');
  const [fps, setFps]                 = useState(5);
  const [streamActive, setStreamActive] = useState(false);
  const [streamSource, setStreamSource] = useState('');
  const [statusMsg, setStatusMsg]     = useState('');
  const [error, setError]             = useState('');
  const [starting, setStarting]       = useState(false);
  const [results, setResults]         = useState([]);
  const [lastSince, setLastSince]     = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [frameTs, setFrameTs]         = useState(null); // to force img reload
  const pollRef  = useRef(null);
  const imageRef = useRef(null);

  // Clock
  useEffect(() => {
    const t = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Poll initial stream status
  useEffect(() => {
    fetchStatus();
  }, []);

  // Poll results while stream is active
  useEffect(() => {
    if (streamActive) {
      pollRef.current = setInterval(fetchResults, 2000);
    } else {
      clearInterval(pollRef.current);
    }
    return () => clearInterval(pollRef.current);
  }, [streamActive, lastSince]);

  const token = () => localStorage.getItem('token');
  const authHeaders = () => ({ 'Authorization': `Bearer ${token()}`, 'Content-Type': 'application/json' });

  async function fetchStatus() {
    try {
      const res  = await fetch(`${API}/api/stream/status`);
      const data = await res.json();
      if (data.data?.stream_active) {
        setStreamActive(true);
        setStreamSource(data.data.stream_source || '');
        setStatusMsg('Stream is active');
      }
    } catch (_) {}
  }

  async function fetchResults() {
    try {
      const res  = await fetch(`${API}/api/stream/results?limit=20&since=${lastSince}`);
      const data = await res.json();
      if (data.data?.history?.length > 0) {
        const incoming = data.data.history;
        setResults(prev => {
          const merged = [...incoming, ...prev].slice(0, 50);
          return merged;
        });
        const maxTs = Math.max(...incoming.map(r => r.timestamp));
        setLastSince(maxTs);
      }
      // Force img reload to reduce latency perception
      setFrameTs(Date.now());
    } catch (_) {}
  }

  async function handleStart() {
    const src = rtspUrl.trim() || '0';
    setError('');
    setStatusMsg('');
    setStarting(true);

    try {
      const res  = await fetch(`${API}/api/stream/start`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ rtsp_url: src, fps: Number(fps), reload_index: true }),
      });
      const data = await res.json();

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.message || data.detail?.message || 'Failed to start stream');
      }

      setStreamActive(true);
      setStreamSource(src);
      setResults([]);
      setLastSince(0);
      setStatusMsg(`Stream started. ${data.data?.embeddings_loaded ?? 0} person embeddings loaded.`);
    } catch (e) {
      setError(e.message);
    } finally {
      setStarting(false);
    }
  }

  async function handleStop() {
    try {
      await fetch(`${API}/api/stream/stop`, {
        method: 'POST',
        headers: authHeaders(),
      });
    } catch (_) {}
    setStreamActive(false);
    setStreamSource('');
    setResults([]);
    setStatusMsg('Stream stopped.');
  }

  const videoFeedUrl = `${API}/api/stream/video_feed`;

  return (
    <div className="live-monitoring-page" id="live-monitoring-page">
      <Navbar />
      <div className="page-container">

        {/* Page Header */}
        <div className="page-header">
          <div className="page-header-icon danger">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="6" width="24" height="16" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M4 24H28" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="16" cy="14" r="2" fill="var(--color-danger)"/>
            </svg>
          </div>
          <div>
            <h1 className="page-title">Live CCTV Monitoring</h1>
            <p className="page-subtitle">
              Connect to any RTSP camera stream. Face recognition runs on the server — the raw stream is never exposed to the browser.
            </p>
          </div>
          {streamActive && (
            <div className="live-indicator" id="live-indicator">
              <span className="live-dot"></span>
              LIVE
            </div>
          )}
        </div>

        {/* Stream Control Panel */}
        <div className="form-card" style={{ marginBottom: '1.5rem' }}>
          <p className="section-title" style={{ marginBottom: '1rem' }}>Stream Configuration</p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px auto auto', gap: '0.75rem', alignItems: 'end' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="rtsp-url-input">RTSP URL / Source</label>
              <input
                id="rtsp-url-input"
                className="form-input"
                type="text"
                placeholder="rtsp://admin:password@192.168.1.100:554/stream  or  0 for webcam"
                value={rtspUrl}
                onChange={e => setRtspUrl(e.target.value)}
                disabled={streamActive || starting}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="fps-input">Process FPS</label>
              <input
                id="fps-input"
                className="form-input"
                type="number"
                min="1" max="30"
                value={fps}
                onChange={e => setFps(e.target.value)}
                disabled={streamActive || starting}
              />
            </div>

            {!streamActive ? (
              <button
                className="btn btn-primary"
                onClick={handleStart}
                disabled={starting}
                id="start-stream-btn"
                style={{ alignSelf: 'end', whiteSpace: 'nowrap' }}
              >
                {starting ? 'Connecting...' : 'Start Stream'}
              </button>
            ) : (
              <button
                className="btn btn-ghost"
                onClick={handleStop}
                id="stop-stream-btn"
                style={{ alignSelf: 'end', whiteSpace: 'nowrap', borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }}
              >
                Stop Stream
              </button>
            )}

            <div style={{ alignSelf: 'end', fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', paddingBottom: '0.55rem' }}>
              {currentTime.toLocaleTimeString()}
            </div>
          </div>

          {statusMsg && (
            <div className="alert alert-success" style={{ marginTop: '1rem', marginBottom: 0 }}>
              {statusMsg}
            </div>
          )}
          {error && (
            <div className="alert alert-error" style={{ marginTop: '1rem', marginBottom: 0 }}>
              {error}
            </div>
          )}
        </div>

        {/* Main Layout: Video + Results */}
        <div className="monitor-layout" id="monitor-layout">

          {/* Video Feed */}
          <div className="main-feed" id="main-feed">
            <div className="feed-display">
              <div className="feed-placeholder" style={{ position: 'relative', overflow: 'hidden', background: '#0f172a' }}>
                {streamActive ? (
                  <img
                    ref={imageRef}
                    src={`${videoFeedUrl}`}
                    alt="Live annotated CCTV feed"
                    style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                    onError={() => setError('Video feed unavailable. Verify the stream is active.')}
                  />
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
                    <svg viewBox="0 0 64 64" fill="none" width="56" height="56" style={{ marginBottom: '1rem' }}>
                      <rect x="8" y="12" width="48" height="32" rx="4" stroke="currentColor" strokeWidth="2" fill="none"/>
                      <circle cx="32" cy="28" r="8" stroke="currentColor" strokeWidth="2" fill="none"/>
                      <circle cx="32" cy="28" r="3" fill="currentColor"/>
                      <path d="M20 48H44" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                    <p style={{ fontWeight: '500' }}>No active stream</p>
                    <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Enter an RTSP URL above and click Start Stream</p>
                  </div>
                )}
              </div>

              <div className="feed-info-bar">
                <div className="feed-meta">
                  <span className="feed-cam-name">
                    {streamActive ? streamSource || 'Active Stream' : 'Not Connected'}
                  </span>
                  <span className={`feed-status ${streamActive ? 'online' : 'offline'}`}>
                    {streamActive ? 'Online' : 'Offline'}
                  </span>
                </div>
                <span className="feed-timestamp">
                  {currentTime.toLocaleTimeString()} | {currentTime.toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* Results Sidebar */}
          <div className="camera-sidebar" id="results-sidebar">
            <h3 className="sidebar-title">Detection Results</h3>

            {results.length === 0 ? (
              <div style={{ padding: '1rem 0', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
                {streamActive ? 'Waiting for face detections...' : 'Start a stream to see results'}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '420px', overflowY: 'auto' }}>
                {results.map((r, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '0.6rem 0.75rem',
                      background: 'var(--bg-card-hover)',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.82rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                      <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                        {r.name || 'Unknown'}
                      </span>
                      <span style={{
                        fontWeight: '600',
                        color: r.confidence >= 80 ? 'var(--color-danger)' : 'var(--color-warning)'
                      }}>
                        {r.confidence?.toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-muted)' }}>
                      ID: {r.person_id} &nbsp;|&nbsp;
                      Frame: {r.frame_index ?? r.frame}
                    </div>
                    <div style={{ color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                      {r.timestamp ? new Date(r.timestamp * 1000).toLocaleTimeString() : ''}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="sidebar-stats" style={{ marginTop: '1rem' }}>
              <div className="sidebar-stat">
                <span className="sidebar-stat-value">{results.length}</span>
                <span className="sidebar-stat-label">Detections</span>
              </div>
              <div className="sidebar-stat">
                <span className="sidebar-stat-value">
                  {results.filter(r => r.confidence >= 80).length}
                </span>
                <span className="sidebar-stat-label">High Conf.</span>
              </div>
              <div className="sidebar-stat">
                <span className="sidebar-stat-value">
                  {new Set(results.map(r => r.person_id)).size}
                </span>
                <span className="sidebar-stat-label">Unique IDs</span>
              </div>
            </div>

            {results.length > 0 && (
              <button
                className="btn btn-ghost btn-sm"
                style={{ marginTop: '0.75rem', width: '100%' }}
                onClick={() => setResults([])}
              >
                Clear Results
              </button>
            )}
          </div>
        </div>

        {/* Usage Note */}
        <div style={{
          marginTop: '1.5rem',
          padding: '0.75rem 1rem',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '6px',
          fontSize: '0.8rem',
          color: 'var(--text-muted)'
        }}>
          <strong style={{ color: 'var(--text-secondary)' }}>RTSP Format:</strong>
          &nbsp; rtsp://username:password@ip_address:port/stream_path
          &nbsp;&nbsp;|&nbsp;&nbsp;
          <strong style={{ color: 'var(--text-secondary)' }}>Webcam:</strong>
          &nbsp; Enter 0 (or leave blank) to use the local webcam.
          &nbsp;&nbsp;|&nbsp;&nbsp;
          The raw RTSP feed is never sent to the browser — all processing is server-side.
        </div>

      </div>
    </div>
  );
}
