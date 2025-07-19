import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
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
  onMarkerClick: (marker: MapMarker) => void;
  onQuickView?: (marker: MapMarker) => void;
  onFullDetails?: (marker: MapMarker) => void;
  loading?: boolean;
}

const ClaimsMapSimple: React.FC<ClaimsMapSimpleProps> = ({
  markers,
  selectedSiteId,
  onMarkerClick,
  onQuickView,
  onFullDetails,
  loading = false,
}) => {
  console.log('ClaimsMapSimple rendering with', markers.length, 'markers');

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
        
        {markers.map((marker) => {
          if (!marker.latitude || !marker.longitude) return null;
          
          // Calculate radius based on visit volume
          const getRadius = (visits: number) => {
            if (visits >= 10000) return 12;
            if (visits >= 5000) return 10;
            if (visits >= 1000) return 8;
            if (visits >= 500) return 6;
            return 4;
          };
          
          // Get color based on site type
          const getColor = (siteType?: string) => {
            if (!siteType) return '#2ecc71'; // Default green
            const type = siteType.toLowerCase();
            if (type.includes('hospital')) return '#e74c3c'; // Red
            if (type.includes('clinic')) return '#3498db'; // Blue
            if (type.includes('surgery') || type.includes('surgical')) return '#f39c12'; // Orange
            if (type.includes('imaging') || type.includes('radiology')) return '#9b59b6'; // Purple
            if (type.includes('lab') || type.includes('laboratory')) return '#1abc9c'; // Teal
            return '#2ecc71'; // Default green
          };
          
          return (
            <CircleMarker
              key={marker.id}
              center={[marker.latitude, marker.longitude]}
              radius={getRadius(marker.total_visits)}
              fillColor={getColor(marker.site_type)}
              color='#fff'
              weight={2}
              opacity={1}
              fillOpacity={0.8}
              eventHandlers={{
                click: () => {
                  console.log('Marker clicked:', marker);
                  onMarkerClick(marker);
                },
              }}
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
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('Quick View clicked for:', marker.name);
                        if (onQuickView) {
                          onQuickView(marker);
                        }
                      }}
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
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('Full Details clicked for:', marker.name);
                        if (onFullDetails) {
                          onFullDetails(marker);
                        }
                      }}
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
        })}
      </MapContainer>
    </div>
  );
};

export default ClaimsMapSimple;