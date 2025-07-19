import React, { useState, useEffect, useCallback } from 'react';
import { ClaimsFilters, FilterOptions, ViewMode } from '../types/claims';
import claimsService from '../services/claimsService';
import './ClaimsFilters.css';

interface ClaimsFiltersProps {
  filters: ClaimsFilters;
  onFiltersChange: (filters: ClaimsFilters) => void;
  viewMode: ViewMode;
}

const ClaimsFiltersComponent: React.FC<ClaimsFiltersProps> = ({
  filters,
  onFiltersChange,
  viewMode,
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

  const handleMultiSelectChange = useCallback((key: keyof ClaimsFilters, value: string, checked: boolean) => {
    const currentValues = (localFilters[key] as string[]) || [];
    const newValues = checked
      ? [...currentValues, value]
      : currentValues.filter(v => v !== value);
    
    handleFilterChange(key, newValues.length > 0 ? newValues : undefined);
  }, [localFilters, handleFilterChange]);

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
            
            <div className="filter-group">
              <label className="filter-label">Geomarket</label>
              <div className="checkbox-list">
                {filterOptions.geomarkets.slice(0, 10).map(geomarket => (
                  <label key={geomarket} className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={(localFilters.geomarket || []).includes(geomarket)}
                      onChange={(e) => handleMultiSelectChange('geomarket', geomarket, e.target.checked)}
                    />
                    <span className="checkbox-label">{geomarket}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="filter-group">
              <label className="filter-label">City</label>
              <div className="checkbox-list">
                {filterOptions.cities.slice(0, 15).map(city => (
                  <label key={city} className="checkbox-item">
                    <input
                      type="checkbox"
                      checked={(localFilters.city || []).includes(city)}
                      onChange={(e) => handleMultiSelectChange('city', city, e.target.checked)}
                    />
                    <span className="checkbox-label">{city}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Provider Filters */}
          <div className="filter-section">
            <h4 className="section-title">Providers</h4>
              
              <div className="filter-group">
                <label className="filter-label">Specialty</label>
                <div className="checkbox-list">
                  {filterOptions.specialties.slice(0, 12).map(specialty => (
                    <label key={specialty} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={(localFilters.specialty || []).includes(specialty)}
                        onChange={(e) => handleMultiSelectChange('specialty', specialty, e.target.checked)}
                      />
                      <span className="checkbox-label">{specialty}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="filter-group">
                <label className="filter-label">Provider Group</label>
                <div className="checkbox-list">
                  {filterOptions.provider_groups.slice(0, 10).map(group => (
                    <label key={group} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={(localFilters.provider_group || []).includes(group)}
                        onChange={(e) => handleMultiSelectChange('provider_group', group, e.target.checked)}
                      />
                      <span className="checkbox-label">{group}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

          {/* Site Filters */}
          <div className="filter-section">
            <h4 className="section-title">Sites</h4>
              
              <div className="filter-group">
                <label className="filter-label">Site Type</label>
                <div className="checkbox-list">
                  {filterOptions.site_types.map(type => (
                    <label key={type} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={(localFilters.site_type || []).includes(type)}
                        onChange={(e) => handleMultiSelectChange('site_type', type, e.target.checked)}
                      />
                      <span className="checkbox-label">{type}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

          {/* Visit Volume Filters */}
          <div className="filter-section">
            <h4 className="section-title">Visit Volume</h4>
            
            <div className="filter-group">
              <label className="filter-label">Minimum Visits</label>
              <input
                type="number"
                className="filter-input"
                placeholder="0"
                min="0"
                value={localFilters.min_visits || ''}
                onChange={(e) => handleFilterChange('min_visits', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>

            <div className="filter-group">
              <label className="filter-label">Maximum Visits</label>
              <input
                type="number"
                className="filter-input"
                placeholder="No limit"
                min="0"
                value={localFilters.max_visits || ''}
                onChange={(e) => handleFilterChange('max_visits', e.target.value ? parseInt(e.target.value) : undefined)}
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