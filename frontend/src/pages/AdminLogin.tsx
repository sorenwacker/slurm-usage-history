import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminClient } from '../api/adminClient';
import './AdminLogin.css';

export function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await adminClient.login(username, password);
      navigate('/admin/clusters');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-wrapper">
        {/* Login Card */}
        <div className="login-card">
          {/* Header */}
          <div className="login-header">
            <div className="login-icon">
              <span>🔐</span>
            </div>
            <h2 className="login-title">Admin Login</h2>
            <p className="login-subtitle">
              SLURM Usage History - Cluster Management
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="login-error">
              <div className="login-error-content">
                <span className="login-error-icon">⚠️</span>
                <div className="login-error-text">{error}</div>
                <button
                  onClick={() => setError('')}
                  className="login-error-close"
                >
                  ×
                </button>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="login-form" onSubmit={handleSubmit}>
            {/* Username */}
            <div className="login-form-group">
              <label htmlFor="username" className="login-label">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="login-input"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            {/* Password */}
            <div className="login-form-group">
              <label htmlFor="password" className="login-label">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="login-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="login-submit"
            >
              {loading ? (
                <>
                  <div className="login-spinner"></div>
                  Logging in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>
        </div>

        {/* Back Link */}
        <div className="login-back">
          <a href="/" className="login-back-link">
            <span className="login-back-arrow">←</span>
            Back to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
