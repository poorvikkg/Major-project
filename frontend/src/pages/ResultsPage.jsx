import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

export default function ResultsPage() {
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
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
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
          // Map backend data format to frontend expectations
          const formatted = data.data.map(item => ({
            id: item.id,
            personName: item.person_name,
            matchConfidence: item.confidence_score,
            location: item.camera_id ? `Camera #${item.camera_id}` : 'Uploaded Video',
            timestamp: new Date(item.timestamp).toLocaleString(),
            status: 'confirmed', // Assuming backend doesn't have status on logs for now
            snapshotPath: item.snapshot_path
          }));
          setResults(formatted);
        } else {
          setError(data.message || 'Failed to fetch results');
        }
      } catch (err) {
        setError('Network error loading results');
      } finally {
        setIsLoading(false);
      }
    };
    fetchResults();
  }, [user]);

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
            filteredResults.map((result, i) => {
              const badge = getStatusBadge(result.status);
              return (
                <div
                  className="result-card"
                  key={result.id}
                  id={`result-${result.id}`}
                  style={{ animationDelay: `${i * 0.08}s` }}
                >
                  <div className="result-header">
                    <div className="result-avatar">
                      {result.personName.charAt(0)}
                    </div>
                    <div className="result-info">
                      <h3 className="result-name">{result.personName}</h3>
                    </div>
                    <span className={`badge ${badge.className}`}>{badge.label}</span>
                  </div>

                  <div className="result-body">
                    <div className="result-detail">
                      <span className="detail-label"> Location</span>
                      <span className="detail-value">{result.location}</span>
                    </div>
                    <div className="result-detail">
                      <span className="detail-label"> Detected</span>
                      <span className="detail-value">{result.timestamp}</span>
                    </div>
                  </div>

                  <div className="result-footer">
                    <div className="confidence-bar-container">
                      <div className="confidence-header">
                        <span>Match Confidence</span>
                        <span style={{ color: getConfidenceColor(result.matchConfidence), fontWeight: 600 }}>
                          {result.matchConfidence}%
                        </span>
                      </div>
                      <div className="confidence-bar">
                        <div 
                          className="confidence-fill" 
                          style={{ 
                            width: `${result.matchConfidence}%`,
                            background: getConfidenceColor(result.matchConfidence)
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
