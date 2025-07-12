import React from 'react';
import { ContactListItem } from '../types/contact';
import './ContactList.css';

interface ContactListProps {
  contacts: ContactListItem[];
  selectedContactId?: string;
  onContactSelect: (contact: ContactListItem) => void;
  onViewDetails: (contact: ContactListItem) => void;
  loading?: boolean;
}

const ContactList: React.FC<ContactListProps> = ({
  contacts,
  selectedContactId,
  onContactSelect,
  onViewDetails,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="contact-list loading">
        <div className="contact-list-loader">Loading contacts...</div>
      </div>
    );
  }

  if (contacts.length === 0) {
    return (
      <div className="contact-list empty">
        <div className="empty-state">
          <p>No contacts found</p>
          <p className="empty-hint">Try adjusting your filters or search criteria</p>
        </div>
      </div>
    );
  }

  return (
    <div className="contact-list">
      {contacts.map((contact) => (
        <div
          key={contact.id}
          className={`contact-list-item ${contact.id === selectedContactId ? 'selected' : ''}`}
          onClick={() => onContactSelect(contact)}
        >
          <div className="contact-header">
            <h4 className="contact-name">{contact.name}</h4>
            {contact.is_physician && <span className="physician-badge">MD</span>}
          </div>
          
          {contact.specialty && (
            <div className="contact-specialty">{contact.specialty}</div>
          )}
          
          {contact.organization && (
            <div className="contact-organization">{contact.organization}</div>
          )}
          
          <div className="contact-location">
            {contact.city && contact.state && `${contact.city}, ${contact.state}`}
          </div>
          
          <div className="contact-actions">
            <button 
              className="contact-action-button"
              onClick={(e) => {
                e.stopPropagation();
                onContactSelect(contact);
              }}
            >
              Show on Map
            </button>
            <button 
              className="contact-action-button details"
              onClick={(e) => {
                e.stopPropagation();
                onViewDetails(contact);
              }}
            >
              View Details
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ContactList;