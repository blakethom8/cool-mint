import React from 'react';
import { DashboardStats } from '../types/emailActions';
import './JunoHeader.css';

interface JunoHeaderProps {
  stats?: DashboardStats;
}

const JunoHeader: React.FC<JunoHeaderProps> = ({ stats }) => {
  return (
    <div className="juno-header">
      <div className="juno-branding">
        <div className="juno-avatar">
          <span className="juno-icon">🤖</span>
        </div>
        <div className="juno-info">
          <h1 className="juno-title">Juno AI Assistant</h1>
          <p className="juno-tagline">Your intelligent email action processor</p>
        </div>
      </div>
      
      {stats && (
        <div className="juno-stats">
          <div className="stat-card pending">
            <div className="stat-value">{stats.pending_actions}</div>
            <div className="stat-label">Pending Review</div>
          </div>
          
          <div className="stat-card approved">
            <div className="stat-value">{stats.approved_actions}</div>
            <div className="stat-label">Approved</div>
          </div>
          
          <div className="stat-card completed">
            <div className="stat-value">{stats.completed_actions}</div>
            <div className="stat-label">Completed</div>
          </div>
          
          <div className="stat-card confidence">
            <div className="stat-value">{Math.round(stats.average_confidence_score * 100)}%</div>
            <div className="stat-label">Avg Confidence</div>
          </div>
          
          <div className="stat-card recent">
            <div className="stat-value">{stats.recent_actions_7_days}</div>
            <div className="stat-label">Last 7 Days</div>
          </div>
        </div>
      )}
      
      <div className="juno-welcome">
        <p>Hi! I'm Juno, your AI assistant. I help process emails and extract actionable items for your CRM.</p>
        <p className="juno-instructions">
          Forward emails to <strong>thomsonblakecrm@gmail.com</strong> with instructions, and I'll prepare the actions for your review.
        </p>
      </div>
    </div>
  );
};

export default JunoHeader;