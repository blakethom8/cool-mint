import React, { useState, useEffect, useCallback } from 'react';
import { ClaimsFilters, FilterOptions, ViewMode } from '../types/claims';
import claimsService from '../services/claimsService';
import DropdownMultiSelect from './DropdownMultiSelect';
import './ClaimsFilters.css';

interface ClaimsFiltersProps {
  filters: ClaimsFilters;
  onFiltersChange: (filters: ClaimsFilters) => void;
  viewMode?: ViewMode;
}

const ClaimsFiltersComponent: React.FC<ClaimsFiltersProps> = ({
  filters,
  onFiltersChange,
}) => {
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [localFilters, setLocalFilters] = useState<ClaimsFilters>(filters);
  const [isExpanded, setIsExpanded] = useState(true);

  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const loadFilterOptions = async () => {
    try {
      const options = await claimsService.getFilterOptions();
      setFilterOptions(options);
    } catch (error) {
      console.error('Error loading filter options:', error);
    }
  };

  const handleFilterChange = useCallback((key: keyof ClaimsFilters, value: any) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
    onFiltersChange(newFilters);
  }, [localFilters, onFiltersChange]);

  const handleMultiSelectChange = useCallback((key: keyof ClaimsFilters, values: string[]) => {
    handleFilterChange(key, values.length > 0 ? values : undefined);
  }, [handleFilterChange]);

  const clearFilters = useCallback(() => {
    const clearedFilters: ClaimsFilters = {};
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  }, [onFiltersChange]);

  const getActiveFilterCount = () => {
    return Object.values(localFilters).filter(value => {
      if (Array.isArray(value)) return value.length > 0;
      return value !== undefined && value !== null && value !== '';
    }).length;
  };

  if (!filterOptions) {
    return (
      <div className="claims-filters loading">
        <div className="loading-text">Loading filters...</div>
      </div>
    );
  }

  return (
    <div className="claims-filters">
      <div className="filters-header">
        <h3>
          Filters 
          {getActiveFilterCount() > 0 && (
            <span className="filter-count">({getActiveFilterCount()})</span>
          )}
        </h3>
        <div className="header-actions">
          <button
            className="clear-filters-btn"
            onClick={clearFilters}
            disabled={getActiveFilterCount() === 0}
          >
            Clear All
          </button>
          <button
            className="expand-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '−' : '+'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="filters-content">
          {/* Search Filter */}
          <div className="filter-group">
            <label className="filter-label">Search</label>
            <input
              type="text"
              className="filter-input"
              placeholder="Search..."
              value={localFilters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value || undefined)}
            />
          </div>

          {/* Geographic Filters */}
          <div className="filter-section">
            <h4 className="section-title">Geographic</h4>
            
            <DropdownMultiSelect
              label="Geomarket"
              options={filterOptions.geomarkets}
              selectedValues={localFilters.geomarket || []}
              onChange={(values) => handleMultiSelectChange('geomarket', values)}
              placeholder="Select geomarkets..."
            />

            <DropdownMultiSelect
              label="City"
              options={filterOptions.cities}
              selectedValues={localFilters.city || []}
              onChange={(values) => handleMultiSelectChange('city', values)}
              placeholder="Select cities..."
            />
          </div>

          {/* Site Filters - First */}
          <div className="filter-section">
            <h4 className="section-title">Sites</h4>
              
              <DropdownMultiSelect
                label="Site Type"
                options={filterOptions.site_types}
                selectedValues={localFilters.site_type || []}
                onChange={(values) => handleMultiSelectChange('site_type', values)}
                placeholder="Select site types..."
              />

              <div className="filter-group">
                <label className="filter-label">Minimum Site Visits</label>
                <input
                  type="number"
                  className="filter-input"
                  placeholder="0"
                  min="0"
                  value={localFilters.min_site_visits || ''}
                  onChange={(e) => handleFilterChange('min_site_visits', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>

              <div className="filter-group">
                <label className="filter-label">Minimum Providers</label>
                <input
                  type="number"
                  className="filter-input"
                  placeholder="0"
                  min="0"
                  value={localFilters.min_providers || ''}
                  onChange={(e) => handleFilterChange('min_providers', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
            </div>

          {/* Provider Filters - Second */}
          <div className="filter-section">
            <h4 className="section-title">Providers</h4>
              
              <DropdownMultiSelect
                label="Specialty"
                options={filterOptions.specialties}
                selectedValues={localFilters.specialty || []}
                onChange={(values) => handleMultiSelectChange('specialty', values)}
                placeholder="Select specialties..."
              />

              <DropdownMultiSelect
                label="Service Line"
                options={filterOptions.service_lines}
                selectedValues={localFilters.service_line || []}
                onChange={(values) => handleMultiSelectChange('service_line', values)}
                placeholder="Select service lines..."
              />

              <div className="filter-group">
                <label className="filter-label">Minimum Provider Visits</label>
                <input
                  type="number"
                  className="filter-input"
                  placeholder="0"
                  min="0"
                  value={localFilters.min_provider_visits || ''}
                  onChange={(e) => handleFilterChange('min_provider_visits', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
            </div>

          {/* Provider Group Filters - Third */}
          <div className="filter-section">
            <h4 className="section-title">Provider Groups</h4>

              <DropdownMultiSelect
                label="Provider Group"
                options={filterOptions.provider_groups}
                selectedValues={localFilters.provider_group || []}
                onChange={(values) => handleMultiSelectChange('provider_group', values)}
                placeholder="Select provider groups..."
                searchable={true}
              />

              <div className="filter-group">
                <label className="filter-label">Minimum Group Visits</label>
                <input
                  type="number"
                  className="filter-input"
                  placeholder="0"
                  min="0"
                  value={localFilters.min_group_visits || ''}
                  onChange={(e) => handleFilterChange('min_group_visits', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>

              <div className="filter-group">
                <label className="filter-label">Minimum Sites per Group</label>
                <input
                  type="number"
                  className="filter-input"
                  placeholder="0"
                  min="0"
                  value={localFilters.min_group_sites || ''}
                  onChange={(e) => handleFilterChange('min_group_sites', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
            </div>



          {/* Service Type Filters */}
          <div className="filter-section">
            <h4 className="section-title">Services</h4>
            
            <div className="filter-group">
              <label className="checkbox-item service-filter">
                <input
                  type="checkbox"
                  checked={localFilters.has_oncology || false}
                  onChange={(e) => handleFilterChange('has_oncology', e.target.checked || undefined)}
                />
                <span className="checkbox-label">
                  <span className="service-indicator oncology">●</span>
                  Has Oncology
                </span>
              </label>
            </div>

            <div className="filter-group">
              <label className="checkbox-item service-filter">
                <input
                  type="checkbox"
                  checked={localFilters.has_surgery || false}
                  onChange={(e) => handleFilterChange('has_surgery', e.target.checked || undefined)}
                />
                <span className="checkbox-label">
                  <span className="service-indicator surgery">●</span>
                  Has Surgery
                </span>
              </label>
            </div>

            <div className="filter-group">
              <label className="checkbox-item service-filter">
                <input
                  type="checkbox"
                  checked={localFilters.has_inpatient || false}
                  onChange={(e) => handleFilterChange('has_inpatient', e.target.checked || undefined)}
                />
                <span className="checkbox-label">
                  <span className="service-indicator inpatient">●</span>
                  Has Inpatient
                </span>
              </label>
            </div>
          </div>

          {/* Data Quality Filters */}
          <div className="filter-section">
            <h4 className="section-title">Data Quality</h4>
            
            <div className="filter-group">
              <label className="checkbox-item">
                <input
                  type="checkbox"
                  checked={localFilters.has_coordinates || false}
                  onChange={(e) => handleFilterChange('has_coordinates', e.target.checked || undefined)}
                />
                <span className="checkbox-label">Only show sites with coordinates</span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClaimsFiltersComponent;