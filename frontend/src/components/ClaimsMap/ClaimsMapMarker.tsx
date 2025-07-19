import React from 'react';
import { Marker, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { MapMarker } from '../../types/claims';
import ClaimsMapPopup from './ClaimsMapPopup';

interface ClaimsMapMarkerProps {
  marker: MapMarker;
  isSelected: boolean;
  onClick: () => void;
}

// Get site type category for styling
const getSiteTypeCategory = (siteType?: string): string => {
  if (!siteType) return 'default';
  
  const type = siteType.toLowerCase();
  if (type.includes('hospital')) return 'hospital';
  if (type.includes('clinic')) return 'clinic';
  if (type.includes('surgery') || type.includes('surgical')) return 'surgery-center';
  if (type.includes('imaging') || type.includes('radiology')) return 'imaging';
  if (type.includes('lab') || type.includes('laboratory')) return 'lab';
  return 'default';
};

// Format visit count for display
const formatVisitCount = (count: number): string => {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
  return count.toString();
};

// Determine marker size based on visit volume
const getMarkerSize = (visitCount: number): number => {
  if (visitCount >= 10000) return 45;
  if (visitCount >= 5000) return 38;
  if (visitCount >= 1000) return 32;
  if (visitCount >= 500) return 28;
  return 24;
};

// Get font size class based on marker size
const getFontSizeClass = (size: number): string => {
  if (size >= 38) return 'xlarge';
  if (size >= 32) return 'large';
  return '';
};

// Create custom icon based on site data
const createClaimsIcon = (marker: MapMarker, isSelected: boolean) => {
  const size = getMarkerSize(marker.total_visits);
  const category = getSiteTypeCategory(marker.site_type);
  const fontSizeClass = getFontSizeClass(size);
  
  // Determine which services are available (would come from backend)
  const services = [];
  // Note: In a real implementation, these would be passed in the marker data
  // For now, we'll simulate based on site type
  if (marker.site_type?.toLowerCase().includes('hospital')) {
    services.push('oncology', 'surgery', 'inpatient');
  } else if (marker.site_type?.toLowerCase().includes('surgery')) {
    services.push('surgery');
  }
  
  const serviceIndicators = services.map(service => 
    `<div class="service-indicator ${service}"></div>`
  ).join('');
  
  return L.divIcon({
    className: 'custom-claims-marker',
    html: `
      <div class="claims-marker-pin ${category} ${isSelected ? 'selected' : ''}" style="width: ${size}px; height: ${size}px;">
        <span class="marker-visit-count ${fontSizeClass}">${formatVisitCount(marker.total_visits)}</span>
        ${serviceIndicators ? `<div class="service-indicators">${serviceIndicators}</div>` : ''}
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
  });
};

const ClaimsMapMarker: React.FC<ClaimsMapMarkerProps> = ({
  marker,
  isSelected,
  onClick,
}) => {
  if (!marker.latitude || !marker.longitude) {
    return null;
  }

  const icon = createClaimsIcon(marker, isSelected);

  // Simulate service data for tooltip (in real implementation, this would come from backend)
  const services = [];
  if (marker.site_type?.toLowerCase().includes('hospital')) {
    services.push('Oncology', 'Surgery', 'Inpatient');
  } else if (marker.site_type?.toLowerCase().includes('surgery')) {
    services.push('Surgery');
  }

  return (
    <Marker
      position={[marker.latitude, marker.longitude]}
      icon={icon}
      eventHandlers={{
        click: onClick,
      }}
    >
      <Tooltip direction="top" offset={[0, -20]} opacity={0.95}>
        <div className="claims-marker-tooltip">
          <div className="tooltip-site-name">{marker.name}</div>
          
          {marker.site_type && (
            <div className="tooltip-site-type">{marker.site_type}</div>
          )}
          
          {(marker.city || marker.geomarket) && (
            <div className="tooltip-location">
              {[marker.city, marker.geomarket].filter(Boolean).join(', ')}
            </div>
          )}
          
          <div className="tooltip-stats">
            <div className="stat-item">
              <div className="stat-value">{marker.total_visits.toLocaleString()}</div>
              <div className="stat-label">Visits</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{marker.provider_count}</div>
              <div className="stat-label">Providers</div>
            </div>
          </div>
          
          {services.length > 0 && (
            <div className="tooltip-services">
              <div className="services-label">Services</div>
              <div className="services-list">
                {services.map(service => (
                  <span key={service} className={`service-badge ${service.toLowerCase()}`}>
                    {service}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </Tooltip>
      <ClaimsMapPopup marker={marker} />
    </Marker>
  );
};

export default ClaimsMapMarker;