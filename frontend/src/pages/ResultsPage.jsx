import { useState } from 'react';
import Navbar from '../components/Navbar';

const MOCK_RESULTS = [
  {
    id: 1,
    personName: 'Rahul Sharma',
    age: 28,
    matchConfidence: 94.2,
    location: 'Camera #12 — MG Road Junction',
    timestamp: '2026-03-28 14:32:18',
    status: 'confirmed',
  },
  {
    id: 2,
    personName: 'Priya Patel',
    age: 35,
    matchConfidence: 87.5,
    location: 'Camera #07 — Bus Station Gate 3',
    timestamp: '2026-03-28 11:05:42',
    status: 'pending',
  },
  {
    id: 3,
    personName: 'Arjun Mehta',
    age: 16,
    matchConfidence: 78.1,
    location: 'Camera #22 — Railway Station Platform 2',
    timestamp: '2026-03-27 22:15:09',
    status: 'reviewing',
  },
  {
    id: 4,
    personName: 'Kavitha Nair',
    age: 42,
    matchConfidence: 91.8,
    location: 'Camera #15 — Shopping Mall Entrance',
    timestamp: '2026-03-27 16:48:33',
    status: 'confirmed',
  },
  {
    id: 5,
    personName: 'Mohammed Ali',
    age: 55,
    matchConfidence: 65.3,
    location: 'Camera #03 — Park Entrance',
    timestamp: '2026-03-27 09:20:11',
    status: 'dismissed',
  },
];

export default function ResultsPage() {
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredResults = MOCK_RESULTS.filter(r => {
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
          {filteredResults.length === 0 ? (
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
                      <p className="result-age">Age: {result.age}</p>
                    </div>
                    <span className={`badge ${badge.className}`}>{badge.label}</span>
                  </div>

                  <div className="result-body">
                    <div className="result-detail">
                      <span className="detail-label">📍 Location</span>
                      <span className="detail-value">{result.location}</span>
                    </div>
                    <div className="result-detail">
                      <span className="detail-label">🕐 Detected</span>
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
