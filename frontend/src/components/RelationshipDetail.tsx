import React, { useState, useCallback } from 'react';
import {
  RelationshipDetail as RelationshipDetailType,
  RelationshipUpdate,
  LEAD_SCORE_LABELS,
  ENGAGEMENT_FREQUENCY_OPTIONS,
  RELATIONSHIP_STATUS_COLORS
} from '../types/relationship';
import relationshipService from '../services/relationshipService';
import ActivityTimeline from './ActivityTimeline';
import './RelationshipDetail.css';

interface RelationshipDetailProps {
  relationship: RelationshipDetailType;
  onUpdate: (updatedRelationship: RelationshipDetailType) => void;
  onClose: () => void;
}

const RelationshipDetail: React.FC<RelationshipDetailProps> = ({
  relationship,
  onUpdate,
  onClose
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<RelationshipUpdate>({
    relationship_status_id: relationship.relationship_status.id,
    loyalty_status_id: relationship.loyalty_status?.id,
    lead_score: relationship.lead_score,
    next_steps: relationship.next_steps,
    engagement_frequency: relationship.engagement_frequency
  });
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'activities' | 'campaigns'>('overview');

  // Handle form changes
  const handleFormChange = useCallback((field: keyof RelationshipUpdate, value: any) => {
    setEditForm(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Save changes
  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const updated = await relationshipService.updateRelationship(
        relationship.relationship_id,
        editForm
      );
      onUpdate(updated);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update relationship:', error);
      alert('Failed to update relationship. Please try again.');
    } finally {
      setSaving(false);
    }
  }, [relationship.relationship_id, editForm, onUpdate]);

  // Cancel editing
  const handleCancel = useCallback(() => {
    setEditForm({
      relationship_status_id: relationship.relationship_status.id,
      loyalty_status_id: relationship.loyalty_status?.id,
      lead_score: relationship.lead_score,
      next_steps: relationship.next_steps,
      engagement_frequency: relationship.engagement_frequency
    });
    setIsEditing(false);
  }, [relationship]);

  // Format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'long', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  // Render entity details based on type
  const renderEntityDetails = () => {
    const details = relationship.entity_details;
    
    switch (relationship.entity_type.code) {
      case 'SfContact':
        return (
          <>
            {details.email && (
              <div className="relationship-detail__info-item">
                <span className="label">Email:</span>
                <a href={`mailto:${details.email}`}>{details.email}</a>
              </div>
            )}
            {details.phone && (
              <div className="relationship-detail__info-item">
                <span className="label">Phone:</span>
                <a href={`tel:${details.phone}`}>{details.phone}</a>
              </div>
            )}
            {details.specialty && (
              <div className="relationship-detail__info-item">
                <span className="label">Specialty:</span>
                <span>{details.specialty}</span>
              </div>
            )}
            {details.account && (
              <div className="relationship-detail__info-item">
                <span className="label">Account:</span>
                <span>{details.account}</span>
              </div>
            )}
            {details.geography && (
              <div className="relationship-detail__info-item">
                <span className="label">Geography:</span>
                <span>{details.geography}</span>
              </div>
            )}
          </>
        );
      
      case 'ClaimsProvider':
        return (
          <>
            {details.npi && (
              <div className="relationship-detail__info-item">
                <span className="label">NPI:</span>
                <span>{details.npi}</span>
              </div>
            )}
            {details.specialty && (
              <div className="relationship-detail__info-item">
                <span className="label">Specialty:</span>
                <span>{details.specialty}</span>
              </div>
            )}
            {details.city && details.state && (
              <div className="relationship-detail__info-item">
                <span className="label">Location:</span>
                <span>{details.city}, {details.state}</span>
              </div>
            )}
          </>
        );
      
      case 'SiteOfService':
        return (
          <>
            {details.site_type && (
              <div className="relationship-detail__info-item">
                <span className="label">Site Type:</span>
                <span>{details.site_type}</span>
              </div>
            )}
            {details.city && details.state && (
              <div className="relationship-detail__info-item">
                <span className="label">Location:</span>
                <span>{details.city}, {details.state}</span>
              </div>
            )}
          </>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="relationship-detail">
      {/* Header */}
      <div className="relationship-detail__header">
        <div className="relationship-detail__header-info">
          <h2>{relationship.entity_name}</h2>
          <span className="relationship-detail__entity-type">
            {relationship.entity_type.common_name}
          </span>
        </div>
        <div className="relationship-detail__header-actions">
          {!isEditing ? (
            <button className="btn btn-primary" onClick={() => setIsEditing(true)}>
              Edit
            </button>
          ) : (
            <>
              <button 
                className="btn btn-primary" 
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={handleCancel}
                disabled={saving}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="relationship-detail__tabs">
        <button
          className={`relationship-detail__tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`relationship-detail__tab ${activeTab === 'activities' ? 'active' : ''}`}
          onClick={() => setActiveTab('activities')}
        >
          Activities ({relationship.recent_activities.length})
        </button>
        <button
          className={`relationship-detail__tab ${activeTab === 'campaigns' ? 'active' : ''}`}
          onClick={() => setActiveTab('campaigns')}
        >
          Campaigns ({relationship.campaigns.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="relationship-detail__content">
        {activeTab === 'overview' && (
          <div className="relationship-detail__overview">
            {/* Status Section */}
            <div className="relationship-detail__section">
              <h3>Status</h3>
              <div className="relationship-detail__status-grid">
                <div className="relationship-detail__status-item">
                  <label>Relationship Status</label>
                  {!isEditing ? (
                    <span 
                      className="relationship-detail__status-badge"
                      style={{ 
                        backgroundColor: RELATIONSHIP_STATUS_COLORS[relationship.relationship_status.code] || '#6c757d' 
                      }}
                    >
                      {relationship.relationship_status.display_name}
                    </span>
                  ) : (
                    <select
                      value={editForm.relationship_status_id}
                      onChange={(e) => handleFormChange('relationship_status_id', Number(e.target.value))}
                    >
                      <option value={1}>Established</option>
                      <option value={2}>Building</option>
                      <option value={3}>Prospecting</option>
                      <option value={4}>Deprioritized</option>
                    </select>
                  )}
                </div>
                
                <div className="relationship-detail__status-item">
                  <label>Loyalty Status</label>
                  {!isEditing ? (
                    relationship.loyalty_status ? (
                      <span 
                        className="relationship-detail__loyalty-badge"
                        style={{
                          borderLeft: `4px solid ${relationship.loyalty_status.color_hex || '#ccc'}`
                        }}
                      >
                        {relationship.loyalty_status.display_name}
                      </span>
                    ) : (
                      <span className="relationship-detail__no-value">Not set</span>
                    )
                  ) : (
                    <select
                      value={editForm.loyalty_status_id || ''}
                      onChange={(e) => handleFormChange('loyalty_status_id', 
                        e.target.value ? Number(e.target.value) : undefined)}
                    >
                      <option value="">None</option>
                      <option value={1}>Loyal</option>
                      <option value={2}>At Risk</option>
                      <option value={3}>Neutral</option>
                    </select>
                  )}
                </div>
                
                <div className="relationship-detail__status-item">
                  <label>Lead Score</label>
                  {!isEditing ? (
                    relationship.lead_score ? (
                      <div className="relationship-detail__lead-score">
                        <span className="stars">{'★'.repeat(relationship.lead_score)}</span>
                        <span className="label">{LEAD_SCORE_LABELS[relationship.lead_score]}</span>
                      </div>
                    ) : (
                      <span className="relationship-detail__no-value">Not scored</span>
                    )
                  ) : (
                    <select
                      value={editForm.lead_score || ''}
                      onChange={(e) => handleFormChange('lead_score', 
                        e.target.value ? Number(e.target.value) : undefined)}
                    >
                      <option value="">None</option>
                      <option value={5}>★★★★★ Very High</option>
                      <option value={4}>★★★★☆ High</option>
                      <option value={3}>★★★☆☆ Medium</option>
                      <option value={2}>★★☆☆☆ Low</option>
                      <option value={1}>★☆☆☆☆ Very Low</option>
                    </select>
                  )}
                </div>
                
                <div className="relationship-detail__status-item">
                  <label>Engagement Frequency</label>
                  {!isEditing ? (
                    <span>{relationship.engagement_frequency || 'Not set'}</span>
                  ) : (
                    <select
                      value={editForm.engagement_frequency || ''}
                      onChange={(e) => handleFormChange('engagement_frequency', e.target.value || undefined)}
                    >
                      <option value="">None</option>
                      {ENGAGEMENT_FREQUENCY_OPTIONS.map(freq => (
                        <option key={freq} value={freq}>{freq}</option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="relationship-detail__section">
              <h3>Contact Information</h3>
              <div className="relationship-detail__info-grid">
                {renderEntityDetails()}
              </div>
            </div>

            {/* Activity Metrics */}
            {relationship.metrics && (
              <div className="relationship-detail__section">
                <h3>Activity Metrics</h3>
                <div className="relationship-detail__metrics-grid">
                  <div className="relationship-detail__metric">
                    <span className="value">{relationship.metrics.total_activities}</span>
                    <span className="label">Total Activities</span>
                  </div>
                  <div className="relationship-detail__metric">
                    <span className="value">{relationship.metrics.activities_last_30_days}</span>
                    <span className="label">Last 30 Days</span>
                  </div>
                  <div className="relationship-detail__metric">
                    <span className="value">{relationship.metrics.meeting_count}</span>
                    <span className="label">Meetings</span>
                  </div>
                  <div className="relationship-detail__metric">
                    <span className="value">{relationship.metrics.referral_count}</span>
                    <span className="label">Referrals</span>
                  </div>
                </div>
              </div>
            )}

            {/* Next Steps */}
            <div className="relationship-detail__section">
              <h3>Next Steps</h3>
              {!isEditing ? (
                <p className="relationship-detail__next-steps">
                  {relationship.next_steps || 'No next steps defined'}
                </p>
              ) : (
                <textarea
                  value={editForm.next_steps || ''}
                  onChange={(e) => handleFormChange('next_steps', e.target.value || undefined)}
                  placeholder="Enter next steps..."
                  rows={4}
                />
              )}
            </div>

            {/* Relationship Info */}
            <div className="relationship-detail__section">
              <h3>Relationship Information</h3>
              <div className="relationship-detail__info-grid">
                <div className="relationship-detail__info-item">
                  <span className="label">Owner:</span>
                  <span>{relationship.user_name}</span>
                </div>
                <div className="relationship-detail__info-item">
                  <span className="label">Last Activity:</span>
                  <span>{formatDate(relationship.last_activity_date)}</span>
                </div>
                <div className="relationship-detail__info-item">
                  <span className="label">Created:</span>
                  <span>{formatDate(relationship.created_at)}</span>
                </div>
                <div className="relationship-detail__info-item">
                  <span className="label">Updated:</span>
                  <span>{formatDate(relationship.updated_at)}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'activities' && (
          <div className="relationship-detail__activities">
            <ActivityTimeline 
              activities={relationship.recent_activities}
              relationshipId={relationship.relationship_id}
            />
          </div>
        )}

        {activeTab === 'campaigns' && (
          <div className="relationship-detail__campaigns">
            {relationship.campaigns.length > 0 ? (
              <div className="relationship-detail__campaign-list">
                {relationship.campaigns.map(campaign => (
                  <div key={campaign.campaign_id} className="relationship-detail__campaign-item">
                    <h4>{campaign.campaign_name}</h4>
                    <div className="relationship-detail__campaign-details">
                      <span className={`status ${campaign.status.toLowerCase()}`}>
                        {campaign.status}
                      </span>
                      <span className="dates">
                        {formatDate(campaign.start_date)}
                        {campaign.end_date && ` - ${formatDate(campaign.end_date)}`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="relationship-detail__empty">
                Not associated with any campaigns
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default RelationshipDetail;