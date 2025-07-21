import React, { useState, useEffect } from 'react';
import { 
  ViewMode, 
  ClaimsFilters, 
  MapMarker,
  SiteOfServiceListItem,
  ClaimsProviderListItem,
  ProviderGroup,
  ClaimsStatistics
} from '../types/claims';
import ViewModeSelector from '../components/ViewModeSelector';
import ClaimsFiltersComponent from '../components/ClaimsFilters';
import ClaimsMapSimple from '../components/ClaimsMapSimple';
import ClaimsDataList from '../components/ClaimsDataList';
import QuickViewHeader from '../components/QuickViewHeader';
import claimsService from '../services/claimsService';
import './MarketExplorer.css';

const MarketExplorerDebug: React.FC = () => {
  console.log('MarketExplorerDebug rendering...');
  
  const [viewMode, setViewMode] = useState<ViewMode>('sites');
  const [showFilters, setShowFilters] = useState(true);
  const [filters, setFilters] = useState<ClaimsFilters>({});
  const [mapMarkers, setMapMarkers] = useState<MapMarker[]>([]);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [loadingMap, setLoadingMap] = useState(true);
  
  // List data states
  const [sites, setSites] = useState<SiteOfServiceListItem[]>([]);
  const [providers, setProviders] = useState<ClaimsProviderListItem[]>([]);
  const [providerGroups, setProviderGroups] = useState<ProviderGroup[]>([]);
  const [statistics, setStatistics] = useState<ClaimsStatistics | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  
  // Quick View state
  const [quickViewSiteId, setQuickViewSiteId] = useState<string | null>(null);
  const [quickViewSiteName, setQuickViewSiteName] = useState<string | null>(null);

  const handleFiltersChange = (newFilters: ClaimsFilters) => {
    console.log('Filters changed:', newFilters);
    setFilters(newFilters);
  };

  const loadMapData = async () => {
    try {
      setLoadingMap(true);
      console.log('Loading map data...');
      const response = await claimsService.getMapMarkers(filters);
      console.log('Map markers loaded:', response.markers.length);
      setMapMarkers(response.markers);
    } catch (error) {
      console.error('Error loading map data:', error);
    } finally {
      setLoadingMap(false);
    }
  };

  const handleMarkerClick = (marker: MapMarker) => {
    console.log('Marker clicked:', marker);
    setSelectedId(marker.id);
  };

  const loadListData = async () => {
    try {
      setLoadingList(true);
      console.log('Loading list data for', viewMode, 'quickView:', quickViewSiteId);
      
      // If in quick view mode, load providers for the specific site
      if (quickViewSiteId && viewMode === 'sites') {
        console.log('Loading providers for site:', quickViewSiteId);
        const siteProvidersResponse = await claimsService.getSiteProviders(quickViewSiteId, 1, 100);
        setProviders(siteProvidersResponse.items);
        setStatistics(siteProvidersResponse.statistics);
        // Clear sites and groups as we're showing providers
        setSites([]);
        setProviderGroups([]);
        return;
      }
      
      // Normal data loading
      switch (viewMode) {
        case 'sites':
          const sitesResponse = await claimsService.getSites(1, 100, filters);
          setSites(sitesResponse.items);
          setStatistics(sitesResponse.statistics);
          setProviders([]);
          setProviderGroups([]);
          break;
        case 'providers':
          const providersResponse = await claimsService.getProviders(1, 100, filters);
          setProviders(providersResponse.items);
          setStatistics(providersResponse.statistics);
          setSites([]);
          setProviderGroups([]);
          break;
        case 'groups':
          const groupsResponse = await claimsService.getProviderGroups(1, 100, filters);
          setProviderGroups(groupsResponse.items);
          setStatistics(groupsResponse.statistics);
          setSites([]);
          setProviders([]);
          break;
      }
    } catch (error) {
      console.error('Error loading list data:', error);
    } finally {
      setLoadingList(false);
    }
  };

  const handleItemSelect = (id: string) => {
    console.log('Item selected:', id);
    setSelectedId(id);
  };

  const handleItemDoubleClick = (id: string) => {
    console.log('Item double-clicked:', id);
    // TODO: Open detail window
  };
  
  const handleQuickView = (marker: MapMarker) => {
    console.log('Quick View for:', marker.name);
    setQuickViewSiteId(marker.id);
    setQuickViewSiteName(marker.name);
    // Force view mode to sites and reload data for this specific site
    if (viewMode !== 'sites') {
      setViewMode('sites');
    }
  };
  
  const handleFullDetails = (marker: MapMarker) => {
    console.log('Full Details for:', marker.name);
    // TODO: Open details modal
    alert(`Full details for ${marker.name} - Coming soon!`);
  };
  
  const clearQuickView = () => {
    setQuickViewSiteId(null);
    setQuickViewSiteName(null);
    // Reload normal list data
    loadListData();
  };

  // Load data on mount and when filters/viewMode/quickView change
  useEffect(() => {
    loadMapData();
    loadListData();
  }, [filters, viewMode, quickViewSiteId]);

  return (
    <div className="market-explorer">
      <div className="explorer-header">
        <div className="header-title">
          <h1>Market Explorer 2.0 - Debug</h1>
          <p className="header-subtitle">Debugging version - Current mode: {viewMode}</p>
        </div>
        
        <div className="header-controls">
          <ViewModeSelector
            currentMode={viewMode}
            onModeChange={setViewMode}
          />
          
          <button 
            className="toggle-filters-button"
            onClick={() => setShowFilters(!showFilters)}
          >
            <span className="filter-icon">🔍</span>
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
        </div>
      </div>

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
            viewMode={quickViewSiteId ? 'providers' : viewMode}
            sites={sites}
            providers={providers}
            providerGroups={providerGroups}
            statistics={statistics}
            selectedId={selectedId}
            onItemSelect={handleItemSelect}
            onItemDoubleClick={handleItemDoubleClick}
            loading={loadingList}
          />
        </div>
      </div>
    </div>
  );
};

export default MarketExplorerDebug;