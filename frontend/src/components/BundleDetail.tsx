import React, { useState, useEffect } from 'react';
import { Bundle, BundleDetailResponse, ActivityDetail } from '../types/bundle';
import { bundleService } from '../services/bundleService';
import './BundleDetail.css';

interface BundleDetailProps {
  bundle: Bundle;
  onStartConversation: () => void;
}

export const BundleDetail: React.FC<BundleDetailProps> = ({
  bundle,
  onStartConversation,
}) => {
  const [bundleDetail, setBundleDetail] = useState<BundleDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadBundleDetail();
  }, [bundle.id]);

  const loadBundleDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await bundleService.getBundleDetail(bundle.id);
      setBundleDetail(response);
    } catch (err) {
      setError('Failed to load bundle details');
      console.error('Error loading bundle detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleActivityExpansion = (activityId: string) => {
    setExpandedActivities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(activityId)) {
        newSet.delete(activityId);
      } else {
        newSet.add(activityId);
      }
      return newSet;
    });
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const renderActivityContext = (activity: ActivityDetail) => {
    if (!activity.llm_context) return null;
    
    return (
      <div className="activity-context">
        <h5>Context Data:</h5>
        <pre className="context-json">
          {JSON.stringify(activity.llm_context, null, 2)}
        </pre>
      </div>
    );
  };

  if (loading) {
    return <div className="bundle-detail-loading">Loading bundle details...</div>;
  }

  if (error) {
    return <div className="bundle-detail-error">{error}</div>;
  }

  if (!bundleDetail) {
    return <div className="bundle-detail-empty">Select a bundle to view details</div>;
  }

  return (
    <div className="bundle-detail">
      <div className="bundle-detail-header">
        <h2>{bundle.name}</h2>
        {bundle.description && (
          <p className="bundle-detail-description">{bundle.description}</p>
        )}
      </div>

      <div className="bundle-detail-stats">
        <div className="stat-item">
          <span className="stat-label">Activities:</span>
          <span className="stat-value">{bundle.activity_count}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Total Tokens:</span>
          <span className="stat-value">~{bundleDetail.total_tokens.toLocaleString()}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Conversations:</span>
          <span className="stat-value">{bundle.conversation_count}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Created:</span>
          <span className="stat-value">{formatDate(bundle.created_at)}</span>
        </div>
      </div>

      <div className="bundle-detail-actions">
        <button
          className="start-conversation-btn"
          onClick={onStartConversation}
        >
          Start New Conversation
        </button>
      </div>

      <div className="bundle-detail-activities">
        <h3>Activities ({bundleDetail.activities.length})</h3>
        <div className="activities-list">
          {bundleDetail.activities.map((activity) => (
            <div key={activity.activity_id} className="activity-item">
              <div
                className="activity-header"
                onClick={() => toggleActivityExpansion(activity.activity_id)}
              >
                <span className="activity-expand-icon">
                  {expandedActivities.has(activity.activity_id) ? '▼' : '▶'}
                </span>
                <div className="activity-summary">
                  <h4 className="activity-subject">{activity.subject}</h4>
                  <div className="activity-meta">
                    <span className="activity-date">{formatDate(activity.activity_date)}</span>
                    <span className="activity-type">{activity.mno_type}</span>
                    {activity.mno_subtype && (
                      <span className="activity-subtype">{activity.mno_subtype}</span>
                    )}
                    <span className="activity-owner">{activity.owner_name}</span>
                  </div>
                </div>
              </div>

              {expandedActivities.has(activity.activity_id) && (
                <div className="activity-details">
                  {activity.description && (
                    <div className="activity-description">
                      <h5>Description:</h5>
                      <p>{activity.description}</p>
                    </div>
                  )}

                  {activity.contact_names.length > 0 && (
                    <div className="activity-contacts">
                      <h5>Contacts ({activity.contact_count}):</h5>
                      <ul>
                        {activity.contact_names.map((name, index) => (
                          <li key={index}>{name}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {activity.llm_context && (
                    <details className="activity-context-details">
                      <summary>View Full Context Data</summary>
                      {renderActivityContext(activity)}
                    </details>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};