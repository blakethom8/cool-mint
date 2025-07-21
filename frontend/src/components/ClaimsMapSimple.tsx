import React, { useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './ClaimsMapSimple.css';
import L from 'leaflet';
import { MapMarker } from '../types/claims';

// Fix for default Leaflet icon issue without importing images
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface ClaimsMapSimpleProps {
  markers: MapMarker[];
  selectedSiteId?: string;
  highlightedSiteIds?: string[];
  highlightMode?: 'single' | 'multiple' | 'none';
  onMarkerClick: (marker: MapMarker) => void;
  onQuickView?: (marker: MapMarker) => void;
  onFullDetails?: (marker: MapMarker) => void;
  loading?: boolean;
}

// Static helper functions to prevent recreation
const getRadius = (visits: number): number => {
  if (visits >= 10000) return 12;
  if (visits >= 5000) return 10;
  if (visits >= 1000) return 8;
  if (visits >= 500) return 6;
  return 4;
};

const getSiteTypeColor = (siteType?: string): string => {
  if (!siteType) return '#2ecc71';
  const type = siteType.toLowerCase();
  if (type.includes('hospital')) return '#e74c3c';
  if (type.includes('clinic')) return '#3498db';
  if (type.includes('surgery') || type.includes('surgical')) return '#f39c12';
  if (type.includes('imaging') || type.includes('radiology')) return '#9b59b6';
  if (type.includes('lab') || type.includes('laboratory')) return '#1abc9c';
  return '#2ecc71';
};

// Create stable path options configurations
const createPathOptions = (
  marker: MapMarker,
  isHighlighted: boolean,
  isInactive: boolean
) => {
  const baseRadius = getRadius(marker.total_visits);
  
  const baseOptions = {
    radius: baseRadius,
    fillColor: isInactive ? '#e0e0e0' : getSiteTypeColor(marker.site_type),
    color: '#fff',
    weight: 2,
    opacity: 1,
    fillOpacity: 0.8,
  };

  if (isHighlighted) {
    return {
      ...baseOptions,
      radius: baseRadius + 2, // Make highlighted markers slightly larger
      fillColor: getSiteTypeColor(marker.site_type), // Keep original color
      color: '#333', // Dark border for contrast
      weight: 4, // Thicker border
      opacity: 1,
      fillOpacity: 0.95,
    };
  }

  if (isInactive) {
    return {
      ...baseOptions,
      color: '#ccc',
      weight: 1, // Thinner border
      opacity: 0.15, // Very low opacity
      fillOpacity: 0.1, // Almost transparent
    };
  }

  return baseOptions;
};

// Memoized marker component to prevent unnecessary re-renders
const MemoizedCircleMarker = React.memo<{
  marker: MapMarker;
  isHighlighted: boolean;
  isInactive: boolean;
  onMarkerClick: (marker: MapMarker) => void;
  onQuickView?: (marker: MapMarker) => void;
  onFullDetails?: (marker: MapMarker) => void;
}>(({ marker, isHighlighted, isInactive, onMarkerClick, onQuickView, onFullDetails }) => {
  // Memoize path options to keep them stable
  const pathOptions = useMemo(
    () => createPathOptions(marker, isHighlighted, isInactive),
    [marker.id, marker.total_visits, marker.site_type, isHighlighted, isInactive]
  );

  // Stable event handler
  const handleClick = useCallback(() => {
    console.log('Marker clicked:', marker);
    onMarkerClick(marker);
  }, [marker, onMarkerClick]);

  const handleQuickView = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    console.log('Quick View clicked for:', marker.name);
    if (onQuickView) {
      onQuickView(marker);
    }
  }, [marker, onQuickView]);

  const handleFullDetails = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    console.log('Full Details clicked for:', marker.name);
    if (onFullDetails) {
      onFullDetails(marker);
    }
  }, [marker, onFullDetails]);

  const className = isHighlighted 
    ? 'marker-highlighted' 
    : isInactive 
    ? 'marker-inactive' 
    : 'marker-normal';

  return (
    <CircleMarker
      key={marker.id}
      center={[marker.latitude, marker.longitude]}
      pathOptions={pathOptions}
      eventHandlers={{ click: handleClick }}
      className={className}
    >
      <Popup>
        <div style={{ minWidth: '250px' }}>
          <h4 style={{ margin: '0 0 10px 0', borderBottom: '1px solid #e0e0e0', paddingBottom: '8px' }}>
            {marker.name}
          </h4>
          
          <div style={{ marginBottom: '12px' }}>
            <p style={{ margin: '4px 0' }}><strong>Type:</strong> {marker.site_type || 'Unknown'}</p>
            <p style={{ margin: '4px 0' }}><strong>Visits:</strong> {marker.total_visits.toLocaleString()}</p>
            <p style={{ margin: '4px 0' }}><strong>Providers:</strong> {marker.provider_count}</p>
            {marker.city && <p style={{ margin: '4px 0' }}><strong>City:</strong> {marker.city}</p>}
            {marker.geomarket && <p style={{ margin: '4px 0' }}><strong>Geomarket:</strong> {marker.geomarket}</p>}
          </div>
          
          <div style={{ 
            display: 'flex', 
            gap: '8px', 
            marginTop: '12px',
            borderTop: '1px solid #e0e0e0',
            paddingTop: '12px'
          }}>
            <button
              onClick={handleQuickView}
              style={{
                flex: 1,
                padding: '8px 12px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2980b9'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3498db'}
            >
              Quick View
            </button>
            
            <button
              onClick={handleFullDetails}
              style={{
                flex: 1,
                padding: '8px 12px',
                backgroundColor: '#27ae60',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#229954'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#27ae60'}
            >
              Full Details
            </button>
          </div>
        </div>
      </Popup>
    </CircleMarker>
  );
});

MemoizedCircleMarker.displayName = 'MemoizedCircleMarker';

const ClaimsMapSimple: React.FC<ClaimsMapSimpleProps> = ({
  markers,
  selectedSiteId,
  highlightedSiteIds = [],
  highlightMode = 'none',
  onMarkerClick,
  onQuickView,
  onFullDetails,
  loading = false,
}) => {
  // Create a set for faster lookups
  const highlightedSet = useMemo(
    () => new Set(highlightedSiteIds),
    [highlightedSiteIds]
  );

  // Memoize the marker highlight states and sort for z-index
  const markerStates = useMemo(() => {
    const hasHighlights = highlightMode !== 'none' && highlightedSiteIds.length > 0;
    
    const states = markers.map(marker => ({
      marker,
      isHighlighted: hasHighlights && highlightedSet.has(marker.id),
      isInactive: hasHighlights && !highlightedSet.has(marker.id),
    }));
    
    // Sort so highlighted markers render last (on top)
    if (hasHighlights) {
      states.sort((a, b) => {
        if (a.isHighlighted && !b.isHighlighted) return 1;
        if (!a.isHighlighted && b.isHighlighted) return -1;
        return 0;
      });
    }
    
    return states;
  }, [markers, highlightMode, highlightedSet]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {loading && (
        <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 1000, background: 'white', padding: '10px' }}>
          Loading map data...
        </div>
      )}
      
      <MapContainer
        center={[34.0522, -118.2437]} // Los Angeles
        zoom={10}
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {markerStates.map(({ marker, isHighlighted, isInactive }) => {
          if (!marker.latitude || !marker.longitude) return null;
          
          return (
            <MemoizedCircleMarker
              key={marker.id}
              marker={marker}
              isHighlighted={isHighlighted}
              isInactive={isInactive}
              onMarkerClick={onMarkerClick}
              onQuickView={onQuickView}
              onFullDetails={onFullDetails}
            />
          );
        })}
      </MapContainer>
    </div>
  );
};

export default ClaimsMapSimple;