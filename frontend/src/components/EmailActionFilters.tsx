import React, { useState } from 'react';
import { EmailActionFilters as FiltersType } from '../types/emailActions';
import './EmailActionFilters.css';

interface EmailActionFiltersProps {
  filters: FiltersType;
  onFiltersChange: (filters: FiltersType) => void;
}

const EmailActionFilters: React.FC<EmailActionFiltersProps> = ({
  filters,
  onFiltersChange
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['actionType', 'dateRange'])
  );

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handleActionTypeChange = (actionType: string, checked: boolean) => {
    const currentTypes = filters.action_types || [];
    let newTypes: string[];
    
    if (checked) {
      newTypes = [...currentTypes, actionType];
    } else {
      newTypes = currentTypes.filter(t => t !== actionType);
    }
    
    onFiltersChange({
      ...filters,
      action_types: newTypes.length > 0 ? newTypes : undefined
    });
  };

  const handleDateChange = (field: 'start_date' | 'end_date', value: string) => {
    onFiltersChange({
      ...filters,
      [field]: value || undefined
    });
  };

  const handleSearchChange = (value: string) => {
    onFiltersChange({
      ...filters,
      search_text: value || undefined
    });
  };

  const handleClearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters = 
    filters.action_types?.length || 
    filters.start_date || 
    filters.end_date || 
    filters.search_text;

  return (
    <div className="email-action-filters">
      <div className="filters-header">
        <h3>Filters</h3>
        {hasActiveFilters && (
          <button className="clear-filters-btn" onClick={handleClearFilters}>
            Clear All
          </button>
        )}
      </div>

      {/* Search */}
      <div className="filter-section">
        <div className="filter-section-header">
          <h4>Search</h4>
        </div>
        <input
          type="text"
          className="search-input"
          placeholder="Search in emails..."
          value={filters.search_text || ''}
          onChange={(e) => handleSearchChange(e.target.value)}
        />
      </div>

      {/* Action Type Filter */}
      <div className="filter-section">
        <div 
          className="filter-section-header"
          onClick={() => toggleSection('actionType')}
        >
          <h4>Action Type</h4>
          <span className="toggle-icon">
            {expandedSections.has('actionType') ? '−' : '+'}
          </span>
        </div>
        {expandedSections.has('actionType') && (
          <div className="filter-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.action_types?.includes('add_note') || false}
                onChange={(e) => handleActionTypeChange('add_note', e.target.checked)}
              />
              <span className="checkbox-icon">📝</span>
              Add Note
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.action_types?.includes('log_call') || false}
                onChange={(e) => handleActionTypeChange('log_call', e.target.checked)}
              />
              <span className="checkbox-icon">📞</span>
              Log Call
            </label>
            
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.action_types?.includes('set_reminder') || false}
                onChange={(e) => handleActionTypeChange('set_reminder', e.target.checked)}
              />
              <span className="checkbox-icon">⏰</span>
              Set Reminder
            </label>
          </div>
        )}
      </div>

      {/* Date Range Filter */}
      <div className="filter-section">
        <div 
          className="filter-section-header"
          onClick={() => toggleSection('dateRange')}
        >
          <h4>Date Range</h4>
          <span className="toggle-icon">
            {expandedSections.has('dateRange') ? '−' : '+'}
          </span>
        </div>
        {expandedSections.has('dateRange') && (
          <div className="filter-options">
            <div className="date-input-group">
              <label>From</label>
              <input
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => handleDateChange('start_date', e.target.value)}
              />
            </div>
            
            <div className="date-input-group">
              <label>To</label>
              <input
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => handleDateChange('end_date', e.target.value)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Quick Filters */}
      <div className="filter-section">
        <h4>Quick Filters</h4>
        <div className="quick-filter-buttons">
          <button
            className="quick-filter-btn"
            onClick={() => {
              const today = new Date();
              onFiltersChange({
                ...filters,
                start_date: today.toISOString().split('T')[0],
                end_date: today.toISOString().split('T')[0]
              });
            }}
          >
            Today
          </button>
          
          <button
            className="quick-filter-btn"
            onClick={() => {
              const date = new Date();
              date.setDate(date.getDate() - 7);
              onFiltersChange({
                ...filters,
                start_date: date.toISOString().split('T')[0],
                end_date: new Date().toISOString().split('T')[0]
              });
            }}
          >
            Last 7 Days
          </button>
          
          <button
            className="quick-filter-btn"
            onClick={() => {
              const date = new Date();
              date.setDate(date.getDate() - 30);
              onFiltersChange({
                ...filters,
                start_date: date.toISOString().split('T')[0],
                end_date: new Date().toISOString().split('T')[0]
              });
            }}
          >
            Last 30 Days
          </button>
        </div>
      </div>

      {/* Filter Summary */}
      {hasActiveFilters && (
        <div className="filter-summary">
          <h4>Active Filters</h4>
          <div className="active-filter-tags">
            {filters.action_types?.map(type => (
              <span key={type} className="filter-tag">
                {type.replace('_', ' ')}
                <button
                  className="remove-tag"
                  onClick={() => handleActionTypeChange(type, false)}
                >
                  ×
                </button>
              </span>
            ))}
            
            {filters.start_date && (
              <span className="filter-tag">
                From: {filters.start_date}
                <button
                  className="remove-tag"
                  onClick={() => handleDateChange('start_date', '')}
                >
                  ×
                </button>
              </span>
            )}
            
            {filters.end_date && (
              <span className="filter-tag">
                To: {filters.end_date}
                <button
                  className="remove-tag"
                  onClick={() => handleDateChange('end_date', '')}
                >
                  ×
                </button>
              </span>
            )}
            
            {filters.search_text && (
              <span className="filter-tag">
                Search: "{filters.search_text}"
                <button
                  className="remove-tag"
                  onClick={() => handleSearchChange('')}
                >
                  ×
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EmailActionFilters;