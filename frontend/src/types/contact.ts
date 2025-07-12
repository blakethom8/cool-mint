export interface ContactMapMarker {
  id: string;
  salesforce_id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  mailing_address: string | null;
  contact_count: number;
  specialty: string | null;
  organization: string | null;
}

export interface ContactListItem {
  id: string;
  salesforce_id: string;
  name: string;
  first_name: string | null;
  last_name: string;
  title: string | null;
  email: string | null;
  phone: string | null;
  specialty: string | null;
  organization: string | null;
  mailing_address: string | null;
  city: string | null;
  state: string | null;
  is_physician: boolean;
  active: boolean;
  last_activity_date: string | null;
}

export interface ContactDetail extends ContactListItem {
  middle_name: string | null;
  salutation: string | null;
  suffix: string | null;
  full_name: string | null;
  mobile_phone: string | null;
  fax: string | null;
  home_phone: string | null;
  other_phone: string | null;
  mailing_street: string | null;
  mailing_city: string | null;
  mailing_state: string | null;
  mailing_postal_code: string | null;
  mailing_country: string | null;
  mailing_latitude: number | null;
  mailing_longitude: number | null;
  mailing_address_compound: string | null;
  npi: string | null;
  days_since_last_visit: number | null;
  external_id: string | null;
  epic_id: string | null;
  geography: string | null;
  primary_geography: string | null;
  primary_mgma_specialty: string | null;
  network_picklist: string | null;
  panel_status: string | null;
}

export interface ContactFilterOptions {
  specialties: string[];
  organizations: string[];
  cities: string[];
  states: string[];
  geographies: string[];
  panel_statuses: string[];
}

export interface ContactFilters {
  search?: string;
  specialty?: string;
  organization?: string;
  city?: string;
  state?: string;
  geography?: string;
  is_physician?: boolean;
  active?: boolean;
  panel_status?: string;
  north?: number;
  south?: number;
  east?: number;
  west?: number;
}

export interface ContactListResponse {
  items: ContactListItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ContactMapResponse {
  markers: ContactMapMarker[];
  total: number;
  clustered: boolean;
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
}