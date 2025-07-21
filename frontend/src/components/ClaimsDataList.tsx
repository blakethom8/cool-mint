import React, { useState, useMemo } from 'react';
import { 
  ViewMode, 
  SiteOfServiceListItem, 
  ClaimsProviderListItem, 
  ProviderGroup,
  ClaimsStatistics 
} from '../types/claims';
import ExpandableProviderCard from './ExpandableProviderCard';
import './ClaimsDataList.css';

interface ClaimsDataListProps {
  viewMode: ViewMode;
  sites: SiteOfServiceListItem[];
  providers: ClaimsProviderListItem[];
  providerGroups: ProviderGroup[];
  statistics: ClaimsStatistics | null;
  selectedId?: string;
  onItemSelect: (id: string) => void;
  onItemDoubleClick?: (id: string) => void;
  onAddProviderToRelationships?: (provider: ClaimsProviderListItem) => void;
  loading?: boolean;
  isQuickView?: boolean;
}

type SortOption = 'name' | 'visits' | 'providers' | 'city' | 'specialty';
type SortDirection = 'asc' | 'desc';

const ClaimsDataList: React.FC<ClaimsDataListProps> = ({
  viewMode,
  sites,
  providers,
  providerGroups,
  statistics,
  selectedId,
  onItemSelect,
  onItemDoubleClick,
  onAddProviderToRelationships,
  loading = false,
  isQuickView = false,
}) => {
  const [sortBy, setSortBy] = useState<SortOption>('visits');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [expandedProviderId, setExpandedProviderId] = useState<string | null>(null);

  // Get the current data based on view mode
  const currentData = useMemo(() => {
    switch (viewMode) {
      case 'sites':
        return sites;
      case 'providers':
        return providers;
      case 'groups':
        return providerGroups;
      default:
        return [];
    }
  }, [viewMode, sites, providers, providerGroups]);

  // Sort the data
  const sortedData = useMemo(() => {
    if (!currentData) return [];

    return [...currentData].sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortBy) {
        case 'name':
          aValue = a.name?.toLowerCase() || '';
          bValue = b.name?.toLowerCase() || '';
          break;
        case 'visits':
          aValue = ('total_visits' in a) ? a.total_visits : 0;
          bValue = ('total_visits' in b) ? b.total_visits : 0;
          break;
        case 'providers':
          aValue = ('provider_count' in a) ? a.provider_count : 0;
          bValue = ('provider_count' in b) ? b.provider_count : 0;
          break;
        case 'city':
          aValue = ('city' in a) ? a.city?.toLowerCase() || '' : '';
          bValue = ('city' in b) ? b.city?.toLowerCase() || '' : '';
          break;
        case 'specialty':
          aValue = ('specialty' in a) ? a.specialty?.toLowerCase() || '' : '';
          bValue = ('specialty' in b) ? b.specialty?.toLowerCase() || '' : '';
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [currentData, sortBy, sortDirection]);


  const handleItemClick = (id: string) => {
    // If clicking the same item that's already selected, deselect it
    if (selectedId === id) {
      onItemSelect('');  // Pass empty string to clear selection
    } else {
      onItemSelect(id);
    }
  };

  const handleItemDoubleClick = (id: string) => {
    if (onItemDoubleClick) {
      onItemDoubleClick(id);
    }
  };

  const renderSiteItem = (site: SiteOfServiceListItem) => (
    <div
      key={site.id}
      className={`data-list-item ${selectedId === site.id ? 'selected' : ''}`}
      onClick={() => handleItemClick(site.id)}
      onDoubleClick={() => handleItemDoubleClick?.(site.id)}
    >
      <div className="item-header">
        <h4 className="item-name">{site.name}</h4>
        <div className="item-stats">
          <span className="stat-visits">{site.total_visits?.toLocaleString() || 0}</span>
          <span className="stat-label">visits</span>
        </div>
      </div>
      
      <div className="item-details">
        {site.site_type && (
          <span className="site-type-badge">{site.site_type}</span>
        )}
        {site.city && <span className="location">{site.city}</span>}
        {site.geomarket && site.city !== site.geomarket && (
          <span className="geomarket">• {site.geomarket}</span>
        )}
      </div>
      
      <div className="item-footer">
        <span className="provider-count">{site.provider_count || 0} providers</span>
      </div>
    </div>
  );

  const handleProviderExpand = (providerId: string) => {
    setExpandedProviderId(expandedProviderId === providerId ? null : providerId);
  };

  const handleAddToRelationships = (providerId: string) => {
    const provider = providers.find(p => p.id === providerId);
    if (provider && onAddProviderToRelationships) {
      onAddProviderToRelationships(provider);
    }
  };

  const handleViewDetails = (providerId: string) => {
    console.log('View details:', providerId);
    if (onItemDoubleClick) {
      onItemDoubleClick(providerId);
    }
  };

  const renderProviderItem = (provider: ClaimsProviderListItem) => (
    <ExpandableProviderCard
      key={provider.id}
      provider={provider}
      isSelected={selectedId === provider.id}
      isExpanded={expandedProviderId === provider.id}
      onSelect={handleItemClick}
      onExpand={handleProviderExpand}
      onAddToRelationships={handleAddToRelationships}
      onViewDetails={handleViewDetails}
    />
  );

  const renderProviderGroupItem = (group: ProviderGroup) => (
    <div
      key={group.name}
      className={`data-list-item ${selectedId === group.name ? 'selected' : ''}`}
      onClick={() => handleItemClick(group.name)}
      onDoubleClick={() => handleItemDoubleClick?.(group.name)}
    >
      <div className="item-header">
        <h4 className="item-name">{group.name}</h4>
        <div className="item-stats">
          <span className="stat-visits">{group.total_visits.toLocaleString()}</span>
          <span className="stat-label">visits</span>
        </div>
      </div>
      
      <div className="item-details">
        <span className="provider-count-badge">{group.provider_count} providers</span>
        {group.specialties.length > 0 && (
          <span className="specialties">
            {group.specialties.slice(0, 2).join(', ')}
            {group.specialties.length > 2 && ` +${group.specialties.length - 2} more`}
          </span>
        )}
      </div>
      
      <div className="item-footer">
        {group.geomarkets.length > 0 && (
          <span className="geomarkets">
            {group.geomarkets.slice(0, 2).join(', ')}
            {group.geomarkets.length > 2 && ` +${group.geomarkets.length - 2} more`}
          </span>
        )}
      </div>
    </div>
  );

  const renderItem = (item: any) => {
    switch (viewMode) {
      case 'sites':
        return renderSiteItem(item);
      case 'providers':
        return renderProviderItem(item);
      case 'groups':
        return renderProviderGroupItem(item);
      default:
        return null;
    }
  };

  const getSortOptions = (): Array<{ value: SortOption; label: string }> => {
    const baseOptions = [
      { value: 'name' as SortOption, label: 'Name' },
      { value: 'visits' as SortOption, label: 'Visits' },
    ];

    switch (viewMode) {
      case 'sites':
        return [
          ...baseOptions,
          { value: 'providers' as SortOption, label: 'Providers' },
          { value: 'city' as SortOption, label: 'City' },
        ];
      case 'providers':
        return [
          ...baseOptions,
          { value: 'specialty' as SortOption, label: 'Specialty' },
          { value: 'city' as SortOption, label: 'City' },
        ];
      case 'groups':
        return [
          ...baseOptions,
          { value: 'providers' as SortOption, label: 'Providers' },
        ];
      default:
        return baseOptions;
    }
  };

  const getViewModeTitle = () => {
    switch (viewMode) {
      case 'sites':
        return 'Sites of Service';
      case 'providers':
        return 'Healthcare Providers';
      case 'groups':
        return 'Provider Groups';
      default:
        return 'Data';
    }
  };

  const getEmptyMessage = () => {
    if (loading) return 'Loading...';
    
    switch (viewMode) {
      case 'sites':
        return 'No sites found matching your filters';
      case 'providers':
        return 'No providers found matching your filters';
      case 'groups':
        return 'No provider groups found matching your filters';
      default:
        return 'No data available';
    }
  };

  return (
    <div className="claims-data-list">
      <div className="list-header">
        <div className="header-title">
          <h2>{getViewModeTitle()}</h2>
          {statistics && (
            <div className="result-count">
              {sortedData.length.toLocaleString()} results
            </div>
          )}
        </div>
        
        <div className="list-controls">
          <select
            className="sort-select"
            value={`${sortBy}-${sortDirection}`}
            onChange={(e) => {
              const [option, direction] = e.target.value.split('-');
              setSortBy(option as SortOption);
              setSortDirection(direction as SortDirection);
            }}
          >
            {getSortOptions().map(option => (
              <React.Fragment key={option.value}>
                <option value={`${option.value}-desc`}>
                  {option.label} (High to Low)
                </option>
                <option value={`${option.value}-asc`}>
                  {option.label} (Low to High)
                </option>
              </React.Fragment>
            ))}
          </select>
        </div>
      </div>

      <div className="list-content">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <span>Loading {viewMode}...</span>
          </div>
        ) : sortedData.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📍</div>
            <div className="empty-message">{getEmptyMessage()}</div>
          </div>
        ) : (
          <div 
            className="data-items"
            onClick={(e) => {
              // Clear selection if clicking on empty space
              if (e.target === e.currentTarget) {
                onItemSelect('');
              }
            }}
          >
            {sortedData.map(renderItem)}
          </div>
        )}
      </div>

      {statistics && !loading && (
        <div className="list-footer">
          <div className="summary-stats">
            <div className="summary-item">
              <span className="summary-value">{statistics.total_visits.toLocaleString()}</span>
              <span className="summary-label">Total Visits</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{statistics.total_providers.toLocaleString()}</span>
              <span className="summary-label">Total Providers</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{statistics.total_sites.toLocaleString()}</span>
              <span className="summary-label">Total Sites</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClaimsDataList;