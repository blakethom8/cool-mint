import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { MapMarker, MapBounds } from '../../types/claims';
import ClaimsMapMarker from './ClaimsMapMarker';
import ClaimsMapControls from './ClaimsMapControls';
import './ClaimsMap.css';

// Fix Leaflet icon issue with webpack
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface ClaimsMapProps {
  markers: MapMarker[];
  selectedSiteId?: string;
  onMarkerClick: (marker: MapMarker) => void;
  onBoundsChange?: (bounds: MapBounds) => void;
  center?: [number, number];
  zoom?: number;
  loading?: boolean;
}

// Component to handle map events
function MapEventHandler({ 
  onBoundsChange 
}: { 
  onBoundsChange?: (bounds: MapBounds) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (!onBoundsChange) return;

    const handleMoveEnd = () => {
      const bounds = map.getBounds();
      const mapBounds: MapBounds = {
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      };
      onBoundsChange(mapBounds);
    };

    map.on('moveend', handleMoveEnd);
    map.on('zoomend', handleMoveEnd);
    
    return () => {
      map.off('moveend', handleMoveEnd);
      map.off('zoomend', handleMoveEnd);
    };
  }, [map, onBoundsChange]);

  return null;
}

// Component to handle centering on selected site
function CenterOnSite({ 
  marker, 
  zoom = 15 
}: { 
  marker?: MapMarker; 
  zoom?: number;
}) {
  const map = useMap();

  useEffect(() => {
    if (marker && marker.latitude && marker.longitude) {
      map.setView([marker.latitude, marker.longitude], zoom, {
        animate: true,
        duration: 1,
      });
    }
  }, [marker, map, zoom]);

  return null;
}

// Component to fit map to show all markers
function FitBounds({ 
  markers, 
  shouldFit 
}: { 
  markers: MapMarker[]; 
  shouldFit: boolean;
}) {
  const map = useMap();

  useEffect(() => {
    if (!shouldFit || markers.length === 0) return;

    const validMarkers = markers.filter(m => m.latitude && m.longitude);
    if (validMarkers.length === 0) return;

    if (validMarkers.length === 1) {
      const marker = validMarkers[0];
      map.setView([marker.latitude, marker.longitude], 12);
    } else {
      const bounds = L.latLngBounds(
        validMarkers.map(m => [m.latitude, m.longitude])
      );
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [markers, shouldFit, map]);

  return null;
}

const ClaimsMap: React.FC<ClaimsMapProps> = ({
  markers,
  selectedSiteId,
  onMarkerClick,
  onBoundsChange,
  center = [34.0522, -118.2437], // Default to Los Angeles
  zoom = 10,
  loading = false,
}) => {
  const mapRef = useRef<L.Map | null>(null);
  const [shouldFitBounds, setShouldFitBounds] = useState(false);
  const selectedMarker = markers.find(m => m.id === selectedSiteId);

  // Trigger fit bounds when markers change significantly
  useEffect(() => {
    if (markers.length > 0) {
      setShouldFitBounds(true);
      // Reset the flag after a short delay
      const timer = setTimeout(() => setShouldFitBounds(false), 100);
      return () => clearTimeout(timer);
    }
  }, [markers.length]);

  const handleResetView = () => {
    if (markers.length > 0) {
      setShouldFitBounds(true);
      setTimeout(() => setShouldFitBounds(false), 100);
    }
  };

  return (
    <div className="claims-map-container">
      {loading && (
        <div className="map-loading">
          <div className="loader">Loading map data...</div>
        </div>
      )}
      
      <MapContainer
        center={center}
        zoom={zoom}
        className="claims-map"
        ref={mapRef}
        zoomControl={false} // We'll add our own
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        
        <MapEventHandler onBoundsChange={onBoundsChange} />
        <CenterOnSite marker={selectedMarker} />
        <FitBounds markers={markers} shouldFit={shouldFitBounds} />
        <ClaimsMapControls 
          onResetView={handleResetView}
          defaultCenter={center}
          defaultZoom={zoom}
        />
        
        {markers.map((marker) => (
          <ClaimsMapMarker
            key={marker.id}
            marker={marker}
            isSelected={marker.id === selectedSiteId}
            onClick={() => onMarkerClick(marker)}
          />
        ))}
      </MapContainer>
    </div>
  );
};

export default ClaimsMap;