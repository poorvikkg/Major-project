import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';

const CAMERA_FEEDS = [
  { id: 1, name: 'MG Road Junction', location: 'Camera #12', status: 'online', alerts: 2 },
  { id: 2, name: 'Bus Station Gate 3', location: 'Camera #07', status: 'online', alerts: 0 },
  { id: 3, name: 'Railway Station P2', location: 'Camera #22', status: 'online', alerts: 1 },
  { id: 4, name: 'Shopping Mall Entrance', location: 'Camera #15', status: 'offline', alerts: 0 },
  { id: 5, name: 'Park Entrance', location: 'Camera #03', status: 'online', alerts: 0 },
  { id: 6, name: 'Highway Toll Gate', location: 'Camera #31', status: 'online', alerts: 3 },
];

export default function LiveMonitoringPage() {
  const [selectedCamera, setSelectedCamera] = useState(CAMERA_FEEDS[0]);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="live-monitoring-page" id="live-monitoring-page">
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <div className="page-header-icon danger">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="6" width="24" height="16" rx="2" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M4 24H28" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="16" cy="14" r="2" fill="var(--color-danger)"/>
            </svg>
          </div>
          <div>
            <h1 className="page-title">Live Monitoring</h1>
            <p className="page-subtitle">Real-time surveillance feed monitoring with instant alert notifications.</p>
          </div>
          <div className="live-indicator" id="live-indicator">
            <span className="live-dot"></span>
            LIVE
          </div>
        </div>

        <div className="monitor-layout" id="monitor-layout">
          {/* Main Feed */}
          <div className="main-feed" id="main-feed">
            <div className="feed-display">
              <div className="feed-placeholder" style={{position: 'relative', overflow: 'hidden'}}>
                {selectedCamera.id === 1 ? (
                  <img 
                    src="http://localhost:8000/api/live-stream?source=0" 
                    alt="Live Stream" 
                    style={{width: '100%', height: '100%', objectFit: 'cover'}}
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : null}
                
                <div style={{display: selectedCamera.id === 1 ? 'none' : 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%'}}>
                  <div className="scan-line"></div>
                  <div className="feed-overlay">
                    <div className="overlay-corner tl"></div>
                    <div className="overlay-corner tr"></div>
                    <div className="overlay-corner bl"></div>
                    <div className="overlay-corner br"></div>
                  </div>
                  <div className="feed-center-icon">
                    <svg viewBox="0 0 64 64" fill="none" width="48" height="48">
                      <rect x="8" y="12" width="48" height="32" rx="4" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.3"/>
                      <circle cx="32" cy="28" r="8" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.5"/>
                      <circle cx="32" cy="28" r="3" fill="currentColor" opacity="0.3"/>
                    </svg>
                    <p>Feed: {selectedCamera.name}</p>
                    <p style={{fontSize: '0.8rem', opacity: 0.7}}>Camera source not connected</p>
                  </div>
                </div>
              </div>
              <div className="feed-info-bar">
                <div className="feed-meta">
                  <span className="feed-cam-name">{selectedCamera.location} — {selectedCamera.name}</span>
                  <span className={`feed-status ${selectedCamera.status}`}>
                    {selectedCamera.status === 'online' ? '● Online' : '○ Offline'}
                  </span>
                </div>
                <span className="feed-timestamp">
                  {currentTime.toLocaleTimeString()} | {currentTime.toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* Camera List Sidebar */}
          <div className="camera-sidebar" id="camera-sidebar">
            <h3 className="sidebar-title">Camera Feeds</h3>
            <div className="camera-list">
              {CAMERA_FEEDS.map(cam => (
                <button
                  key={cam.id}
                  className={`camera-item ${selectedCamera.id === cam.id ? 'active' : ''} ${cam.status}`}
                  onClick={() => setSelectedCamera(cam)}
                  id={`camera-${cam.id}`}
                >
                  <div className="camera-item-info">
                    <span className={`cam-status-dot ${cam.status}`}></span>
                    <div>
                      <p className="cam-name">{cam.name}</p>
                      <p className="cam-location">{cam.location}</p>
                    </div>
                  </div>
                  {cam.alerts > 0 && (
                    <span className="alert-badge">{cam.alerts}</span>
                  )}
                </button>
              ))}
            </div>

            <div className="sidebar-stats">
              <div className="sidebar-stat">
                <span className="sidebar-stat-value">{CAMERA_FEEDS.filter(c => c.status === 'online').length}</span>
                <span className="sidebar-stat-label">Online</span>
              </div>
              <div className="sidebar-stat">
                <span className="sidebar-stat-value">{CAMERA_FEEDS.filter(c => c.status === 'offline').length}</span>
                <span className="sidebar-stat-label">Offline</span>
              </div>
              <div className="sidebar-stat">
                <span className="sidebar-stat-value">{CAMERA_FEEDS.reduce((sum, c) => sum + c.alerts, 0)}</span>
                <span className="sidebar-stat-label">Alerts</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
