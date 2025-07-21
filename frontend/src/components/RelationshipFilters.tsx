import React, { useState, useCallback } from 'react';
import {
  RelationshipFilters as RelationshipFiltersType,
  FilterOptionsResponse,
  ENGAGEMENT_FREQUENCY_OPTIONS
} from '../types/relationship';
import './RelationshipFilters.css';

interface RelationshipFiltersProps {
  filters: RelationshipFiltersType;
  filterOptions?: FilterOptionsResponse;
  onChange: (filters: RelationshipFiltersType) => void;
}

const RelationshipFilters: React.FC<RelationshipFiltersProps> = ({
  filters,
  filterOptions,
  onChange
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['users', 'status', 'activity'])
  );

  // Toggle section expansion
  const toggleSection = useCallback((section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  }, []);

  // Handle filter changes
  const handleMultiSelectChange = useCallback((
    field: keyof RelationshipFiltersType,
    value: string | number,
    checked: boolean
  ) => {
    const currentValues = (filters[field] as any[]) || [];
    let newValues: any[];
    
    if (checked) {
      newValues = [...currentValues, value];
    } else {
      newValues = currentValues.filter(v => v !== value);
    }
    
    onChange({
      ...filters,
      [field]: newValues.length > 0 ? newValues : undefined
    });
  }, [filters, onChange]);

  const handleSingleValueChange = useCallback((
    field: keyof RelationshipFiltersType,
    value: any
  ) => {
    onChange({
      ...filters,
      [field]: value || undefined
    });
  }, [filters, onChange]);

  const clearAllFilters = useCallback(() => {
    onChange({});
  }, [onChange]);

  // Count active filters
  const activeFilterCount = Object.keys(filters).reduce((count, key) => {
    const value = filters[key as keyof RelationshipFiltersType];
    if (Array.isArray(value)) return count + (value.length > 0 ? 1 : 0);
    return count + (value !== undefined ? 1 : 0);
  }, 0);

  if (!filterOptions) {
    return <div className="relationship-filters__loading">Loading filters...</div>;
  }

  return (
    <div className="relationship-filters">
      <div className="relationship-filters__header">
        <span className="relationship-filters__count">
          {activeFilterCount > 0 && `(${activeFilterCount} active)`}
        </span>
        {activeFilterCount > 0 && (
          <button 
            className="relationship-filters__clear"
            onClick={clearAllFilters}
          >
            Clear all
          </button>
        )}
      </div>

      {/* Users Section */}
      <div className="relationship-filters__section">
        <button
          className="relationship-filters__section-header"
          onClick={() => toggleSection('users')}
        >
          <span>Users</span>
          <span className="chevron">{expandedSections.has('users') ? '▼' : '▶'}</span>
        </button>
        
        {expandedSections.has('users') && (
          <div className="relationship-filters__section-content">
            <label className="relationship-filters__checkbox">
              <input
                type="checkbox"
                checked={filters.my_relationships_only || false}
                onChange={(e) => handleSingleValueChange('my_relationships_only', e.target.checked)}
              />
              <span>My Relationships Only</span>
            </label>
            
            <div className="relationship-filters__divider" />
            
            <div className="relationship-filters__scroll-list">
              {filterOptions.users?.map(user => (
                <label key={user.id} className="relationship-filters__checkbox">
                  <input
                    type="checkbox"
                    checked={filters.user_ids?.includes(user.id) || false}
                    onChange={(e) => handleMultiSelectChange('user_ids', user.id, e.target.checked)}
                  />
                  <span>{user.name}</span>
                  <span className="relationship-filters__count">({user.relationship_count})</span>
                </label>
              )) || <div className="relationship-filters__empty">No users available</div>}
            </div>
          </div>
        )}
      </div>

      {/* Status Section */}
      <div className="relationship-filters__section">
        <button
          className="relationship-filters__section-header"
          onClick={() => toggleSection('status')}
        >
          <span>Status</span>
          <span className="chevron">{expandedSections.has('status') ? '▼' : '▶'}</span>
        </button>
        
        {expandedSections.has('status') && (
          <div className="relationship-filters__section-content">
            <div className="relationship-filters__subsection">
              <h4>Relationship Status</h4>
              {filterOptions.relationship_statuses?.map(status => (
                <label key={status.id} className="relationship-filters__checkbox">
                  <input
                    type="checkbox"
                    checked={filters.relationship_status_ids?.includes(status.id) || false}
                    onChange={(e) => handleMultiSelectChange('relationship_status_ids', status.id, e.target.checked)}
                  />
                  <span>{status.display_name}</span>
                </label>
              ))}
            </div>
            
            <div className="relationship-filters__subsection">
              <h4>Loyalty Status</h4>
              {filterOptions.loyalty_statuses?.map(status => (
                <label key={status.id} className="relationship-filters__checkbox">
                  <input
                    type="checkbox"
                    checked={filters.loyalty_status_ids?.includes(status.id) || false}
                    onChange={(e) => handleMultiSelectChange('loyalty_status_ids', status.id, e.target.checked)}
                  />
                  <span 
                    className="relationship-filters__loyalty-label"
                    style={{ 
                      borderLeft: `4px solid ${status.color_hex || '#ccc'}`,
                      paddingLeft: '8px'
                    }}
                  >
                    {status.display_name}
                  </span>
                </label>
              ))}
            </div>
            
            <div className="relationship-filters__subsection">
              <h4>Lead Score</h4>
              {[5, 4, 3, 2, 1].map(score => (
                <label key={score} className="relationship-filters__checkbox">
                  <input
                    type="checkbox"
                    checked={filters.lead_scores?.includes(score) || false}
                    onChange={(e) => handleMultiSelectChange('lead_scores', score, e.target.checked)}
                  />
                  <span>{'★'.repeat(score)}{'☆'.repeat(5 - score)}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Activity Section */}
      <div className="relationship-filters__section">
        <button
          className="relationship-filters__section-header"
          onClick={() => toggleSection('activity')}
        >
          <span>Activity</span>
          <span className="chevron">{expandedSections.has('activity') ? '▼' : '▶'}</span>
        </button>
        
        {expandedSections.has('activity') && (
          <div className="relationship-filters__section-content">
            <div className="relationship-filters__date-range">
              <label>
                <span>After</span>
                <input
                  type="date"
                  value={filters.last_activity_after || ''}
                  onChange={(e) => handleSingleValueChange('last_activity_after', e.target.value)}
                />
              </label>
              <label>
                <span>Before</span>
                <input
                  type="date"
                  value={filters.last_activity_before || ''}
                  onChange={(e) => handleSingleValueChange('last_activity_before', e.target.value)}
                />
              </label>
            </div>
            
            <div className="relationship-filters__number-range">
              <h4>Days Since Last Activity</h4>
              <div className="relationship-filters__range-inputs">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.days_since_activity_min || ''}
                  onChange={(e) => handleSingleValueChange('days_since_activity_min', 
                    e.target.value ? parseInt(e.target.value) : undefined)}
                />
                <span>to</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.days_since_activity_max || ''}
                  onChange={(e) => handleSingleValueChange('days_since_activity_max', 
                    e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Entity Type Section */}
      <div className="relationship-filters__section">
        <button
          className="relationship-filters__section-header"
          onClick={() => toggleSection('entity')}
        >
          <span>Entity Type</span>
          <span className="chevron">{expandedSections.has('entity') ? '▼' : '▶'}</span>
        </button>
        
        {expandedSections.has('entity') && (
          <div className="relationship-filters__section-content">
            {filterOptions.entity_types?.map(type => (
              <label key={type.id} className="relationship-filters__checkbox">
                <input
                  type="checkbox"
                  checked={filters.entity_type_ids?.includes(type.id) || false}
                  onChange={(e) => handleMultiSelectChange('entity_type_ids', type.id, e.target.checked)}
                />
                <span>{type.common_name}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Location Section */}
      <div className="relationship-filters__section">
        <button
          className="relationship-filters__section-header"
          onClick={() => toggleSection('location')}
        >
          <span>Location</span>
          <span className="chevron">{expandedSections.has('location') ? '▼' : '▶'}</span>
        </button>
        
        {expandedSections.has('location') && (
          <div className="relationship-filters__section-content">
            {filterOptions.geographies && filterOptions.geographies.length > 0 && (
              <div className="relationship-filters__subsection">
                <h4>Geography</h4>
                <div className="relationship-filters__scroll-list">
                  {filterOptions.geographies?.map(geo => (
                    <label key={geo} className="relationship-filters__checkbox">
                      <input
                        type="checkbox"
                        checked={filters.geographies?.includes(geo) || false}
                        onChange={(e) => handleMultiSelectChange('geographies', geo, e.target.checked)}
                      />
                      <span>{geo}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Specialty Section */}
      <div className="relationship-filters__section">
        <button
          className="relationship-filters__section-header"
          onClick={() => toggleSection('specialty')}
        >
          <span>Specialty</span>
          <span className="chevron">{expandedSections.has('specialty') ? '▼' : '▶'}</span>
        </button>
        
        {expandedSections.has('specialty') && (
          <div className="relationship-filters__section-content">
            <div className="relationship-filters__scroll-list">
              {filterOptions.specialties?.map(specialty => (
                <label key={specialty} className="relationship-filters__checkbox">
                  <input
                    type="checkbox"
                    checked={filters.specialties?.includes(specialty) || false}
                    onChange={(e) => handleMultiSelectChange('specialties', specialty, e.target.checked)}
                  />
                  <span>{specialty}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Campaigns Section */}
      {filterOptions.campaigns && filterOptions.campaigns.length > 0 && (
        <div className="relationship-filters__section">
          <button
            className="relationship-filters__section-header"
            onClick={() => toggleSection('campaigns')}
          >
            <span>Campaigns</span>
            <span className="chevron">{expandedSections.has('campaigns') ? '▼' : '▶'}</span>
          </button>
          
          {expandedSections.has('campaigns') && (
            <div className="relationship-filters__section-content">
              <div className="relationship-filters__scroll-list">
                {filterOptions.campaigns?.map(campaign => (
                  <label key={campaign.id} className="relationship-filters__checkbox">
                    <input
                      type="checkbox"
                      checked={filters.campaign_ids?.includes(campaign.id) || false}
                      onChange={(e) => handleMultiSelectChange('campaign_ids', campaign.id, e.target.checked)}
                    />
                    <span>{campaign.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search Section */}
      <div className="relationship-filters__section">
        <div className="relationship-filters__search">
          <input
            type="text"
            placeholder="Search names, notes..."
            value={filters.search_text || ''}
            onChange={(e) => handleSingleValueChange('search_text', e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};

export default RelationshipFilters;