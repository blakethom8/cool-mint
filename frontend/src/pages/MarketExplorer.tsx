import React, { useState, useEffect, useCallback } from 'react';
import { 
  MapMarker, 
  ClaimsFilters, 
  ViewMode, 
  SiteOfServiceListItem,
  ClaimsProviderListItem,
  ProviderGroup,
  ClaimsStatistics,
  MapBounds
} from '../types/claims';
import claimsService from '../services/claimsService';
import ClaimsMapSimple from '../components/ClaimsMapSimple';
import ClaimsFiltersComponent from '../components/ClaimsFilters';
import ClaimsDataList from '../components/ClaimsDataList';
import ViewModeSelector from '../components/ViewModeSelector';
import QuickViewHeader from '../components/QuickViewHeader';
import AddToRelationshipModal from '../components/AddToRelationshipModal';
import './MarketExplorer.css';

const MarketExplorer: React.FC = () => {
  // State management
  const [mapMarkers, setMapMarkers] = useState<MapMarker[]>([]);
  const [sites, setSites] = useState<SiteOfServiceListItem[]>([]);
  const [providers, setProviders] = useState<ClaimsProviderListItem[]>([]);
  const [providerGroups, setProviderGroups] = useState<ProviderGroup[]>([]);
  const [statistics, setStatistics] = useState<ClaimsStatistics | null>(null);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [highlightedSiteIds, setHighlightedSiteIds] = useState<string[]>([]);
  const [highlightMode, setHighlightMode] = useState<'single' | 'multiple' | 'none'>('none');
  const [filters, setFilters] = useState<ClaimsFilters>({});
  const [viewMode, setViewMode] = useState<ViewMode>('sites');
  const [showFilters, setShowFilters] = useState(true);
  
  // Quick View state
  const [quickViewSiteId, setQuickViewSiteId] = useState<string | null>(null);
  const [quickViewSiteName, setQuickViewSiteName] = useState<string | null>(null);
  
  // Loading states
  const [loadingMap, setLoadingMap] = useState(true);
  const [loadingList, setLoadingList] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal state for adding to relationships
  const [selectedProviderForModal, setSelectedProviderForModal] = useState<ClaimsProviderListItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Load data when filters, view mode, or quick view changes
  useEffect(() => {
    loadData();
  }, [filters, viewMode, quickViewSiteId]);

  const loadData = async () => {
    try {
      setLoadingMap(true);
      setLoadingList(true);
      setError(null);

      // Load map markers (always sites)
      const mapResponse = await claimsService.getMapMarkers(filters);
      setMapMarkers(mapResponse.markers);

      // Load list data based on view mode with filters (including quick view)
      const combinedFilters = quickViewSiteId 
        ? { ...filters, site_id: quickViewSiteId }
        : filters;

      switch (viewMode) {
        case 'sites':
          if (quickViewSiteId) {
            // In quick view, show only the selected site
            console.log('Loading site quick view for:', quickViewSiteId);
            const siteQuickViewResponse = await claimsService.getSiteQuickView(quickViewSiteId);
            setSites(siteQuickViewResponse.items);
            setStatistics(siteQuickViewResponse.statistics);
            setProviders([]);
            setProviderGroups([]);
          } else {
            const sitesResponse = await claimsService.getSites(1, 100, filters);
            setSites(sitesResponse.items);
            setStatistics(sitesResponse.statistics);
            setProviders([]);
            setProviderGroups([]);
          }
          break;
        case 'providers':
          if (quickViewSiteId) {
            // Show providers for the specific site
            console.log('Loading providers for site:', quickViewSiteId);
            const siteProvidersResponse = await claimsService.getSiteProviders(quickViewSiteId, 1, 100);
            setProviders(siteProvidersResponse.items);
            setStatistics(siteProvidersResponse.statistics);
          } else {
            const providersResponse = await claimsService.getProviders(1, 100, filters);
            setProviders(providersResponse.items);
            setStatistics(providersResponse.statistics);
          }
          setSites([]);
          setProviderGroups([]);
          break;
        case 'groups':
          if (quickViewSiteId) {
            // Show provider groups for the specific site
            console.log('Loading provider groups for site:', quickViewSiteId);
            const siteGroupsResponse = await claimsService.getSiteProviderGroups(quickViewSiteId, 1, 100);
            setProviderGroups(siteGroupsResponse.items);
            setStatistics(siteGroupsResponse.statistics);
          } else {
            const groupsResponse = await claimsService.getProviderGroups(1, 100, filters);
            setProviderGroups(groupsResponse.items);
            setStatistics(groupsResponse.statistics);
          }
          setSites([]);
          setProviders([]);
          break;
      }
    } catch (error: any) {
      console.error('Error loading data:', error);
      console.error('Error details:', {
        message: error?.message,
        response: error?.response,
        quickViewSiteId,
        viewMode,
        filters
      });
      setError(`Failed to load data: ${error?.message || 'Unknown error'}`);
    } finally {
      setLoadingMap(false);
      setLoadingList(false);
    }
  };

  const handleMarkerClick = useCallback((marker: MapMarker) => {
    setSelectedId(marker.id);
    // Marker click just selects the site, doesn't change view mode
  }, []);

  const handleFiltersChange = useCallback((newFilters: ClaimsFilters) => {
    setFilters(newFilters);
    setSelectedId(undefined);
    setHighlightedSiteIds([]);
    setHighlightMode('none');
  }, []);

  const handleViewModeChange = useCallback((newViewMode: ViewMode) => {
    setViewMode(newViewMode);
    setSelectedId(undefined);
    setHighlightedSiteIds([]);
    setHighlightMode('none');
  }, []);

  const handleItemSelect = useCallback(async (itemId: string) => {
    // Handle deselection
    if (!itemId || itemId === '') {
      setSelectedId(undefined);
      setHighlightedSiteIds([]);
      setHighlightMode('none');
      return;
    }
    
    setSelectedId(itemId);
    
    // Don't update highlighting if we're in Quick View mode
    // Quick View takes precedence over item selection
    if (quickViewSiteId) {
      console.log('In Quick View mode, maintaining Quick View highlighting');
      return;
    }
    
    // Update highlighting based on view mode
    try {
      switch (viewMode) {
        case 'sites':
          // For sites mode, highlight only the selected site
          setHighlightedSiteIds([itemId]);
          setHighlightMode('single');
          break;
          
        case 'providers':
          // For providers mode, fetch all sites where this provider operates
          const providerSites = await claimsService.getProviderSites(itemId);
          const siteIds = providerSites.map(site => site.id);
          setHighlightedSiteIds(siteIds);
          setHighlightMode(siteIds.length > 1 ? 'multiple' : 'single');
          break;
          
        case 'groups':
          // For groups mode, fetch all sites where this group operates
          const groupSites = await claimsService.getProviderGroupSites(itemId);
          const groupSiteIds = groupSites.map(site => site.id);
          setHighlightedSiteIds(groupSiteIds);
          setHighlightMode('multiple');
          break;
      }
    } catch (error) {
      console.error('Error fetching sites for highlighting:', error);
      // Fall back to no highlighting on error
      setHighlightedSiteIds([]);
      setHighlightMode('none');
    }
    
    // Find the marker for this item and center the map on it (for sites mode)
    if (viewMode === 'sites') {
      const marker = mapMarkers.find(m => m.id === itemId);
      if (marker) {
        // Map centering is handled in the ClaimsMap component
      }
    }
  }, [mapMarkers, viewMode, quickViewSiteId]);

  const handleItemDoubleClick = useCallback((itemId: string) => {
    // TODO: Open detail window for the selected item
    console.log('Double-clicked item:', itemId);
  }, []);

  const handleBoundsChange = useCallback((bounds: MapBounds) => {
    // TODO: Update filters based on map bounds if needed
    console.log('Map bounds changed:', bounds);
  }, []);

  const handleQuickView = (marker: MapMarker) => {
    console.log('Quick View for:', marker.name);
    setQuickViewSiteId(marker.id);
    setQuickViewSiteName(marker.name);
    // Quick view acts as a filter, not a view mode change
    // In quick view mode, highlight only the quick view site
    setHighlightedSiteIds([marker.id]);
    setHighlightMode('single');
  };
  
  const handleFullDetails = (marker: MapMarker) => {
    console.log('Full Details for:', marker.name);
    // TODO: Open details modal
    alert(`Full details for ${marker.name} - Coming soon!`);
  };
  
  const clearQuickView = () => {
    setQuickViewSiteId(null);
    setQuickViewSiteName(null);
    // Clear highlighting when exiting quick view
    setHighlightedSiteIds([]);
    setHighlightMode('none');
  };

  const refreshData = useCallback(() => {
    claimsService.clearCache();
    loadData();
  }, [filters, viewMode, quickViewSiteId]);

  const handleAddProviderToRelationships = useCallback((provider: ClaimsProviderListItem) => {
    setSelectedProviderForModal(provider);
    setIsModalOpen(true);
  }, []);

  const handleModalClose = useCallback(() => {
    setIsModalOpen(false);
    setSelectedProviderForModal(null);
  }, []);

  const handleModalSuccess = useCallback(() => {
    // Show success message or navigate to relationship manager
    console.log('Relationship created successfully');
    // You could add a toast notification here
  }, []);

  return (
    <div className="market-explorer">
      <div className="explorer-header">
        <div className="header-title">
          <h1>Market Explorer 2.0</h1>
          <p className="header-subtitle">Explore healthcare markets with claims intelligence</p>
        </div>
        
        <div className="header-controls">
          <ViewModeSelector
            currentMode={viewMode}
            onModeChange={handleViewModeChange}
          />
          
          <button 
            className="toggle-filters-button"
            onClick={() => setShowFilters(!showFilters)}
            title={showFilters ? 'Hide Filters' : 'Show Filters'}
          >
            <span className="filter-icon">🔍</span>
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
          
          <button 
            className="refresh-button"
            onClick={refreshData}
            title="Refresh Data"
          >
            <span className="refresh-icon">🔄</span>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="dismiss-error">×</button>
        </div>
      )}

      <div className="explorer-content">
        {showFilters && (
          <div className="filters-panel">
            <ClaimsFiltersComponent 
              filters={filters}
              onFiltersChange={handleFiltersChange}
              viewMode={viewMode}
            />
          </div>
        )}

        <div className="map-panel">
          <ClaimsMapSimple
            markers={mapMarkers}
            selectedSiteId={selectedId}
            highlightedSiteIds={highlightedSiteIds}
            highlightMode={highlightMode}
            onMarkerClick={handleMarkerClick}
            onQuickView={handleQuickView}
            onFullDetails={handleFullDetails}
            loading={loadingMap}
          />
        </div>

        <div className="list-panel">
          {quickViewSiteId && quickViewSiteName && (
            <QuickViewHeader 
              siteName={quickViewSiteName}
              onClose={clearQuickView}
            />
          )}
          <ClaimsDataList
            viewMode={viewMode}
            sites={sites}
            providers={providers}
            providerGroups={providerGroups}
            statistics={statistics}
            selectedId={selectedId}
            onItemSelect={handleItemSelect}
            onItemDoubleClick={handleItemDoubleClick}
            onAddProviderToRelationships={handleAddProviderToRelationships}
            loading={loadingList}
            isQuickView={!!quickViewSiteId}
          />
        </div>
      </div>
      
      {/* Add to Relationship Modal */}
      {selectedProviderForModal && (
        <AddToRelationshipModal
          provider={selectedProviderForModal}
          isOpen={isModalOpen}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
};

export default MarketExplorer;