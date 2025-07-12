import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { ContactMapMarker as ContactMapMarkerType } from '../../types/contact';
import ContactMapMarker from './ContactMapMarker';
import MapControls from './MapControls';
import './ContactMap.css';

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

interface ContactMapProps {
  markers: ContactMapMarkerType[];
  selectedContactId?: string;
  onMarkerClick: (contact: ContactMapMarkerType) => void;
  onBoundsChange?: (bounds: L.LatLngBounds) => void;
  center?: [number, number];
  zoom?: number;
}

// Component to handle map events
function MapEventHandler({ onBoundsChange }: { onBoundsChange?: (bounds: L.LatLngBounds) => void }) {
  const map = useMap();

  useEffect(() => {
    if (!onBoundsChange) return;

    const handleMoveEnd = () => {
      const bounds = map.getBounds();
      onBoundsChange(bounds);
    };

    map.on('moveend', handleMoveEnd);
    return () => {
      map.off('moveend', handleMoveEnd);
    };
  }, [map, onBoundsChange]);

  return null;
}

// Component to handle centering on selected contact
function CenterOnContact({ contact, zoom = 15 }: { contact?: ContactMapMarkerType; zoom?: number }) {
  const map = useMap();

  useEffect(() => {
    if (contact && contact.latitude && contact.longitude) {
      map.setView([contact.latitude, contact.longitude], zoom, {
        animate: true,
        duration: 1,
      });
    }
  }, [contact, map, zoom]);

  return null;
}

const ContactMap: React.FC<ContactMapProps> = ({
  markers,
  selectedContactId,
  onMarkerClick,
  onBoundsChange,
  center = [34.0522, -118.2437], // Default to Los Angeles
  zoom = 10,
}) => {
  const mapRef = useRef<L.Map | null>(null);
  const selectedContact = markers.find(m => m.id === selectedContactId);

  return (
    <div className="contact-map-container">
      <MapContainer
        center={center}
        zoom={zoom}
        className="contact-map"
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        
        <MapEventHandler onBoundsChange={onBoundsChange} />
        <CenterOnContact contact={selectedContact} />
        <MapControls />
        
        {markers.map((marker) => (
          <ContactMapMarker
            key={marker.id}
            marker={marker}
            isSelected={marker.id === selectedContactId}
            onClick={() => onMarkerClick(marker)}
          />
        ))}
      </MapContainer>
    </div>
  );
};

export default ContactMap;