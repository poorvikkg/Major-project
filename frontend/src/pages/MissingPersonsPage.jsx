import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const API = 'http://localhost:8000';

export default function MissingPersonsPage() {
  const [persons, setPersons]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [filter, setFilter]     = useState('all'); // all | missing | found
  const [search, setSearch]     = useState('');

  useEffect(() => {
    const params = filter !== 'all' ? `?status_filter=${filter}` : '';
    setLoading(true);
    fetch(`${API}/api/persons${params}`)
      .then(r => r.json())
      .then(data => {
        if (data.status === 'success') setPersons(data.data || []);
        else setError(data.message || 'Failed to fetch persons');
      })
      .catch(() => setError('Network error — backend unreachable'))
      .finally(() => setLoading(false));
  }, [filter]);

  const firstImage = p => {
    if (!p.image_path) return null;
    const paths = p.image_path.split(',');
    if (!paths[0]) return null;
    // Convert absolute path to backend static URL
    const rel = paths[0].replace(/\\/g, '/').replace(/.*\/data\//, '/data/');
    return `${API}${rel}`;
  };

  const filtered = persons.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.last_seen_location || '').toLowerCase().includes(search.toLowerCase())
  );

  const statusBadge = s =>
    s === 'found'
      ? <span className="mp-badge mp-badge-found">Found</span>
      : <span className="mp-badge mp-badge-missing">Missing</span>;

  return (
    <div className="mp-page" id="missing-persons-page">
      <Navbar />
      <div className="page-container">

        {/* Header */}
        <div className="mp-header">
          <div>
            <h1 className="page-title">Missing Persons Registry</h1>
            <p className="page-subtitle">
              {loading ? 'Loading…' : `${filtered.length} record${filtered.length !== 1 ? 's' : ''} found`}
            </p>
          </div>
          <Link to="/add-person" className="btn btn-primary" id="btn-add-new">
            + Register New Case
          </Link>
        </div>

        {/* Controls */}
        <div className="mp-controls">
          <div className="mp-search-wrap">
            <span className="mp-search-icon">🔍</span>
            <input
              type="text"
              className="form-input mp-search"
              placeholder="Search by name or location…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              id="search-persons"
            />
          </div>
          <div className="mp-filters">
            {['all', 'missing', 'found'].map(f => (
              <button
                key={f}
                type="button"
                className={`chip${filter === f ? ' active' : ''}`}
                onClick={() => setFilter(f)}
                id={`filter-${f}`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* States */}
        {loading && (
          <div className="mp-state-center">
            <div className="loader" />
            <p>Loading records…</p>
          </div>
        )}

        {!loading && error && (
          <div className="alert alert-error">{error}</div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="mp-empty">
            <div className="mp-empty-icon">🔎</div>
            <h3>No records found</h3>
            <p>{search ? 'Try a different search term.' : 'No missing persons are registered yet.'}</p>
            <Link to="/add-person" className="btn btn-primary" style={{marginTop:'1rem'}}>
              Register First Case
            </Link>
          </div>
        )}

        {/* Grid */}
        {!loading && !error && filtered.length > 0 && (
          <div className="mp-grid" id="persons-grid">
            {filtered.map(p => (
              <Link
                to={`/person/${p.id}`}
                key={p.id}
                className="mp-card"
                id={`person-card-${p.id}`}
              >
                {/* Photo */}
                <div className="mp-card-photo">
                  {firstImage(p) ? (
                    <img src={firstImage(p)} alt={p.name} className="mp-card-img" />
                  ) : (
                    <div className="mp-card-no-photo">
                      <svg viewBox="0 0 48 48" fill="none" width="36" height="36">
                        <circle cx="24" cy="18" r="8" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.4"/>
                        <path d="M10 42C10 34 16 28 24 28C32 28 38 34 38 42" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.4"/>
                      </svg>
                    </div>
                  )}
                  <div className="mp-card-status">{statusBadge(p.status)}</div>
                </div>

                {/* Info */}
                <div className="mp-card-body">
                  <h3 className="mp-card-name">{p.name}</h3>
                  {p.nickname && <p className="mp-card-alias">aka {p.nickname}</p>}

                  <div className="mp-card-meta">
                    <span className="mp-meta-item">
                      <span className="mp-meta-icon">👤</span>
                      {p.age ? `${p.age} yrs` : '—'} · {p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : '—'}
                    </span>
                    {p.last_seen_location && (
                      <span className="mp-meta-item">
                        <span className="mp-meta-icon">📍</span>
                        <span className="mp-meta-truncate">{p.last_seen_location}</span>
                      </span>
                    )}
                    {p.last_seen_date && (
                      <span className="mp-meta-item">
                        <span className="mp-meta-icon">📅</span>
                        {p.last_seen_date}
                      </span>
                    )}
                  </div>

                  <div className="mp-card-footer">
                    <span className="mp-view-link">View Details →</span>
                    <span className="mp-card-id">#{p.id}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
