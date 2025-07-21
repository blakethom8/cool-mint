import React from 'react';
import { Popup } from 'react-leaflet';
import { ContactMapMarker } from '../../types/contact';

interface ContactMapPopupProps {
  marker: ContactMapMarker;
}

const ContactMapPopup: React.FC<ContactMapPopupProps> = ({ marker }) => {
  return (
    <Popup>
      <div className="contact-popup">
        <h3>{marker.name}</h3>
        
        {marker.specialty && (
          <div className="popup-field">
            <strong>Specialty:</strong> {marker.specialty}
          </div>
        )}
        
        {marker.organization && (
          <div className="popup-field">
            <strong>Organization:</strong> {marker.organization}
          </div>
        )}
        
        {marker.mailing_address && (
          <div className="popup-field">
            <strong>Address:</strong>
            <div className="popup-address">{marker.mailing_address}</div>
          </div>
        )}
        
        {marker.contact_count > 1 && (
          <div className="popup-field">
            <strong>Contacts at this location:</strong> {marker.contact_count}
          </div>
        )}
        
        <div className="popup-actions">
          <button className="popup-button view-details">
            View Details
          </button>
          {marker.mailing_address && (
            <button 
              className="popup-button directions"
              onClick={() => {
                const address = encodeURIComponent(marker.mailing_address);
                window.open(`https://maps.google.com/?q=${address}`, '_blank');
              }}
            >
              Get Directions
            </button>
          )}
        </div>
      </div>
    </Popup>
  );
};

export default ContactMapPopup;