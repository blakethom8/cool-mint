import React, { useState, useEffect } from 'react';
import {
  CreateRelationshipFromProvider,
  FilterOptionsResponse,
  LEAD_SCORE_LABELS,
  ENGAGEMENT_FREQUENCY_OPTIONS
} from '../types/relationship';
import { ClaimsProviderListItem } from '../types/claims';
import relationshipService from '../services/relationshipService';
import './AddToRelationshipModal.css';

interface AddToRelationshipModalProps {
  provider: ClaimsProviderListItem;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const AddToRelationshipModal: React.FC<AddToRelationshipModalProps> = ({
  provider,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState<CreateRelationshipFromProvider>({
    provider_id: provider.id,
    user_id: 0,
    relationship_status_id: 0,
    lead_score: 3,
    next_steps: '',
    note_content: ''
  });
  
  const [filterOptions, setFilterOptions] = useState<FilterOptionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load filter options when modal opens
  useEffect(() => {
    if (isOpen) {
      loadFilterOptions();
    }
  }, [isOpen]);

  const loadFilterOptions = async () => {
    try {
      const options = await relationshipService.getFilterOptions();
      setFilterOptions(options);
      
      // Set default values
      if (options.relationship_statuses.length > 0) {
        const prospectingStatus = options.relationship_statuses.find(s => s.code === 'PROSPECTING');
        setFormData(prev => ({
          ...prev,
          relationship_status_id: prospectingStatus?.id || options.relationship_statuses[0].id
        }));
      }
    } catch (err) {
      console.error('Failed to load filter options:', err);
      setError('Failed to load form options');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await relationshipService.createRelationshipFromProvider(formData);
      
      if (onSuccess) {
        onSuccess();
      }
      
      onClose();
    } catch (err: any) {
      console.error('Failed to create relationship:', err);
      setError(err.response?.data?.detail || 'Failed to create relationship');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'user_id' || name === 'relationship_status_id' || name === 'loyalty_status_id' || name === 'lead_score'
        ? Number(value)
        : value
    }));
  };

  const renderStarRating = () => {
    return (
      <div className="star-rating">
        {[1, 2, 3, 4, 5].map(score => (
          <button
            key={score}
            type="button"
            className={`star ${formData.lead_score && formData.lead_score >= score ? 'active' : ''}`}
            onClick={() => setFormData(prev => ({ ...prev, lead_score: score }))}
            title={LEAD_SCORE_LABELS[score]}
          >
            ★
          </button>
        ))}
        <span className="score-label">
          {formData.lead_score ? LEAD_SCORE_LABELS[formData.lead_score] : 'Select score'}
        </span>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add Provider to Relationships</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="modal-body">
            {/* Provider Information */}
            <div className="form-section">
              <h3>Provider Information</h3>
              <div className="provider-info-display">
                <div className="info-row">
                  <span className="info-label">Name:</span>
                  <span className="info-value">{provider.name}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Specialty:</span>
                  <span className="info-value">{provider.specialty}</span>
                </div>
                {provider.provider_group && (
                  <div className="info-row">
                    <span className="info-label">Group:</span>
                    <span className="info-value">{provider.provider_group}</span>
                  </div>
                )}
              </div>
            </div>

            {/* User Selection */}
            <div className="form-group">
              <label htmlFor="user_id">Assign To User *</label>
              <select
                id="user_id"
                name="user_id"
                value={formData.user_id}
                onChange={handleInputChange}
                required
              >
                <option value="">Select a user</option>
                {filterOptions?.users.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Relationship Configuration */}
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="relationship_status_id">Relationship Status *</label>
                <select
                  id="relationship_status_id"
                  name="relationship_status_id"
                  value={formData.relationship_status_id}
                  onChange={handleInputChange}
                  required
                >
                  {filterOptions?.relationship_statuses.map(status => (
                    <option key={status.id} value={status.id}>
                      {status.display_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="loyalty_status_id">Loyalty Status</label>
                <select
                  id="loyalty_status_id"
                  name="loyalty_status_id"
                  value={formData.loyalty_status_id || ''}
                  onChange={handleInputChange}
                >
                  <option value="">Not specified</option>
                  {filterOptions?.loyalty_statuses.map(status => (
                    <option key={status.id} value={status.id}>
                      {status.display_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Lead Score */}
            <div className="form-group">
              <label>Lead Score</label>
              {renderStarRating()}
            </div>

            {/* Next Steps */}
            <div className="form-group">
              <label htmlFor="next_steps">Next Steps</label>
              <input
                type="text"
                id="next_steps"
                name="next_steps"
                value={formData.next_steps || ''}
                onChange={handleInputChange}
                placeholder="e.g., Schedule introductory meeting"
              />
            </div>

            {/* Notes */}
            <div className="form-group">
              <label htmlFor="note_content">Notes</label>
              <textarea
                id="note_content"
                name="note_content"
                value={formData.note_content || ''}
                onChange={handleInputChange}
                rows={4}
                placeholder="Add any relevant notes about this relationship..."
              />
            </div>

            {error && (
              <div className="form-error">
                {error}
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Relationship'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddToRelationshipModal;