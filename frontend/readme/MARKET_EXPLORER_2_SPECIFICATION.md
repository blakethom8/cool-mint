# Market Explorer 2.0 - Product Specification & Implementation Plan

## Executive Summary
The Market Explorer 2.0 will be a comprehensive claims intelligence platform that enables physician liaisons to explore and analyze local healthcare markets through an interactive map interface. Unlike the current Salesforce-based contact explorer, this new system will leverage external claims data to provide deeper insights into healthcare utilization patterns, provider relationships, and market dynamics.

## Core Value Proposition
Enable physician liaisons to:
- Identify high-volume sites of service and provider groups
- Discover provider relationships and referral patterns
- Target outreach efforts based on actual claims volume
- Track and manage market intelligence with notes and classifications

## Data Architecture

### Three-Tier Data Model
1. **Providers** (Physicians)
   - Unique identifier: NPI (National Provider Identifier)
   - Attributes: Name, Specialty, Provider Group, Top Site of Service, Total Visits
   - Relationships: Many-to-many with Sites of Service through Visits

2. **Sites of Service** (Healthcare Facilities)
   - Unique identifier: Name + Address (to be replaced with generated IDs)
   - Attributes: Name, Type, Address, City, County, Zip, Latitude, Longitude, Geomarket
   - Relationships: Many-to-many with Providers through Visits

3. **Visits** (Fact Table)
   - Links Providers to Sites of Service
   - Attributes: Visit count, has_oncology, has_surgery, has_inpatient
   - Enables volume-based analysis

### CSV Data Structure Analysis
Based on the provided CSV files:

#### Providers.csv
- Lead_NPI: Provider identifier
- Lead_Name: Provider name
- Lead_Specialty: Provider specialty
- Lead_Top_Geomarket: Geographic market
- Lead_Provider_Group: Organization affiliation
- Lead_Specialty_Grandparent: High-level specialty category
- Lead_Service_Line: Service line category
- Lead_Top_Payer: Primary payer
- Lead_Top_Payer_Percent: Payer percentage
- Lead_Top_Referring_Org: Top referring organization
- Lead_Top_SoS: Primary site of service
- Lead_Top_Latitude/Longitude: Coordinates
- Lead_Top_SoS_Address: Site address
- Lead_Top_SoS_ID: Site identifier
- Lead_Total_Visits: Total visit count

#### SoS.csv
- SoS_ID: Site identifier
- SoS_Name: Site name
- SoS_City/County: Location
- SoS_Type: Facility type
- SoS_Zip: ZIP code
- SoS_Latitude/Longitude: Coordinates
- SoS_Geomarket: Market area

#### Visits.csv
- Lead_NPI: Provider identifier
- visit_has_oncology: Boolean flag
- visit_has_surgery: Boolean flag
- lead_has_inpatient: Boolean flag
- SoS_ID: Site identifier
- Visits: Visit count

## User Interface Design

### Map View (Center Panel)
- Interactive Leaflet map showing Sites of Service as markers
- Marker size based on total visit volume
- Color coding by facility type (Hospital, Clinic, Practice, Surgery Center, etc.)
- Clustering for dense areas
- Click markers to see basic info and select for detail view

### Right Panel - Three View Modes

#### 1. Sites of Service View (Default)
- List of sites visible in current map viewport
- Sortable by: Name, Visit Volume, Type, Distance from center
- Quick stats: Total visits, Number of providers
- Action buttons:
  - "View Details" - Opens detail window
  - "Add Note" - Quick note addition
  - "View on Map" - Centers map on site

#### 2. Provider Groups View
- Aggregated view of provider organizations
- Shows: Group name, Total providers, Total visits, Primary sites
- Sortable by volume and provider count
- Action buttons similar to Sites view

#### 3. Providers View
- Individual physician listing
- Shows: Name, Specialty, Group, Primary site, Visit volume
- Searchable and filterable
- Links to detailed provider view

### Detail Windows (Pop-out Design)
**Rationale for Pop-out Windows:**
- Allows simultaneous comparison of multiple sites/providers
- Preserves map context while diving into details
- Supports multi-monitor workflows
- Better for complex data exploration

