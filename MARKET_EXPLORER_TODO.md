# Market Explorer Feature - Development Todo

## Overview
Build a read-only map interface for physician liaisons to explore contacts geographically, view practice locations, and access contact information through an interactive map of Los Angeles and other regions.

## Mapping Library Analysis

### Option 1: React Leaflet (RECOMMENDED)
**Pros:**
- Lightweight (~42KB core library)
- Open-source with MIT license
- No API key required (uses OpenStreetMap by default)
- Extensive plugin ecosystem
- Great React integration with hooks support
- Mobile-friendly with touch gestures
- Clustering support via plugins
- Custom marker styling capabilities

**Cons:**
- Requires CSS import for proper styling
- Less built-in features compared to commercial solutions

### Option 2: Google Maps React
**Pros:**
- Familiar Google Maps interface
- Rich feature set (Street View, satellite imagery)
- Excellent geocoding services
- Good documentation

**Cons:**
- Requires API key and billing account
- Usage limits and costs
- Heavier bundle size
- Vendor lock-in

### Option 3: Mapbox GL JS
**Pros:**
- Beautiful default styling
- WebGL-powered for performance
- Advanced data visualization features
- Good for large datasets

**Cons:**
- Requires API key
- More complex setup
- Pricing for commercial use
- Larger bundle size (~200KB)

### Option 4: Deck.gl
**Pros:**
- Excellent for data visualization
- WebGL performance
- 3D capabilities

**Cons:**
- Overkill for simple markers
- Steeper learning curve
- Better suited for analytics dashboards

## Development Todos

### Phase 1: Backend API Development

- [ ] Create Contact Schema Models
  - [ ] Create `app/schemas/contact_schema.py`
  - [ ] Define `ContactListItem` model (minimal fields for map markers)
  - [ ] Define `ContactDetail` model (full contact information)
  - [ ] Define `ContactMapMarker` model (id, name, lat, lng, count)
  - [ ] Define `ContactFilterOptions` model
  - [ ] Define `ContactListResponse` with pagination support

- [ ] Create Contact API Endpoints
  - [ ] Create `app/api/contacts.py`
  - [ ] Implement `GET /api/contacts/map-data` endpoint
    - Return optimized data for map markers
    - Group contacts by address
    - Include count for marker sizing
  - [ ] Implement `GET /api/contacts/{contact_id}` endpoint
  - [ ] Implement `GET /api/contacts` with pagination
  - [ ] Implement `GET /api/contacts/filter-options`
  - [ ] Add geographic bounding box filter support

- [ ] Update API Router
  - [ ] Import contact router in `app/api/__init__.py`
  - [ ] Add contact routes to main router

### Phase 2: Frontend Setup

- [ ] Install Dependencies
  - [ ] Run `npm install react-leaflet leaflet`
  - [ ] Run `npm install --save-dev @types/leaflet`
  - [ ] Add Leaflet CSS import to main App component

- [ ] Create Base Map Components
  - [ ] Create `frontend/src/components/ContactMap/` directory
  - [ ] Create `ContactMap.tsx` - Main map container
  - [ ] Create `ContactMapMarker.tsx` - Custom marker component
  - [ ] Create `ContactMapPopup.tsx` - Popup for contact details
  - [ ] Create `MapControls.tsx` - Zoom and layer controls
  - [ ] Create `ContactMap.css` - Map-specific styles

### Phase 3: Contact Service Layer

- [ ] Create Contact Service
  - [ ] Create `frontend/src/services/contactService.ts`
  - [ ] Implement `getMapData()` function
  - [ ] Implement `getContactDetails()` function
  - [ ] Implement `getFilterOptions()` function
  - [ ] Add response caching for performance

- [ ] Create Contact Types
  - [ ] Create `frontend/src/types/contact.ts`
  - [ ] Define TypeScript interfaces matching backend schemas

### Phase 4: Main Contact Explorer Page

- [ ] Create Contact Explorer Page
  - [ ] Create `frontend/src/pages/ContactExplorer.tsx`
  - [ ] Create `frontend/src/pages/ContactExplorer.css`
  - [ ] Implement split-pane layout (map left, list right)
  - [ ] Add responsive mobile layout

- [ ] Add Navigation Entry
  - [ ] Update `Navigation.tsx` to include "Contact Explorer"
  - [ ] Add route in `App.tsx`

### Phase 5: Core Features Implementation

- [ ] Map Interaction Features
  - [ ] Implement marker click to show popup
  - [ ] Implement marker hover effects
  - [ ] Add marker clustering for dense areas
  - [ ] Size markers based on contact count
  - [ ] Sync map selection with list view

- [ ] Search and Filter Panel
  - [ ] Create `ContactFilters.tsx` component
  - [ ] Add specialty dropdown filter
  - [ ] Add provider practice group filter
  - [ ] Add city/region filter
  - [ ] Add text search for contact names
  - [ ] Implement real-time filtering

