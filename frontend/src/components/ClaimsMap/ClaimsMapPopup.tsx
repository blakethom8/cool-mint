import React from 'react';
import { Popup } from 'react-leaflet';
import { MapMarker } from '../../types/claims';

interface ClaimsMapPopupProps {
  marker: MapMarker;
}

const ClaimsMapPopup: React.FC<ClaimsMapPopupProps> = ({ marker }) => {
  // Simulate service data (in real implementation, this would come from backend)
  const services = [];
  if (marker.site_type?.toLowerCase().includes('hospital')) {
    services.push('Oncology', 'Surgery', 'Inpatient');
  } else if (marker.site_type?.toLowerCase().includes('surgery')) {
    services.push('Surgery');
  }

  // Format address from available data
  const getAddressString = () => {
    const parts = [marker.city, marker.geomarket].filter(Boolean);
    return parts.length > 0 ? parts.join(', ') : 'Address not available';
  };

  const handleViewDetails = () => {
    // In a real implementation, this would open a detail modal or navigate to a detail page
    console.log('View details for site:', marker.id);
  };

  const handleGetDirections = () => {
    if (marker.latitude && marker.longitude) {
      const url = `https://maps.google.com/?q=${marker.latitude},${marker.longitude}`;
      window.open(url, '_blank');
    }
  };

  return (
    <Popup>
      <div className="claims-popup">
        <h3>{marker.name}</h3>
        
        {marker.site_type && (
          <div className="popup-site-type">{marker.site_type}</div>
        )}
        
        <div className="popup-field">
          <strong>Total Visits:</strong>
          <span className="popup-field-value">{marker.total_visits.toLocaleString()}</span>
        </div>
        
        <div className="popup-field">
          <strong>Providers:</strong>
          <span className="popup-field-value">{marker.provider_count}</span>
        </div>
        
        {marker.geomarket && (
          <div className="popup-field">
            <strong>Geomarket:</strong>
            <span className="popup-field-value">{marker.geomarket}</span>
          </div>
        )}
        
        <div className="popup-location">
          <strong>Location:</strong> {getAddressString()}
        </div>
        
        {services.length > 0 && (
          <div className="popup-services">
            <h4>Available Services</h4>
            <div className="popup-services-list">
              {services.map(service => (
                <span key={service} className={`service-badge ${service.toLowerCase()}`}>
                  {service}
                </span>
              ))}
            </div>
          </div>
        )}
        
        <div className="popup-actions">
          <button 
            className="popup-button view-details"
            onClick={handleViewDetails}
          >
            View Details
          </button>
          <button 
            className="popup-button directions"
            onClick={handleGetDirections}
          >
            Get Directions
          </button>
        </div>
      </div>
    </Popup>
  );
};

export default ClaimsMapPopup;