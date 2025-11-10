import React from 'react';

interface UserInfo {
  username?: string;
  email?: string;
  is_admin?: boolean;
}

interface HeaderProps {
  activeTab?: 'overview' | 'reports';
  onTabChange?: (tab: 'overview' | 'reports') => void;
  userInfo?: UserInfo | null;
}

const Header: React.FC<HeaderProps> = ({ activeTab = 'overview', onTabChange, userInfo }) => {
  const handleLogout = async () => {
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8100'}/api/saml/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
      window.location.href = '/';
    }
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
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              color: 'white',
              fontSize: '0.875rem'
            }}>
              <span style={{ opacity: 0.9 }}>
                Logged in as {userInfo.username || userInfo.email}
              </span>
              <button
                onClick={handleLogout}
                style={{
                  padding: '0.5rem 1rem',
                  color: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  textDecoration: 'none',
                  borderRadius: '0.375rem',
                  border: '1px solid white',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                Logout
              </button>
            </div>
          )}
          {userInfo?.is_admin && (
            <a
              href="/admin/login"
              className="admin-link"
              style={{
                padding: '0.5rem 1rem',
                color: '#6366f1',
                textDecoration: 'none',
                borderRadius: '0.375rem',
                border: '1px solid #6366f1',
                fontSize: '0.875rem',
                fontWeight: 500,
              }}
            >
              Admin
            </a>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Header;
