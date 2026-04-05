import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinks = [
    { path: '/dashboard',        label: 'Dashboard',        icon: '⊞' },
    { path: '/missing-persons',  label: 'Missing Persons',  icon: '' },
    { path: '/add-person',       label: 'Add Person',       icon: '＋' },
    { path: '/upload-video',     label: 'Upload CCTV',      icon: '⎗' },
    { path: '/results',          label: 'Results',          icon: '◉' },
    { path: '/live-monitoring',  label: 'Live Monitor',     icon: '◎' },
  ];

  return (
    <nav className="navbar" id="main-navbar">
      <div className="navbar-inner">
        <Link to="/dashboard" className="navbar-brand" id="navbar-brand">
          <span className="brand-icon"></span>
          <span className="brand-text">MPDS</span>
        </Link>

        <button 
          className={`hamburger ${mobileOpen ? 'active' : ''}`}
          onClick={() => setMobileOpen(!mobileOpen)}
          id="hamburger-btn"
          aria-label="Toggle navigation"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <div className={`navbar-links ${mobileOpen ? 'open' : ''}`}>
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
              id={`nav-link-${link.path.slice(1)}`}
            >
              <span className="nav-icon">{link.icon}</span>
              <span className="nav-label">{link.label}</span>
            </Link>
          ))}
        </div>

        <div className="navbar-actions">
          {user && (
            <div className="user-section">
              <div className="user-avatar" id="user-avatar">
                {user.name?.charAt(0) || 'A'}
              </div>
              <button 
                className="btn btn-ghost btn-sm" 
                onClick={handleLogout}
                id="logout-btn"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