**Site of Service Detail Window:**
- Header: Site name, type, address
- Tabs:
  - **Overview**: Visit statistics, charts, top specialties
  - **Providers**: List of all providers at site with visit volumes
  - **Notes**: Chronological notes with author and timestamp
  - **Intelligence**: AI-generated insights (future feature)

**Provider Group Detail Window:**
- Similar structure with group-specific information
- Cross-referenced sites and providers

**Provider Detail Window:**
- Individual provider information
- Sites where they practice
- Referral patterns (future feature)

### Filter System (Left Panel)

#### Geographic Filters
- Geomarket selection (dropdown)
- City/County selection
- Radius from point
- Draw custom area on map

#### Site Filters
- Facility type (multi-select)
- Minimum visit volume slider
- Has oncology/surgery/inpatient (checkboxes)

#### Provider Filters
- Specialty selection (hierarchical)
- Provider group
- Visit volume thresholds

#### Data Quality Filters
- Hide sites without coordinates
- Show only verified data
- Exclude outliers

## Core Features

### 1. Data Import & Management
- **Geocoding Service Integration**
  - Primary: Use existing lat/long from SoS.csv
  - Fallback: Integrate geocoding API for missing coordinates
  - Address standardization and validation

- **ID Generation System**
  - Create unique IDs for Sites of Service
  - Maintain mapping to legacy name+address identifiers
  - Support for data updates and merging

### 2. Search & Discovery
- **Smart Search**
  - Search across providers, sites, and groups
  - Fuzzy matching for names
  - Search by NPI, address, or specialty

- **Saved Searches**
  - Save complex filter combinations
  - Share searches with team members

### 3. Notes & Intelligence Management
- **Structured Notes System**
  - Note types: General, Relationship, Opportunity, Challenge
  - Attachable to Sites, Providers, or Groups
  - Timestamp and author tracking
  - Search within notes

- **Lead Classification**
  - Mark as: Hot Lead, Warm Lead, Cold Lead, Existing Relationship
  - Classification history tracking
  - Bulk classification tools

### 4. Analytics & Insights
- **Volume Analysis**
  - Trending over time (when historical data available)
  - Specialty mix analysis
  - Payer mix insights

- **Market Share Visualization**
  - Provider group market share by geography
  - Specialty dominance mapping

### 5. Export & Reporting
- **Export Formats**
  - CSV export of filtered data
  - PDF reports with maps and charts
  - Integration with CRM systems

- **Scheduled Reports**
  - Weekly territory summaries
  - New provider alerts
  - Volume change notifications

## Technical Implementation Strategy

### Backend Architecture
```
PostgreSQL Database:
- providers (from CSV import)
- sites_of_service (from CSV import)
- visits (from CSV import)
- notes (new table)
- user_classifications (new table)
- saved_filters (new table)
```

### API Design
```
/api/claims/
  /sites/
    GET / (list with filters)
    GET /{id} (detail)
    GET /map-markers (optimized for map)
    POST /{id}/notes
  /providers/
    GET / (list with filters)
    GET /{id} (detail)
  /provider-groups/
    GET / (aggregated view)
    GET /{id} (detail)
  /visits/
    GET /stats (aggregated statistics)
```

### Frontend Components
- Reuse existing ContactExplorer structure
- Adapt for three-entity model (Sites, Providers, Groups)
- Add tabbed interface for view switching
- Implement windowing system for detail views

## Performance Requirements
- Map loads < 2 seconds with 5000+ markers
- Smooth panning/zooming with marker clustering
- Sub-second filter response times
- Efficient viewport-based data loading

## Security & Privacy
- Role-based access control
- Audit trail for all data modifications
- No PII in browser storage
- Encrypted API communications

## Success Metrics
- User can identify top 10 sites by volume in < 30 seconds
- 80% of searches return relevant results
- Detail windows load in < 1 second
- Support 10+ simultaneous detail windows

## Future Enhancements
1. **Referral Network Visualization**
2. **Predictive Lead Scoring**
3. **Integration with Salesforce**
4. **Mobile Application**
5. **Real-time Claims Updates**

