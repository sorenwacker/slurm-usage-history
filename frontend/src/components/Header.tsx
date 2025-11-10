import React from 'react';
import type { UserInfo } from '../api/client';

interface HeaderProps {
  activeTab?: 'overview' | 'reports';
  onTabChange?: (tab: 'overview' | 'reports') => void;
  userInfo?: UserInfo;
}

const Header: React.FC<HeaderProps> = ({ activeTab = 'overview', onTabChange, userInfo }) => {
  const handleLogout = () => {
    // Redirect to logout endpoint, then back to frontend root
    const frontendUrl = window.location.origin;
    window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:8100'}/saml/logout?redirect_to=${encodeURIComponent(frontendUrl)}`;
  };
  return (
    <header className="header">
      <div className="header-content">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <img
            src="/REIT_logo.png"
            alt="REIT Logo"
            style={{
              height: '60px',
              width: 'auto',
              backgroundColor: 'white',
              borderRadius: '0.5rem',
              padding: '0.5rem',
            }}
          />
          <h1 className="header-title">Slurm Usage History Dashboard</h1>
        </div>
        <nav className="header-nav">
          <button
            onClick={() => {
              onTabChange?.('overview');
              if (activeTab === 'overview') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }
            }}
            style={{
              padding: '0.5rem 1rem',
              color: 'white',
              backgroundColor: 'transparent',
              textDecoration: 'none',
              borderRadius: '0.375rem',
              border: '1px solid white',
              fontSize: '0.875rem',
              fontWeight: activeTab === 'overview' ? 700 : 500,
              cursor: 'pointer',
            }}
          >
            Dashboard
          </button>
          <button
            onClick={() => {
              onTabChange?.('reports');
            }}
            style={{
              padding: '0.5rem 1rem',
              color: 'white',
              backgroundColor: 'transparent',
              textDecoration: 'none',
              borderRadius: '0.375rem',
              border: '1px solid white',
              fontSize: '0.875rem',
              fontWeight: activeTab === 'reports' ? 700 : 500,
              cursor: 'pointer',
            }}
          >
            Reports
          </button>
          {userInfo && (
            <>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                padding: '0.5rem 1rem',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '0.375rem',
                gap: '0.5rem',
              }}>
                <span style={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  User
                </span>
                <span style={{
                  color: 'white',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                }}>
                  {userInfo.username || userInfo.email}
                </span>
              </div>
              {userInfo.is_admin && (
                <a
                  href="/admin/login"
                  style={{
                    padding: '0.5rem 1rem',
                    color: 'white',
                    backgroundColor: 'rgba(245, 158, 11, 0.9)',
                    textDecoration: 'none',
                    borderRadius: '0.375rem',
                    border: '1px solid rgba(251, 191, 36, 1)',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Admin
                </a>
              )}
              <button
                onClick={handleLogout}
                style={{
                  padding: '0.5rem 1rem',
                  color: 'white',
                  backgroundColor: 'transparent',
                  textDecoration: 'none',
                  borderRadius: '0.375rem',
                  border: '1px solid rgba(255, 255, 255, 0.5)',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                Logout
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Header;
