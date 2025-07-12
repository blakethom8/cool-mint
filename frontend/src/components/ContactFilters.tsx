import React, { useEffect, useState } from 'react';
import { ContactFilters as ContactFiltersType, ContactFilterOptions } from '../types/contact';
import contactService from '../services/contactService';
import './ContactFilters.css';

interface ContactFiltersProps {
  filters: ContactFiltersType;
  onFiltersChange: (filters: ContactFiltersType) => void;
}

const ContactFilters: React.FC<ContactFiltersProps> = ({ filters, onFiltersChange }) => {
  const [filterOptions, setFilterOptions] = useState<ContactFilterOptions | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
    try {
      setLoading(true);
      const options = await contactService.getFilterOptions();
      setFilterOptions(options);
    } catch (error) {
      console.error('Error loading filter options:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof ContactFiltersType, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const clearFilters = () => {
    onFiltersChange({
      active: true, // Keep active filter as default
    });
  };

  const hasActiveFilters = () => {
    return Object.keys(filters).some(key => 
      key !== 'active' && filters[key as keyof ContactFiltersType] !== undefined
    );
  };

  if (loading) {
    return <div className="contact-filters loading">Loading filters...</div>;
  }

  return (
    <div className="contact-filters">
      <div className="filters-header">
        <h3>Filters</h3>
        {hasActiveFilters() && (
          <button className="clear-filters-button" onClick={clearFilters}>
            Clear All
          </button>
        )}
      </div>

      <div className="filter-group">
        <label htmlFor="search">Search</label>
        <input
          id="search"
          type="text"
          placeholder="Name, email, or NPI..."
          value={filters.search || ''}
          onChange={(e) => handleFilterChange('search', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label htmlFor="specialty">Specialty</label>
        <select
          id="specialty"
          value={filters.specialty || ''}
          onChange={(e) => handleFilterChange('specialty', e.target.value)}
        >
          <option value="">All Specialties</option>
          {filterOptions?.specialties.map(specialty => (
            <option key={specialty} value={specialty}>
              {specialty}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="organization">Organization</label>
        <select
          id="organization"
          value={filters.organization || ''}
          onChange={(e) => handleFilterChange('organization', e.target.value)}
        >
          <option value="">All Organizations</option>
          {filterOptions?.organizations.map(org => (
            <option key={org} value={org}>
              {org}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="city">City</label>
        <select
          id="city"
          value={filters.city || ''}
          onChange={(e) => handleFilterChange('city', e.target.value)}
        >
          <option value="">All Cities</option>
          {filterOptions?.cities.map(city => (
            <option key={city} value={city}>
              {city}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="state">State</label>
        <select
          id="state"
          value={filters.state || ''}
          onChange={(e) => handleFilterChange('state', e.target.value)}
        >
          <option value="">All States</option>
          {filterOptions?.states.map(state => (
            <option key={state} value={state}>
              {state}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="geography">Geography</label>
        <select
          id="geography"
          value={filters.geography || ''}
          onChange={(e) => handleFilterChange('geography', e.target.value)}
        >
          <option value="">All Geographies</option>
          {filterOptions?.geographies.map(geo => (
            <option key={geo} value={geo}>
              {geo}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="panel_status">Panel Status</label>
        <select
          id="panel_status"
          value={filters.panel_status || ''}
          onChange={(e) => handleFilterChange('panel_status', e.target.value)}
        >
          <option value="">All Statuses</option>
          {filterOptions?.panel_statuses.map(status => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={filters.is_physician || false}
            onChange={(e) => handleFilterChange('is_physician', e.target.checked || undefined)}
          />
          Physicians Only
        </label>
      </div>

      <div className="filter-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={filters.active !== false}
            onChange={(e) => handleFilterChange('active', e.target.checked)}
          />
          Active Contacts Only
        </label>
      </div>
    </div>
  );
};

export default ContactFilters;