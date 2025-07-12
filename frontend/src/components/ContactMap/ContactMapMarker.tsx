import React from 'react';
import { Marker, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { ContactMapMarker as ContactMapMarkerType } from '../../types/contact';
import ContactMapPopup from './ContactMapPopup';

interface ContactMapMarkerProps {
  marker: ContactMapMarkerType;
  isSelected: boolean;
  onClick: () => void;
}

// Create custom icon based on contact count
const createIcon = (count: number, isSelected: boolean) => {
  const size = count > 1 ? Math.min(30 + count * 2, 50) : 25;
  const color = isSelected ? '#e74c3c' : count > 1 ? '#3498db' : '#2ecc71';
  
  return L.divIcon({
    className: 'custom-contact-marker',
    html: `
      <div class="marker-pin ${isSelected ? 'selected' : ''}" style="background-color: ${color}; width: ${size}px; height: ${size}px;">
        ${count > 1 ? `<span class="marker-count">${count}</span>` : ''}
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
  });
};

const ContactMapMarker: React.FC<ContactMapMarkerProps> = ({
  marker,
  isSelected,
  onClick,
}) => {
  if (!marker.latitude || !marker.longitude) {
    return null;
  }

  const icon = createIcon(marker.contact_count, isSelected);

  return (
    <Marker
      position={[marker.latitude, marker.longitude]}
      icon={icon}
      eventHandlers={{
        click: onClick,
      }}
    >
      <Tooltip direction="top" offset={[0, -20]} opacity={0.9}>
        <div className="marker-tooltip">
          <strong>{marker.name}</strong>
          {marker.specialty && <div className="tooltip-specialty">{marker.specialty}</div>}
          {marker.organization && <div className="tooltip-org">{marker.organization}</div>}
          {marker.contact_count > 1 && (
            <div className="tooltip-count">{marker.contact_count} contacts at this location</div>
          )}
        </div>
      </Tooltip>
      <ContactMapPopup marker={marker} />
    </Marker>
  );
};

export default ContactMapMarker;