import React from 'react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-content">
        <p>
          Copyright © {currentYear} TU Delft - Research & Education IT (REIT)
        </p>
        <p className="footer-links">
          <a
            href="https://gitlab.ewi.tudelft.nl/reit/slurm-usage-history"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitLab Repository
          </a>
          {' • '}
          <a
            href="http://localhost:8100/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            API Documentation
          </a>
        </p>
      </div>
    </footer>
  );
};

export default Footer;