- [ ] Contact List Panel
  - [ ] Create `ContactList.tsx` component
  - [ ] Show filtered contacts in scrollable list
  - [ ] Highlight selected contact
  - [ ] Add "Center on Map" button for each contact
  - [ ] Show distance from map center

### Phase 6: User Experience Enhancements

- [ ] Performance Optimization
  - [ ] Implement viewport-based loading
  - [ ] Add loading states and skeletons
  - [ ] Optimize marker rendering for 3000+ points
  - [ ] Add request debouncing for filters

- [ ] Visual Enhancements
  - [ ] Create custom marker icons by specialty
  - [ ] Add marker animations on selection
  - [ ] Implement smooth pan/zoom to selected contacts
  - [ ] Add map legend for marker types

- [ ] Data Handling
  - [ ] Handle missing coordinates gracefully
  - [ ] Geocode addresses without lat/lng (if needed)
  - [ ] Show data quality indicators
  - [ ] Handle multiple contacts at same address

### Phase 7: Integration Features

- [ ] Activity Integration
  - [ ] Add "View on Map" button in activity details
  - [ ] Show activity count on contact markers
  - [ ] Add activity recency indicator

- [ ] Bundle Integration
  - [ ] Show bundle membership on markers
  - [ ] Filter by bundle assignment
  - [ ] Quick-add to bundle from map popup

### Phase 8: Advanced Features (Future)

- [ ] Heat Map View
  - [ ] Toggle between marker and density view
  - [ ] Show contact concentration by region
  - [ ] Customizable heat map parameters

- [ ] Territory Management
  - [ ] Draw custom territories on map
  - [ ] Assign contacts to territories
  - [ ] Territory-based filtering

- [ ] Route Planning
  - [ ] Multi-stop route optimization
  - [ ] Export routes to navigation apps
  - [ ] Save frequently used routes

## Technical Considerations

### Address Handling
- Use existing mailing address compound column from SF Contacts
- Fallback options if geocoding needed:
  1. Use lat/lng if available
  2. Geocode using address fields
  3. Show in list only if no coordinates

### Performance Strategy
- Initial load: Fetch only markers in viewport
- Use clustering for zoom levels < 12
- Lazy load full contact details
- Cache filter options client-side
- Implement virtual scrolling for contact list

### Mobile Experience
- Touch-friendly marker sizes
- Swipeable panels on mobile
- Simplified controls for small screens
- Progressive disclosure of information

### Data Privacy
- Ensure all data access follows existing permissions
- No PII in browser local storage
- Secure API endpoints with authentication

## Success Metrics
- Map loads in < 2 seconds
- Smooth interaction with 3000+ markers
- Intuitive navigation between map and list
- Quick access to contact information
- Effective filtering reduces markers to manageable sets

## Review Section

### Implementation Summary

Successfully implemented the Market Explorer feature with the following components:

#### Backend (FastAPI)
1. **Contact Schema Models** (`app/schemas/contact_schema.py`)
   - Created comprehensive Pydantic models for contact data
   - Includes models for map markers, list items, details, and filters

2. **Contact API Endpoints** (`app/api/contacts.py`)
   - `/api/contacts/map-data` - Optimized endpoint for map markers
   - `/api/contacts` - Paginated list endpoint with filtering
   - `/api/contacts/{contact_id}` - Detailed contact information
   - `/api/contacts/filter-options` - Dynamic filter options

3. **API Router Integration**
   - Added contact routes to main API router

#### Frontend (React + TypeScript)
1. **React Leaflet Integration**
   - Installed react-leaflet@4.2.1 (compatible with React 18)
   - Configured Leaflet CSS and icon fixes

2. **Map Components** (`frontend/src/components/ContactMap/`)
   - `ContactMap` - Main map container with viewport tracking
   - `ContactMapMarker` - Custom markers with size based on contact count
   - `ContactMapPopup` - Interactive popups with contact details
   - `MapControls` - Zoom controls and reset button

3. **Contact Management Components**
   - `ContactList` - Scrollable list with selection sync
   - `ContactFilters` - Comprehensive filter panel
   - `contactService` - API service layer with caching

4. **Contact Explorer Page**
   - Split-pane layout (filters | map | list)
   - Real-time filtering and search
   - Map-list synchronization
   - Responsive design

### Key Features Implemented
- ✅ Interactive map with contact locations
- ✅ Marker sizing based on contact density
- ✅ Search and filter functionality
- ✅ Geographic viewport-based loading
- ✅ Split-view interface
- ✅ Contact detail popups
- ✅ Navigation integration

### Performance Considerations
- Implemented client-side caching (5-minute TTL)
- Viewport-based map data loading
- Pagination for contact lists
- Optimized SQL queries with proper indexing

### Next Steps (Future Enhancements)
- Add marker clustering for dense areas (react-leaflet-cluster)
- Implement heat map visualization toggle
- Add export functionality for filtered contacts
- Integrate with activity data
- Add route planning features

The Market Explorer is now fully functional and ready for use!

---

This plan prioritizes user experience while maintaining technical simplicity and performance. React Leaflet is recommended for its balance of features, performance, and ease of implementation.