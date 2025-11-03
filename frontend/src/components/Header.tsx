import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">Slurm Usage History Dashboard</h1>
        <nav className="header-nav">
          <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            Overview
          </button>
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
          <button onClick={() => window.open('https://github.com', '_blank')}>
            Help
          </button>
        </nav>
      </div>
    </header>
  );
};

export default Header;
