import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

export const Navigation: React.FC = () => {
  const location = useLocation();
  
  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <Link to="/" className="brand-link">
            <span className="brand-icon">🧊</span>
            <span className="brand-text">Cool Mint</span>
          </Link>
        </div>
        
        <div className="nav-links">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            <span className="nav-icon">🏠</span>
            Home
          </Link>
          
          <div className="nav-section">
            <span className="nav-section-title">AI-Enabled CRM</span>
            <Link 
              to="/activities" 
              className={`nav-link ${isActive('/activities') ? 'active' : ''}`}
            >
              <span className="nav-icon">📊</span>
              Activity Selector
            </Link>
            
            <Link 
              to="/bundles" 
              className={`nav-link ${isActive('/bundles') ? 'active' : ''}`}
            >
              <span className="nav-icon">📦</span>
              Bundle Manager
            </Link>
            
            <Link 
              to="/contacts" 
              className={`nav-link ${isActive('/contacts') ? 'active' : ''}`}
            >
              <span className="nav-icon">🗺️</span>
              Market Explorer
            </Link>
            
            <Link 
              to="/relationships" 
              className={`nav-link ${isActive('/relationships') ? 'active' : ''}`}
            >
              <span className="nav-icon">🤝</span>
              Relationship Manager
            </Link>
            
            <Link 
              to="/juno" 
              className={`nav-link ${isActive('/juno') ? 'active' : ''}`}
            >
              <span className="nav-icon">🤖</span>
              Juno Assistant
            </Link>
          </div>
          
          <div className="nav-section nav-section-future">
            <span className="nav-section-title">Coming Soon</span>
            
            <div className="nav-link disabled">
              <span className="nav-icon">📈</span>
              Referral Analyzer
              <span className="coming-soon-badge">Soon</span>
            </div>
          </div>
        </div>
        
        <div className="nav-footer">
          <div className="nav-version">v1.0.0</div>
        </div>
      </div>
    </nav>
  );
};