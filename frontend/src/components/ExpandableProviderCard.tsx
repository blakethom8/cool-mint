import React from 'react';
import { ClaimsProviderListItem } from '../types/claims';
import './ExpandableProviderCard.css';

interface ExpandableProviderCardProps {
  provider: ClaimsProviderListItem;
  isSelected: boolean;
  isExpanded: boolean;
  onSelect: (id: string) => void;
  onExpand: (id: string) => void;
  onAddToRelationships?: (id: string) => void;
  onViewDetails?: (id: string) => void;
}

const ExpandableProviderCard: React.FC<ExpandableProviderCardProps> = ({
  provider,
  isSelected,
  isExpanded,
  onSelect,
  onExpand,
  onAddToRelationships,
  onViewDetails,
}) => {

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onSelect(provider.id);
  };

  const handleExpandClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onExpand(provider.id);
  };

  const handleAddToRelationships = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onAddToRelationships) {
      onAddToRelationships(provider.id);
    }
  };

  const handleViewDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onViewDetails) {
      onViewDetails(provider.id);
    }
  };

  return (
    <div 
      className={`expandable-provider-card ${isSelected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}`}
      onClick={handleClick}
    >
      {/* Compact View - Always Visible */}
      <div className="provider-card-header">
        <div className="provider-info">
          <h4 className="provider-name">{provider.name}</h4>
          <div className="provider-meta">
            <span className="provider-specialty">{provider.specialty}</span>
            {provider.provider_group && (
              <span className="provider-group">• {provider.provider_group}</span>
            )}
          </div>
        </div>
        
        <div className="provider-stats">
          <div className="visit-count">
            <span className="visit-number">{provider.total_visits.toLocaleString()}</span>
            <span className="visit-label">visits</span>
          </div>
          <button 
            className="expand-button"
            onClick={handleExpandClick}
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            <svg width="12" height="12" viewBox="0 0 12 12">
              <path
                d={isExpanded ? 'M10 8L6 4L2 8' : 'M2 4L6 8L10 4'}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Expanded View - Details & Actions */}
      {isExpanded && (
        <div className="provider-card-details">
          <div className="detail-section">
            {provider.top_site_name && (
              <div className="detail-item">
                <span className="detail-label">Top Site:</span>
                <span className="detail-value">{provider.top_site_name}</span>
              </div>
            )}
            
            {provider.top_payer && (
              <div className="detail-item">
                <span className="detail-label">Top Payer:</span>
                <span className="detail-value">
                  {provider.top_payer}
                  {provider.top_payer_percent && (
                    <span className="detail-percent"> ({Math.round(provider.top_payer_percent * 100)}%)</span>
                  )}
                </span>
              </div>
            )}
            
            {provider.top_referring_org && (
              <div className="detail-item">
                <span className="detail-label">Top Referrer:</span>
                <span className="detail-value">{provider.top_referring_org}</span>
              </div>
            )}
          </div>

          <div className="action-section">
            <button
              className="action-button add-to-relationships"
              onClick={handleAddToRelationships}
            >
              Add to Relationships
            </button>

            <button
              className="action-button view-details"
              onClick={handleViewDetails}
            >
              View Full Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpandableProviderCard;