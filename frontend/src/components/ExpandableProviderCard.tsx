import React, { useState } from 'react';
import { ClaimsProviderListItem } from '../types/claims';
import './ExpandableProviderCard.css';

interface ExpandableProviderCardProps {
  provider: ClaimsProviderListItem;
  isSelected: boolean;
  isExpanded: boolean;
  onSelect: (id: string) => void;
  onExpand: (id: string) => void;
  onLeadClassification?: (id: string, classification: string) => void;
  onAddToLeads?: (id: string) => void;
  onViewDetails?: (id: string) => void;
}

const ExpandableProviderCard: React.FC<ExpandableProviderCardProps> = ({
  provider,
  isSelected,
  isExpanded,
  onSelect,
  onExpand,
  onLeadClassification,
  onAddToLeads,
  onViewDetails,
}) => {
  const [selectedClassification, setSelectedClassification] = useState<string>('');

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onSelect(provider.id);
  };

  const handleExpandClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onExpand(provider.id);
  };

  const handleClassificationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const classification = e.target.value;
    setSelectedClassification(classification);
    if (classification && onLeadClassification) {
      onLeadClassification(provider.id, classification);
    }
  };

  const handleAddToLeads = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onAddToLeads) {
      onAddToLeads(provider.id);
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
            <div className="action-row">
              <select
                className="lead-classification-select"
                value={selectedClassification}
                onChange={handleClassificationChange}
                onClick={(e) => e.stopPropagation()}
              >
                <option value="">Lead Classification</option>
                <option value="hot">Hot Lead</option>
                <option value="warm">Warm Lead</option>
                <option value="cold">Cold Lead</option>
                <option value="not-qualified">Not Qualified</option>
              </select>

              <button
                className="action-button add-to-leads"
                onClick={handleAddToLeads}
              >
                Add to Leads
              </button>
            </div>

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