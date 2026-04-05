import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

export default function ResultsPage() {
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [activeTasks, setActiveTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/results', {
          headers: {
            'Authorization': `Bearer ${user?.token}`
          }
        });
        const tasksRes = await fetch('http://localhost:8000/api/active-tasks', {
          headers: { 'Authorization': `Bearer ${user?.token}` }
        });
        
        const data = await response.json();
        const tasksData = await tasksRes.json();
        
        if (response.ok && data.status === 'success') {
          const formatted = data.data.map(item => ({
            id: item.id,
            personName: item.person_name,
            matchConfidence: item.confidence_score,
            location: item.camera_id ? `Camera #${item.camera_id}` : 'Uploaded Video',
            timestamp: new Date(item.timestamp).toLocaleString(),
            status: item.status || 'pending',
            videoTime: item.video_time_sec ? `${Math.floor(item.video_time_sec / 60)}:${Math.floor(item.video_time_sec % 60).toString().padStart(2, '0')}` : null,
            snapshotPath: item.snapshot_path
          }));
          setResults(formatted);
        } else {
          setError(data.message || 'Failed to fetch results');
        }

        if (tasksRes.ok && tasksData.status === 'success') {
          setActiveTasks(tasksData.data || []);
        }
      } catch (err) {
        setError('Network error loading results');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchResults();
    const interval = setInterval(fetchResults, 5000);
    return () => clearInterval(interval);
  }, [user]);

  const updateStatus = async (id, newStatus) => {
    try {
      const res = await fetch(`http://localhost:8000/api/results/${id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user?.token}`
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        setResults(prev => prev.map(r => r.id === id ? { ...r, status: newStatus } : r));
      }
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const deleteResult = async (id) => {
    if (!window.confirm('Are you sure you want to completely delete this detection record?')) return;
    try {
      const res = await fetch(`http://localhost:8000/api/results/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${user?.token}`
        }
      });
      if (res.ok) {
        setResults(prev => prev.filter(r => r.id !== id));
      }
    } catch (err) {
      console.error("Failed to delete", err);
    }
  };

  const filteredResults = results.filter(r => {
    const matchesFilter = filter === 'all' || r.status === filter;
    const matchesSearch = r.personName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.location.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusBadge = (status) => {
    const map = {
      confirmed: { label: 'Confirmed', className: 'badge-success' },
      pending: { label: 'Pending', className: 'badge-warning' },
      reviewing: { label: 'Reviewing', className: 'badge-info' },
      dismissed: { label: 'Dismissed', className: 'badge-muted' },
    };
    return map[status] || { label: status, className: 'badge-muted' };
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 90) return 'var(--color-success)';
    if (confidence >= 75) return 'var(--color-warning)';
    return 'var(--color-danger)';
  };

  return (
    <div className="results-page" id="results-page">
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <div className="page-header-icon success">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="14" cy="14" r="8" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M20 20L28 28" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <h1 className="page-title">Detection Results</h1>
            <p className="page-subtitle">Review AI-powered face matching results from surveillance footage.</p>
          </div>
        </div>

        {/* Filters */}
        <div className="results-toolbar" id="results-toolbar">
          <div className="search-box">
            <span className="search-icon">⌕</span>
            <input
              type="text"
              className="form-input"
              placeholder="Search by name or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              id="results-search"
            />
          </div>
          <div className="filter-chips">
            {['all', 'confirmed', 'pending', 'reviewing', 'dismissed'].map(f => (
              <button
                key={f}
                className={`chip ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
                id={`filter-${f}`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Results Grid */}
        <div className="results-grid" id="results-grid">
          {isLoading ? (
            <div className="empty-state">
              <span className="btn-loader" style={{borderTopColor: 'var(--color-primary)', width: '3rem', height: '3rem'}}></span>
              <p>Loading results...</p>
            </div>
          ) : error ? (
            <div className="empty-state" style={{color: 'var(--color-danger)'}}>
              <p>{error}</p>
            </div>
          ) : filteredResults.length === 0 ? (
            <div className="empty-state">
              <svg viewBox="0 0 64 64" fill="none" width="64" height="64" opacity="0.3">
                <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="2"/>
                <path d="M22 38C22 38 26 34 32 34C38 34 42 38 42 38" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                <circle cx="24" cy="26" r="2" fill="currentColor"/>
                <circle cx="40" cy="26" r="2" fill="currentColor"/>
              </svg>
              <p>No results match your filters</p>
            </div>
          ) : (
            <>
              {/* Render Active Processing Tasks First outside of normal filters if in all or pending view */}
              {(filter === 'all' || filter === 'pending') && activeTasks.map(task => (
                <div
                  className="result-card"
                  key={task.id}
                  style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', opacity: 0.8 }}
                >
                  <div style={{ 
                      height: '180px', 
                      backgroundColor: 'var(--bg-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderBottom: '1px solid var(--border-color)',
                      flexDirection: 'column'
                    }}
                  >
                    <span className="btn-loader" style={{ borderTopColor: 'var(--color-primary)', width: '2rem', height: '2rem', marginBottom: '1rem' }}></span>
                    <span style={{ color: 'var(--text-secondary)' }}>Analyzing Video...</span>
                  </div>
                  <div className="result-content" style={{ padding: '1.25rem' }}>
                    <div className="result-header" style={{ padding: 0, borderBottom: 'none', marginBottom: '1rem' }}>
                      <div className="result-avatar" style={{ width: '32px', height: '32px', backgroundColor: 'var(--color-warning)' }}>
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="white" strokeWidth="2" fill="none"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                      </div>
                      <div className="result-info">
                        <h3 className="result-name" style={{ fontSize: '1.1rem' }}>Pending Target</h3>
                      </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.2rem 0', marginBottom: '0.5rem' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Status</span>
                      <span className="badge badge-warning">Processing</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.2rem 0' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Task Started</span>
                      <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{new Date(task.started_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
              ))}

              {/* Render Actual Results */}
              {filteredResults.map((result, i) => {
                const badge = getStatusBadge(result.status);
                return (
                  <div
                    className="result-card"
                  key={result.id}
                  id={`result-${result.id}`}
                  style={{ animationDelay: `${i * 0.08}s`, padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
                >
                  {/* Thumbnail / Image Reveal */}
                  <div 
                    onClick={() => window.open(`http://localhost:8000/${result.snapshotPath}`, '_blank')}
                    style={{ 
                      height: '180px', 
                      backgroundImage: result.snapshotPath ? `url(http://localhost:8000/${result.snapshotPath})` : 'none',
                      backgroundColor: 'var(--bg-secondary)',
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                      position: 'relative',
                      cursor: 'pointer',
                      borderBottom: '1px solid var(--border-color)'
                    }}
                  >
                    {!result.snapshotPath && (
                      <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                        No Image Available
                      </div>
                    )}
                    
                    {/* Floating Badges */}
                    <span 
                      className={`badge ${badge.className}`} 
                      style={{ position: 'absolute', top: '12px', right: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}
                    >
                      {badge.label}
                    </span>
                    <div 
                      style={{ 
                        position: 'absolute', 
                        bottom: '12px', 
                        left: '12px', 
                        background: 'rgba(0, 0, 0, 0.75)', 
                        backdropFilter: 'blur(4px)',
                        padding: '4px 8px', 
                        borderRadius: '6px', 
                        fontSize: '0.85rem', 
                        color: getConfidenceColor(result.matchConfidence), 
                        fontWeight: '600',
                        border: `1px solid ${getConfidenceColor(result.matchConfidence)}40`
                      }}
                    >
                      {result.matchConfidence}% Match
                    </div>
                  </div>

                  <div className="result-content" style={{ padding: '1.25rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <div className="result-header" style={{ padding: 0, borderBottom: 'none', marginBottom: '1rem' }}>
                      <div className="result-avatar" style={{ width: '32px', height: '32px', fontSize: '1rem' }}>
                        {result.personName.charAt(0)}
                      </div>
                      <div className="result-info">
                        <h3 className="result-name" style={{ fontSize: '1.1rem' }}>{result.personName}</h3>
                      </div>
                    </div>

                    <div className="result-body" style={{ gap: '0.5rem', marginBottom: '1.5rem', flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.2rem 0' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Source</span>
                        <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{result.location}</span>
                      </div>
                      {result.videoTime && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.2rem 0' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>Video Time</span>
                          <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{result.videoTime}</span>
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '0.2rem 0' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Logged On</span>
                        <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                          {result.timestamp.split(', ').length > 1 ? result.timestamp.split(', ')[1] : result.timestamp}
                        </span>
                      </div>
                    </div>
                    
                    {/* Streamlined Action Buttons */}
                    <div className="result-actions" style={{ display: 'flex', gap: '0.5rem' }}>
                      {result.status !== 'confirmed' && (
                        <button 
                          className="btn btn-sm btn-primary" 
                          onClick={() => updateStatus(result.id, 'confirmed')}
                          style={{ flex: 1, backgroundColor: 'var(--color-success)', color: 'white', border: 'none' }}
                        >
                          Confirm
                        </button>
                      )}
                      
                      {result.status !== 'dismissed' && (
                        <button 
                          className="btn btn-sm" 
                          onClick={() => updateStatus(result.id, 'dismissed')}
                          style={{ flex: 1, backgroundColor: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}
                        >
                          Dismiss
                        </button>
                      )}

                      <button 
                        className="btn btn-sm" 
                        onClick={() => deleteResult(result.id)}
                        style={{ padding: '0.4rem 0.6rem', backgroundColor: 'transparent', border: '1px solid var(--color-danger)', color: 'var(--color-danger)' }}
                        title="Delete Record"
                      >
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              );
              })}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
