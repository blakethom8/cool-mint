/**
 * TypeScript types for claims data API
 * These match the Pydantic schemas from the backend
 */

// Core entity types
export interface ClaimsProvider {
  id: string;
  npi: string;
  name: string;
  specialty: string;
  geomarket?: string;
  provider_group?: string;
  specialty_grandparent?: string;
  service_line?: string;
  top_payer?: string;
  top_payer_percent?: number;
  total_visits: number;
  top_referring_org?: string;
  top_sos_name?: string;
  top_sos_latitude?: number;
  top_sos_longitude?: number;
  top_sos_address?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ClaimsProviderListItem {
  id: string;
  npi: string;
  name: string;
  specialty: string;
  provider_group?: string;
  geomarket?: string;
  city?: string;
  total_visits: number;
  // Additional detail fields for expandable card
  top_site_name?: string;
  top_site_id?: string;
  top_payer?: string;
  top_payer_percent?: number;
  top_referring_org?: string;
}

export interface SiteOfService {
  id: string;
  legacy_id?: string;
  name: string;
  city?: string;
  county?: string;
  site_type?: string;
  zip_code?: string;
  latitude?: number;
  longitude?: number;
  geomarket?: string;
  address?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SiteOfServiceListItem {
  id: string;
  name: string;
  city?: string;
  site_type?: string;
  geomarket?: string;
  latitude?: number;
  longitude?: number;
  total_visits?: number;
  provider_count?: number;
}

export interface ClaimsVisit {
  id: string;
  provider_id: string;
  site_id: string;
  visits: number;
  has_oncology: boolean;
  has_surgery: boolean;
  has_inpatient: boolean;
  created_at?: string;
}

export interface ProviderGroup {
  name: string;
  provider_count: number;
  total_visits: number;
  specialties: string[];
  geomarkets: string[];
  top_sites: string[];
  site_count?: number;
}

// Map-related types
export interface MapMarker {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  total_visits: number;
  provider_count: number;
  site_type?: string;
  city?: string;
  geomarket?: string;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface MapMarkersResponse {
  markers: MapMarker[];
  total_count: number;
  bounds?: MapBounds;
}

// Filter types
export interface ClaimsFilters {
  // Geographic filters
  geomarket?: string[];
  city?: string[];
  county?: string[];
  north?: number;
  south?: number;
  east?: number;
  west?: number;
  
  // Provider filters
  specialty?: string[];
  service_line?: string[];
  provider_group?: string[];
  min_provider_visits?: number;
  
  // Provider group filters
  min_group_visits?: number;
  min_group_sites?: number;
  
  // Site filters
  site_type?: string[];
  min_site_visits?: number;
  min_providers?: number;
  has_coordinates?: boolean;
  
  // Service filters
  has_oncology?: boolean;
  has_surgery?: boolean;
  has_inpatient?: boolean;
  
  // Search
  search?: string;
  
  // Legacy (for backwards compatibility)
  min_visits?: number;
  max_visits?: number;
}

export interface FilterOptions {
  geomarkets: string[];
  cities: string[];
  counties: string[];
  specialties: string[];
  provider_groups: string[];
  site_types: string[];
  specialty_grandparents: string[];
  service_lines: string[];
}

// Pagination types
export interface PaginationMeta {
  page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ClaimsProvidersResponse {
  items: ClaimsProviderListItem[];
  meta: PaginationMeta;
  statistics: ClaimsStatistics;
}

export interface SitesOfServiceResponse {
  items: SiteOfServiceListItem[];
  meta: PaginationMeta;
  statistics: ClaimsStatistics;
}

export interface ProviderGroupsResponse {
  items: ProviderGroup[];
  meta: PaginationMeta;
  statistics: ClaimsStatistics;
}

// Statistics types
export interface VisitStatistics {
  total_visits: number;
  oncology_visits: number;
  surgery_visits: number;
  inpatient_visits: number;
  outpatient_visits: number;
}

export interface SiteStatistics {
  site_id: string;
  visit_stats: VisitStatistics;
  provider_count: number;
  top_specialties: Array<{specialty: string; visits: number}>;
  top_providers: Array<{name: string; specialty: string; visits: number}>;
}

export interface ProviderStatistics {
  provider_id: string;
  visit_stats: VisitStatistics;
  site_count: number;
  top_sites: Array<{name: string; city?: string; visits: number}>;
}

export interface ClaimsStatistics {
  total_visits: number;
  total_providers: number;
  total_sites: number;
  average_visits_per_site: number;
  average_visits_per_provider: number;
}

// View modes for the right panel
export type ViewMode = 'sites' | 'providers' | 'groups';

// Sort options
export interface SortOption {
  field: string;
  direction: 'asc' | 'desc';
  label: string;
}

export const SORT_OPTIONS: Record<ViewMode, SortOption[]> = {
  sites: [
    { field: 'total_visits', direction: 'desc', label: 'Most Visits' },
    { field: 'total_visits', direction: 'asc', label: 'Least Visits' },
    { field: 'name', direction: 'asc', label: 'Name A-Z' },
    { field: 'name', direction: 'desc', label: 'Name Z-A' },
    { field: 'provider_count', direction: 'desc', label: 'Most Providers' },
    { field: 'city', direction: 'asc', label: 'City A-Z' },
  ],
  providers: [
    { field: 'total_visits', direction: 'desc', label: 'Most Visits' },
    { field: 'total_visits', direction: 'asc', label: 'Least Visits' },
    { field: 'name', direction: 'asc', label: 'Name A-Z' },
    { field: 'name', direction: 'desc', label: 'Name Z-A' },
    { field: 'specialty', direction: 'asc', label: 'Specialty A-Z' },
  ],
  groups: [
    { field: 'total_visits', direction: 'desc', label: 'Most Visits' },
    { field: 'provider_count', direction: 'desc', label: 'Most Providers' },
    { field: 'name', direction: 'asc', label: 'Name A-Z' },
    { field: 'name', direction: 'desc', label: 'Name Z-A' },
  ],
};

// Color scheme for different site types
export const SITE_TYPE_COLORS: Record<string, string> = {
  'Hospital': '#e74c3c',
  'Clinic': '#3498db', 
  'Practice': '#2ecc71',
  'Surgery Center': '#f39c12',
  'Urgent Care': '#9b59b6',
  'Unknown Facility': '#95a5a6',
  default: '#34495e',
};

// Service type icons/colors
export const SERVICE_INDICATORS = {
  oncology: { color: '#e74c3c', label: 'Oncology' },
  surgery: { color: '#f39c12', label: 'Surgery' },
  inpatient: { color: '#3498db', label: 'Inpatient' },
};