---

# Implementation Plan & Todo List

## Phase 1: Database & Data Pipeline (Priority: High)

### 1. ✅ Create comprehensive product specification for Market Explorer using claims data
**Status:** Completed

### 2. 🔄 Design and implement PostgreSQL database schema for claims data
**Status:** In Progress
- Create Alembic migration for new tables
- Add proper indexes for performance
- Implement foreign key relationships

### 3. ⏳ Create data import pipeline for CSV files to PostgreSQL
**Status:** Pending
- Handle UTF-8 BOM encoding in CSV files
- Validate data integrity and relationships
- Create import scripts with error handling

### 4. ⏳ Generate unique IDs for Sites of Service
**Status:** Pending
- Create UUID-based primary keys
- Maintain mapping to legacy identifiers
- Update data relationships

## Phase 2: Backend API Development (Priority: High)

### 5. ⏳ Implement backend API endpoints for sites, providers, and visits
**Status:** Pending
- Create FastAPI routes
- Implement filtering and pagination
- Add geographic bounding box queries

### 6. ⏳ Create Pydantic schemas for claims data models
**Status:** Pending
- Provider, SiteOfService, Visit models
- Request/response schemas
- Map marker optimization schemas

### 7. ⏳ Implement map marker aggregation for sites of service
**Status:** Pending
- Aggregate visit volumes by site
- Optimize for map viewport queries
- Add marker clustering logic

## Phase 3: Frontend Core Features (Priority: High)

### 8. ⏳ Adapt frontend ContactExplorer for claims data
**Status:** Pending
- Modify existing components
- Update service layer for claims API
- Adapt TypeScript interfaces

### 9. ⏳ Implement view toggle (Sites/Providers/Groups) in right panel
**Status:** Pending
- Create tabbed interface
- Implement view switching logic
- Add appropriate list components

## Phase 4: Detail Windows & Interactions (Priority: Medium)

### 10. ⏳ Create detail window pop-out functionality
**Status:** Pending
- Implement windowing system
- Create detail window components
- Handle multiple simultaneous windows

### 11. ⏳ Implement notes system with JSON storage
**Status:** Pending
- Add notes table to database
- Create notes API endpoints
- Build notes UI components

### 12. ⏳ Add provider and provider group list components
**Status:** Pending
- Create Provider list component
- Create ProviderGroup list component
- Implement sorting and filtering

## Phase 5: Advanced Features (Priority: Medium)

### 13. ⏳ Implement advanced filtering for claims data
**Status:** Pending
- Geographic filters
- Facility type filters
- Volume and specialty filters

### 14. ⏳ Create visit volume visualization on markers
**Status:** Pending
- Size markers by volume
- Color code by facility type
- Add hover tooltips

## Phase 6: Search & Intelligence (Priority: Low)

### 15. ⏳ Add search functionality across all entities
**Status:** Pending
- Cross-entity search
- Fuzzy matching
- Search history

### 16. ⏳ Implement lead classification system
**Status:** Pending
- Classification categories
- Bulk operations
- History tracking

### 17. ⏳ Add Google search and LLM summarization integration
**Status:** Pending
- External API integrations
- AI-powered insights
- Market intelligence summaries

## Phase 7: Export & Analytics (Priority: Low)

### 18. ⏳ Create export functionality for filtered data
**Status:** Pending
- CSV export
- PDF reports
- Scheduled exports

### 19. ⏳ Implement saved searches feature
**Status:** Pending
- Save filter combinations
- Share searches
- Search management

### 20. ⏳ Add performance optimizations for large datasets
**Status:** Pending
- Query optimization
- Caching strategies
- Loading performance

---

## Technical Approach
- **Incremental Development**: Start with core map and basic views, add features progressively
- **Reuse Existing Code**: Leverage current ContactExplorer components where possible
- **Performance First**: Implement efficient queries and caching from the start
- **User-Centric Design**: Focus on liaison workflow and ease of use

## Success Criteria
- Load 5000+ sites on map in < 2 seconds
- Support 10+ simultaneous detail windows
- Sub-second filter response times
- Intuitive navigation between map and detailed views