import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

interface FeatureCard {
  title: string;
  description: string;
  icon: string;
  link?: string;
  isAvailable: boolean;
  stats?: {
    label: string;
    value: string | number;
  }[];
}

export const HomePage: React.FC = () => {
  const features: FeatureCard[] = [
    {
      title: 'Activity Selector',
      description: 'Browse, filter, and select healthcare activities from your Salesforce data. Create bundles for AI analysis.',
      icon: '📊',
      link: '/activities',
      isAvailable: true,
      stats: [
        { label: 'Total Activities', value: '1,277+' },
        { label: 'Ready for Analysis', value: 'Yes' }
      ]
    },
    {
      title: 'Bundle Manager',
      description: 'Manage your activity bundles and interact with Claude AI for sophisticated healthcare insights.',
      icon: '📦',
      link: '/bundles',
      isAvailable: true,
      stats: [
        { label: 'AI Model', value: 'Claude 3.5' },
        { label: 'Analysis Ready', value: 'Yes' }
      ]
    },
    {
      title: 'Market Explorer',
      description: 'Analyze claims data to identify market opportunities and generate qualified leads.',
      icon: '🔍',
      isAvailable: false,
      stats: [
        { label: 'Status', value: 'Coming Soon' },
        { label: 'Launch', value: 'Q2 2025' }
      ]
    },
    {
      title: 'Referral Analyzer',
      description: 'Review internal EHR data to understand referral pattern changes and identify growth opportunities.',
      icon: '📈',
      isAvailable: false,
      stats: [
        { label: 'Status', value: 'In Development' },
        { label: 'Launch', value: 'Q2 2025' }
      ]
    }
  ];

  return (
    <div className="home-page">
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Welcome to <span className="brand-highlight">Cool Mint</span>
          </h1>
          <p className="hero-subtitle">
            Your AI-Enabled Healthcare CRM Platform
          </p>
          <p className="hero-description">
            Leverage artificial intelligence to analyze healthcare activities, discover market opportunities, 
            and optimize your network relationships.
          </p>
          <div className="hero-actions">
            <Link to="/activities" className="hero-button primary">
              Get Started
            </Link>
            <Link to="/bundles" className="hero-button secondary">
              View Bundles
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="floating-cards">
            <div className="float-card card-1">🏥</div>
            <div className="float-card card-2">🤖</div>
            <div className="float-card card-3">📊</div>
            <div className="float-card card-4">🔬</div>
          </div>
        </div>
      </div>

      <div className="features-section">
        <h2 className="section-title">Platform Features</h2>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className={`feature-card ${!feature.isAvailable ? 'coming-soon' : ''}`}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
              
              {feature.stats && (
                <div className="feature-stats">
                  {feature.stats.map((stat, idx) => (
                    <div key={idx} className="stat-item">
                      <span className="stat-label">{stat.label}:</span>
                      <span className="stat-value">{stat.value}</span>
                    </div>
                  ))}
                </div>
              )}
              
              {feature.isAvailable && feature.link ? (
                <Link to={feature.link} className="feature-link">
                  Explore <span className="link-arrow">→</span>
                </Link>
              ) : (
                <div className="feature-badge">Coming Soon</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="info-section">
        <div className="info-card">
          <h3>🚀 What's New</h3>
          <ul>
            <li>Bundle Management with Claude AI integration</li>
            <li>Enhanced activity filtering and search</li>
            <li>Real-time token tracking for cost optimization</li>
            <li>Healthcare-specific AI analysis</li>
          </ul>
        </div>
        
        <div className="info-card">
          <h3>💡 Quick Tips</h3>
          <ul>
            <li>Start by selecting activities in the Activity Selector</li>
            <li>Create bundles to organize related activities</li>
            <li>Use Claude AI to analyze patterns and insights</li>
            <li>Save important responses for future reference</li>
          </ul>
        </div>
      </div>
    </div>
  );
};