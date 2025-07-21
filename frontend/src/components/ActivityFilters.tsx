import React, { useState } from 'react';
import { ActivityFilters as IActivityFilters, FilterOptions } from '../types/activity';
import './ActivityFilters.css';

interface ActivityFiltersProps {
  filters: IActivityFilters;
  filterOptions: FilterOptions;
  onFilterChange: (filters: IActivityFilters) => void;
}

export const ActivityFilters: React.FC<ActivityFiltersProps> = ({
  filters,
  filterOptions,
  onFilterChange,
}) => {
  const [localFilters, setLocalFilters] = useState<IActivityFilters>(filters);

  const handleChange = (field: keyof IActivityFilters, value: any) => {
    const newFilters = { ...localFilters, [field]: value };
    setLocalFilters(newFilters);
  };

  const handleApplyFilters = () => {
    onFilterChange(localFilters);
  };

  const handleClearFilters = () => {
    const clearedFilters: IActivityFilters = {};
    setLocalFilters(clearedFilters);
    onFilterChange(clearedFilters);
  };

  const handleMultiSelect = (field: keyof IActivityFilters, value: string, checked: boolean) => {
    const currentValues = (localFilters[field] as string[]) || [];
    const newValues = checked 
      ? [...currentValues, value]
      : currentValues.filter(v => v !== value);
    handleChange(field, newValues.length > 0 ? newValues : undefined);
  };

  return (
    <div className="activity-filters">
      {/* Search Text */}
      <div className="filter-group">
        <label>Search</label>
        <input
          type="text"
          placeholder="Search in subject or description..."
          value={localFilters.search_text || ''}
          onChange={(e) => handleChange('search_text', e.target.value || undefined)}
        />
      </div>

      {/* Date Range */}
      <div className="filter-group">
        <label>Date Range</label>
        <input
          type="date"
          value={localFilters.start_date || ''}
          onChange={(e) => handleChange('start_date', e.target.value || undefined)}
        />
        <span className="date-separator">to</span>
        <input
          type="date"
          value={localFilters.end_date || ''}
          onChange={(e) => handleChange('end_date', e.target.value || undefined)}
        />
      </div>

      {/* Owner Selection */}
      <div className="filter-group">
        <label>Owners</label>
        <div className="checkbox-list">
          {filterOptions.owners.map(owner => (
            <label key={owner.id}>
              <input
                type="checkbox"
                checked={localFilters.owner_ids?.includes(owner.id) || false}
                onChange={(e) => handleMultiSelect('owner_ids', owner.id, e.target.checked)}
              />
              {owner.name}
            </label>
          ))}
        </div>
      </div>

      {/* Contact Type Filters */}
      <div className="filter-group">
        <label>Contact Types</label>
        <label>
          <input
            type="checkbox"
            checked={localFilters.has_contact === true}
            onChange={(e) => handleChange('has_contact', e.target.checked ? true : undefined)}
          />
          Has Any Contact
        </label>
        <label>
          <input
            type="checkbox"
            checked={localFilters.has_md_contact === true}
            onChange={(e) => handleChange('has_md_contact', e.target.checked ? true : undefined)}
          />
          Has MD Contact
        </label>
        <label>
          <input
            type="checkbox"
            checked={localFilters.has_pharma_contact === true}
            onChange={(e) => handleChange('has_pharma_contact', e.target.checked ? true : undefined)}
          />
          Has Pharma Contact
        </label>
      </div>

      {/* Contact Specialties */}
      {filterOptions.contact_specialties.length > 0 && (
        <div className="filter-group">
          <label>Contact Specialties</label>
          <div className="checkbox-list scrollable">
            {filterOptions.contact_specialties.map(specialty => (
              <label key={specialty}>
                <input
                  type="checkbox"
                  checked={localFilters.contact_specialties?.includes(specialty) || false}
                  onChange={(e) => handleMultiSelect('contact_specialties', specialty, e.target.checked)}
                />
                {specialty}
              </label>
            ))}
          </div>
        </div>
      )}

      {/* MNO Types */}
      {filterOptions.mno_types.length > 0 && (
        <div className="filter-group">
          <label>MNO Types</label>
          <div className="checkbox-list">
            {filterOptions.mno_types.map(type => (
              <label key={type}>
                <input
                  type="checkbox"
                  checked={localFilters.mno_types?.includes(type) || false}
                  onChange={(e) => handleMultiSelect('mno_types', type, e.target.checked)}
                />
                {type}
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Status */}
      {filterOptions.statuses.length > 0 && (
        <div className="filter-group">
          <label>Status</label>
          <div className="checkbox-list">
            {filterOptions.statuses.map(status => (
              <label key={status}>
                <input
                  type="checkbox"
                  checked={localFilters.statuses?.includes(status) || false}
                  onChange={(e) => handleMultiSelect('statuses', status, e.target.checked)}
                />
                {status}
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Filter Actions */}
      <div className="filter-actions">
        <button 
          className="apply-button"
          onClick={handleApplyFilters}
        >
          Apply Filters
        </button>
        <button 
          className="clear-button"
          onClick={handleClearFilters}
        >
          Clear All
        </button>
      </div>
    </div>
  );
};