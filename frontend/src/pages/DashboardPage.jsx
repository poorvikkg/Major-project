import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';

export default function DashboardPage() {
  const { user } = useAuth();

  const features = [
    {
      id: 'add-person',
      title: 'Add Missing Person',
      description: 'Register a new missing person with their details and photograph.',
      icon: (
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="16" r="8" stroke="currentColor" strokeWidth="2.5" fill="none"/>
          <path d="M10 40C10 33.37 15.37 28 22 28H26C32.63 28 38 33.37 38 40" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
          <circle cx="36" cy="36" r="8" fill="var(--color-primary)" opacity="0.2"/>
          <path d="M36 32V40M32 36H40" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      ),
      path: '/add-person',
      color: 'primary',
    },
    {
      id: 'missing-persons',
      title: 'Missing Persons Registry',
      description: 'Browse all registered missing persons, filter by status, and view case details.',
      icon: (
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="18" cy="16" r="7" stroke="currentColor" strokeWidth="2.5" fill="none"/>
          <path d="M4 40C4 33 10 28 18 28" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
          <circle cx="34" cy="20" r="5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.6"/>
          <path d="M24 40C24 34.5 28.5 30 34 30" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.6"/>
          <path d="M40 34L44 38" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4"/>
        </svg>
      ),
      path: '/missing-persons',
      color: 'info',
    },
    {
      id: 'upload-video',
      title: 'Upload CCTV Video',
      description: 'Upload surveillance footage for AI-powered face detection and matching.',
      icon: (
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="4" y="10" width="28" height="22" rx="3" stroke="currentColor" strokeWidth="2.5" fill="none"/>
          <path d="M32 18L42 12V30L32 24" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" fill="none"/>
          <circle cx="18" cy="21" r="5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.5"/>
          <path d="M10 38L18 30L24 36L32 26L38 34" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.3"/>
        </svg>
      ),
      path: '/upload-video',
      color: 'accent',
    },
    {
      id: 'view-results',
      title: 'View Results',
      description: 'Review detection results, matched faces, and confidence scores.',
      icon: (
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="20" cy="20" r="12" stroke="currentColor" strokeWidth="2.5" fill="none"/>
          <path d="M28 28L40 40" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
          <circle cx="20" cy="20" r="5" stroke="currentColor" strokeWidth="1.5" fill="none" opacity="0.4"/>
          <path d="M20 14V20H26" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.4"/>
        </svg>
      ),
      path: '/results',
      color: 'success',
    },
    {
      id: 'live-monitoring',
      title: 'Live Monitoring',
      description: 'Real-time surveillance feed monitoring with instant alert system.',
      icon: (
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="6" y="8" width="36" height="24" rx="3" stroke="currentColor" strokeWidth="2.5" fill="none"/>
          <path d="M6 36H42" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
          <path d="M18 36V40H30V36" stroke="currentColor" strokeWidth="2" fill="none"/>
          <circle cx="24" cy="20" r="2" fill="var(--color-danger)"/>
          <circle cx="24" cy="20" r="5" stroke="var(--color-danger)" strokeWidth="1" fill="none" opacity="0.5"/>
          <circle cx="24" cy="20" r="8" stroke="var(--color-danger)" strokeWidth="0.75" fill="none" opacity="0.25"/>
        </svg>
      ),
      path: '/live-monitoring',
      color: 'danger',
    },
  ];

  const stats = [
    { label: 'Cases Active', value: '24', trend: '+3', trendUp: true },
    { label: 'Persons Found', value: '156', trend: '+12', trendUp: true },
    { label: 'CCTV Sources', value: '48', trend: '+5', trendUp: true },
    { label: 'Alerts Today', value: '7', trend: '-2', trendUp: false },
  ];

  return (
    <div className="dashboard-page" id="dashboard-page">
      <Navbar />
      <div className="page-container">
        {/* Hero Section */}
        <section className="dashboard-hero" id="dashboard-hero">
          <div className="hero-content">
            <div className="hero-badge">🛡 Control Center</div>
            <h1 className="hero-title">
              Welcome back, <span className="text-gradient">{user?.name || 'Admin'}</span>
            </h1>
            <p className="hero-subtitle">
              Monitor surveillance feeds, manage missing person records, and review AI detection results from a single command center.
            </p>
          </div>
          <div className="hero-visual">
            <div className="pulse-ring pulse-ring-1"></div>
            <div className="pulse-ring pulse-ring-2"></div>
            <div className="pulse-ring pulse-ring-3"></div>
            <div className="pulse-center">
              <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" width="48" height="48">
                <circle cx="32" cy="24" r="10" stroke="white" strokeWidth="2" fill="none"/>
                <path d="M14 52C14 42 22 36 32 36C42 36 50 42 50 52" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none"/>
              </svg>
            </div>
          </div>
        </section>

        {/* Stats Row */}
        <section className="stats-row" id="stats-section">
          {stats.map((stat, i) => (
            <div className="stat-card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
              <p className="stat-value">{stat.value}</p>
              <p className="stat-label">{stat.label}</p>
              <span className={`stat-trend ${stat.trendUp ? 'up' : 'down'}`}>
                {stat.trendUp ? '↑' : '↓'} {stat.trend}
              </span>
            </div>
          ))}
        </section>

        {/* Feature Cards */}
        <section className="features-grid" id="features-grid">
          {features.map((feature, i) => (
            <Link
              to={feature.path}
              key={feature.id}
              className={`feature-card feature-card-${feature.color}`}
              id={`feature-${feature.id}`}
              style={{ animationDelay: `${i * 0.1 + 0.2}s` }}
            >
              <div className="feature-icon">
                {feature.icon}
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
              <div className="feature-arrow">
                <span>→</span>
              </div>
            </Link>
          ))}
        </section>
      </div>
    </div>
  );
}
