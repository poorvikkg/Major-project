import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

const API = 'http://localhost:8000';

const InfoRow = ({ label, value }) =>
  value ? (
    <div className="pd-info-row">
      <span className="pd-info-label">{label}</span>
      <span className="pd-info-value">{value}</span>
    </div>
  ) : null;

const Section = ({ title, icon, children }) => (
  <div className="pd-section">
    <h3 className="pd-section-title"><span>{icon}</span> {title}</h3>
    <div className="pd-section-body">{children}</div>
  </div>
);

export default function PersonDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [person, setPerson]     = useState(null);
  const [logs, setLogs]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [activeImg, setActiveImg] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/person/${id}`).then(r => r.json()),
      fetch(`${API}/api/results?person_id=${id}`).then(r => r.json()).catch(() => ({ data: [] })),
    ]).then(([pd, ld]) => {
      if (pd.status === 'success') setPerson(pd.data);
      else setError(pd.message || 'Person not found');
      setLogs(ld.data || []);
    }).catch(() => setError('Network error'))
      .finally(() => setLoading(false));
  }, [id]);

  const images = person?.image_path
    ? person.image_path.split(',').filter(Boolean).map(p => {
        const rel = p.replace(/\\/g, '/').replace(/.*\/data\//, '/data/');
        return `${API}${rel}`;
      })
    : [];

  const handleStatusToggle = async () => {
    const newStatus = person.status === 'missing' ? 'found' : 'missing';
    setStatusUpdating(true);
    try {
      const fd = new FormData();
      fd.append('status', newStatus);
      const res = await fetch(`${API}/api/update-person/${id}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${user?.token}` },
        body: fd,
      });
      const data = await res.json();
      if (data.status === 'success') {
        setPerson(p => ({ ...p, status: newStatus }));
      }
    } finally {
      setStatusUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete the record for "${person.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API}/api/delete-person/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${user?.token}` },
      });
      const data = await res.json();
      if (data.status === 'success') navigate('/missing-persons');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return (
    <div className="pd-page"><Navbar />
      <div className="pd-loading"><div className="loader" /><p>Loading case record…</p></div>
    </div>
  );

  if (error) return (
    <div className="pd-page"><Navbar />
      <div className="page-container">
        <div className="alert alert-error">{error}</div>
        <Link to="/missing-persons" className="btn btn-ghost" style={{marginTop:'1rem'}}>← Back to List</Link>
      </div>
    </div>
  );

  const p = person;
  const isFound = p.status === 'found';

  return (
    <div className="pd-page" id="person-detail-page">
      <Navbar />
      <div className="page-container pd-container">

        {/* Breadcrumb */}
        <nav className="pd-breadcrumb">
          <Link to="/missing-persons" className="pd-breadcrumb-link">Missing Persons</Link>
          <span className="pd-breadcrumb-sep">›</span>
          <span>{p.name}</span>
        </nav>

        <div className="pd-layout">

          {/* ── LEFT: Image Gallery + Quick Info ─── */}
          <aside className="pd-sidebar">

            {/* Gallery */}
            <div className="pd-gallery">
              <div className="pd-gallery-main">
                {images.length > 0 ? (
                  <img src={images[activeImg]} alt={p.name} className="pd-gallery-img" id="gallery-main-img" />
                ) : (
                  <div className="pd-gallery-placeholder">
                    <svg viewBox="0 0 64 64" fill="none" width="48" height="48">
                      <circle cx="32" cy="24" r="10" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.3"/>
                      <path d="M14 56C14 44 22 36 32 36C42 36 50 44 50 56" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.3"/>
                    </svg>
                    <p>No photos</p>
                  </div>
                )}
                <div className={`pd-gallery-status-badge ${isFound ? 'found' : 'missing'}`}>
                  {isFound ? ' Found' : ' Missing'}
                </div>
              </div>
              {images.length > 1 && (
                <div className="pd-gallery-thumbs">
                  {images.map((src, i) => (
                    <button
                      key={i}
                      type="button"
                      className={`pd-gallery-thumb-btn${activeImg === i ? ' active' : ''}`}
                      onClick={() => setActiveImg(i)}
                      id={`gallery-thumb-${i}`}
                    >
                      <img src={src} alt={`Photo ${i + 1}`} />
                    </button>
                  ))}
                </div>
              )}
              {images.length > 0 && (
                <p className="pd-gallery-count">{images.length} photo{images.length > 1 ? 's' : ''} available</p>
              )}
            </div>

            {/* Quick Stats */}
            <div className="pd-quick-stats">
              <div className="pd-qs-item"><span className="pd-qs-label">Case ID</span><span className="pd-qs-val">#{p.id}</span></div>
              <div className="pd-qs-item"><span className="pd-qs-label">Status</span><span className={`pd-qs-val ${isFound ? 'color-success' : 'color-danger'}`}>{isFound ? 'Found' : 'Missing'}</span></div>
              <div className="pd-qs-item"><span className="pd-qs-label">Age</span><span className="pd-qs-val">{p.age} yrs</span></div>
              <div className="pd-qs-item"><span className="pd-qs-label">Gender</span><span className="pd-qs-val">{p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : '—'}</span></div>
              {p.blood_group && <div className="pd-qs-item"><span className="pd-qs-label">Blood Group</span><span className="pd-qs-val">{p.blood_group}</span></div>}
              {p.nationality && <div className="pd-qs-item"><span className="pd-qs-label">Nationality</span><span className="pd-qs-val">{p.nationality}</span></div>}
              <div className="pd-qs-item"><span className="pd-qs-label">Registered</span><span className="pd-qs-val">{p.created_at ? new Date(p.created_at).toLocaleDateString('en-IN') : '—'}</span></div>
            </div>

            {/* Admin Actions */}
            {user && (
              <div className="pd-actions">
                <button
                  type="button"
                  className={`btn btn-full ${isFound ? 'btn-ghost' : 'btn-primary'}`}
                  onClick={handleStatusToggle}
                  disabled={statusUpdating}
                  id="btn-toggle-status"
                >
                  {statusUpdating ? <><span className="btn-loader"/> Updating…</> : isFound ? 'Mark as Missing' : ' Mark as Found'}
                </button>
                <button
                  type="button"
                  className="btn btn-full btn-danger"
                  onClick={handleDelete}
                  disabled={deleting}
                  id="btn-delete-person"
                >
                  {deleting ? <><span className="btn-loader"/> Deleting…</> : ' Delete Record'}
                </button>
              </div>
            )}
          </aside>

          {/* ── RIGHT: Detailed Info ─────────────────── */}
          <main className="pd-main">

            {/* Name Header */}
            <div className="pd-name-block">
              <h1 className="pd-name">{p.name}</h1>
              {p.nickname && <p className="pd-alias">aka "{p.nickname}"</p>}
            </div>

            {/* A. Personal Details */}
            <Section title="Personal Details" icon="">
              <InfoRow label="Full Name"    value={p.name} />
              <InfoRow label="Nickname"     value={p.nickname} />
              <InfoRow label="Age"          value={p.age ? `${p.age} years` : null} />
              <InfoRow label="Gender"       value={p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : null} />
              <InfoRow label="Date of Birth" value={p.date_of_birth} />
              <InfoRow label="Height"       value={p.height} />
              <InfoRow label="Weight"       value={p.weight} />
              <InfoRow label="Complexion"   value={p.complexion} />
              <InfoRow label="Blood Group"  value={p.blood_group} />
              <InfoRow label="Nationality"  value={p.nationality} />
            </Section>

            {/* B. Physical Identification */}
            <Section title="Physical Identification" icon="">
              <InfoRow label="Face Shape"   value={p.face_shape} />
              <InfoRow label="Hair Color"   value={p.hair_color} />
              <InfoRow label="Eye Color"    value={p.eye_color} />
              <InfoRow label="Beard / Moustache" value={p.beard_mustache} />
              {p.has_disability && <InfoRow label="Disability" value={p.disability_details || 'Yes (details not specified)'} />}
              {p.identification_marks && (
                <div className="pd-text-block">
                  <span className="pd-info-label">Identification Marks</span>
                  <p className="pd-text-value">{p.identification_marks}</p>
                </div>
              )}
            </Section>

            {/* C. Last Seen */}
            <Section title="Last Seen Details" icon="">
              <InfoRow label="Location"    value={p.last_seen_location} />
              <InfoRow label="Date"        value={p.last_seen_date} />
              <InfoRow label="Time"        value={p.last_seen_time} />
              <InfoRow label="Wearing"     value={p.last_seen_wearing} />
              <InfoRow label="Accompanied By" value={p.accompanied_by} />
              <InfoRow label="Suspected Location" value={p.suspected_location} />
            </Section>

            {/* D. Additional */}
            <Section title="Additional Information" icon="">
              <InfoRow label="Occupation"   value={p.occupation} />
              <InfoRow label="Languages"    value={p.languages_known} />
              {p.habits && (
                <div className="pd-text-block">
                  <span className="pd-info-label">Habits</span>
                  <p className="pd-text-value">{p.habits}</p>
                </div>
              )}
              {p.medical_conditions && (
                <div className="pd-text-block">
                  <span className="pd-info-label">Medical Conditions</span>
                  <p className="pd-text-value">{p.medical_conditions}</p>
                </div>
              )}
              {p.behavioral_notes && (
                <div className="pd-text-block">
                  <span className="pd-info-label">Behavioural Notes</span>
                  <p className="pd-text-value">{p.behavioral_notes}</p>
                </div>
              )}
              {p.description && (
                <div className="pd-text-block">
                  <span className="pd-info-label">Additional Remarks</span>
                  <p className="pd-text-value">{p.description}</p>
                </div>
              )}
            </Section>

            {/* E. Complainant */}
            {p.complainant && (
              <Section title="Complainant Details" icon="">
                <InfoRow label="Name"        value={p.complainant.name} />
                <InfoRow label="Relation"    value={p.complainant.relation_to_person} />
                <InfoRow label="Phone"       value={p.complainant.phone_number} />
                <InfoRow label="Alt. Phone"  value={p.complainant.alternate_phone} />
                <InfoRow label="Email"       value={p.complainant.email} />
                <InfoRow label="Address"     value={p.complainant.address} />
              </Section>
            )}

            {/* F. Detection Logs */}
            <Section title="Detection Logs" icon="">
              {logs.length === 0 ? (
                <p className="pd-no-logs">No detections recorded yet for this person.</p>
              ) : (
                <div className="pd-logs">
                  {logs.map(log => (
                    <div key={log.id} className="pd-log-item" id={`log-${log.id}`}>
                      {log.snapshot_path && (
                        <img
                          src={`${API}${log.snapshot_path.replace(/\\/g, '/').replace(/.*\/data\//, '/data/')}`}
                          alt="Detection snapshot"
                          className="pd-log-snap"
                        />
                      )}
                      <div className="pd-log-info">
                        <span className="pd-log-confidence">{log.confidence_score}% match</span>
                        <span className="pd-log-time">{log.timestamp ? new Date(log.timestamp).toLocaleString('en-IN') : '—'}</span>
                        {log.camera_id && <span className="pd-log-cam">Camera #{log.camera_id}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Section>

          </main>
        </div>
      </div>
    </div>
  );
}
