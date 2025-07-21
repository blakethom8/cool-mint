import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import { ContactMap } from '../components/ContactMap';
import ContactList from '../components/ContactList';
import ContactFilters from '../components/ContactFilters';
import contactService from '../services/contactService';
import {
  ContactMapMarker,
  ContactListItem,
  ContactFilters as ContactFiltersType,
} from '../types/contact';
import './ContactExplorer.css';

const ContactExplorer: React.FC = () => {
  const navigate = useNavigate();
  const [mapMarkers, setMapMarkers] = useState<ContactMapMarker[]>([]);
  const [contacts, setContacts] = useState<ContactListItem[]>([]);
  const [selectedContactId, setSelectedContactId] = useState<string | undefined>();
  const [filters, setFilters] = useState<ContactFiltersType>({ active: true });
  const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null);
  const [loadingMap, setLoadingMap] = useState(true);
  const [loadingList, setLoadingList] = useState(true);
  const [showFilters, setShowFilters] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMoreContacts, setHasMoreContacts] = useState(false);

  // Load map data
  useEffect(() => {
    loadMapData();
  }, [filters, mapBounds]);

  // Load contact list
  useEffect(() => {
    loadContacts();
  }, [filters, currentPage]);

  const loadMapData = async () => {
    try {
      setLoadingMap(true);
      
      const mapFilters = { ...filters };
      if (mapBounds) {
        mapFilters.north = mapBounds.getNorth();
        mapFilters.south = mapBounds.getSouth();
        mapFilters.east = mapBounds.getEast();
        mapFilters.west = mapBounds.getWest();
      }

      const response = await contactService.getMapData(mapFilters);
      setMapMarkers(response.markers);
    } catch (error) {
      console.error('Error loading map data:', error);
    } finally {
      setLoadingMap(false);
    }
  };

  const loadContacts = async () => {
    try {
      setLoadingList(true);
      const response = await contactService.getContacts(
        currentPage,
        50,
        filters
      );
      setContacts(response.items);
      setHasMoreContacts(response.has_more);
    } catch (error) {
      console.error('Error loading contacts:', error);
    } finally {
      setLoadingList(false);
    }
  };

  const handleMarkerClick = (marker: ContactMapMarker) => {
    setSelectedContactId(marker.id);
    // Find contact in list and scroll to it
    const contactElement = document.getElementById(`contact-${marker.id}`);
    if (contactElement) {
      contactElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const handleContactSelect = (contact: ContactListItem) => {
    setSelectedContactId(contact.id);
    // Map will auto-center on selected contact via CenterOnContact component
  };

  const handleViewDetails = (contact: ContactListItem) => {
    navigate(`/contacts/${contact.id}`);
  };

  const handleFiltersChange = (newFilters: ContactFiltersType) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page on filter change
  };

  const handleBoundsChange = useCallback((bounds: L.LatLngBounds) => {
    setMapBounds(bounds);
  }, []);

  return (
    <div className="contact-explorer">
      <div className="explorer-header">
        <h1>Market Explorer</h1>
        <div className="header-actions">
          <button 
            className="toggle-filters-button"
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
          <div className="contact-count">
            {mapMarkers.length} locations on map
          </div>
        </div>
      </div>

      <div className="explorer-content">
        {showFilters && (
          <div className="filters-panel">
            <ContactFilters 
              filters={filters}
              onFiltersChange={handleFiltersChange}
            />
          </div>
        )}

        <div className="map-panel">
          {loadingMap && (
            <div className="map-loading">
              <div className="loader">Loading map...</div>
            </div>
          )}
          <ContactMap
            markers={mapMarkers}
            selectedContactId={selectedContactId}
            onMarkerClick={handleMarkerClick}
            onBoundsChange={handleBoundsChange}
          />
        </div>

        <div className="list-panel">
          <div className="list-header">
            <h2>Contacts</h2>
            <span className="list-count">{contacts.length} results</span>
          </div>
          
          <ContactList
            contacts={contacts}
            selectedContactId={selectedContactId}
            onContactSelect={handleContactSelect}
            onViewDetails={handleViewDetails}
            loading={loadingList}
          />

          {hasMoreContacts && (
            <div className="pagination">
              <button 
                className="load-more-button"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={loadingList}
              >
                Load More
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContactExplorer;