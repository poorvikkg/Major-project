import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Email is required');
      return;
    }
    if (!password.trim()) {
      setError('Password is required');
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));

    const result = login(email, password);
    setIsLoading(false);

    if (result.success) {
      navigate(from, { replace: true });
    } else {
      setError(result.message);
    }
  };

  return (
    <div className="login-page" id="login-page">
      {/* Background animated elements */}
      <div className="login-bg">
        <div className="bg-orb bg-orb-1"></div>
        <div className="bg-orb bg-orb-2"></div>
        <div className="bg-orb bg-orb-3"></div>
        <div className="grid-overlay"></div>
      </div>

      <div className="login-container">
        <div className="login-card" id="login-card">
          <div className="login-header">
            <div className="login-logo">
              <div className="logo-shield">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="shield-svg">
                  <path d="M12 2L3 7V12C3 17.55 6.84 22.74 12 24C17.16 22.74 21 17.55 21 12V7L12 2Z" fill="url(#shieldGrad)" opacity="0.2"/>
                  <path d="M12 2L3 7V12C3 17.55 6.84 22.74 12 24C17.16 22.74 21 17.55 21 12V7L12 2Z" stroke="url(#shieldGrad)" strokeWidth="1.5" fill="none"/>
                  <circle cx="12" cy="10" r="3" stroke="url(#shieldGrad)" strokeWidth="1.5" fill="none"/>
                  <path d="M7 18C7 15.5 9.5 14 12 14C14.5 14 17 15.5 17 18" stroke="url(#shieldGrad)" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
                  <defs>
                    <linearGradient id="shieldGrad" x1="3" y1="2" x2="21" y2="24">
                      <stop stopColor="#6366f1"/>
                      <stop offset="1" stopColor="#a855f7"/>
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
            <h1 className="login-title" id="login-title">Welcome Back</h1>
            <p className="login-subtitle">Missing Person Detection System</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form" id="login-form">
            {error && (
              <div className="alert alert-error" id="login-error">
                <span className="alert-icon">⚠</span>
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email" className="form-label">Email Address</label>
              <div className="input-wrapper">
                <span className="input-icon">✉</span>
                <input
                  type="email"
                  id="email"
                  className="form-input"
                  placeholder="admin@mpds.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <div className="input-wrapper">
                <span className="input-icon">🔒</span>
                <input
                  type="password"
                  id="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button 
              type="submit" 
              className={`btn btn-primary btn-full ${isLoading ? 'loading' : ''}`}
              disabled={isLoading}
              id="login-submit-btn"
            >
              {isLoading ? (
                <span className="btn-loader"></span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="login-footer">
            <p className="login-hint">Demo: admin@mpds.com / admin123</p>
          </div>
        </div>
      </div>
    </div>
  );
}
