export interface ActivityListItem {
  id: number;
  activity_id: string;
  activity_date: string;
  subject: string;
  description: string | null;
  mno_type: string | null;
  mno_subtype: string | null;
  owner_name: string | null;
  owner_id: string | null;
  status: string | null;
  priority: string | null;
  type: string | null;
  contact_count: number;
  contact_names: string[];
  contact_specialties: string[];
  has_contact: boolean;
  has_md_contact: boolean;
  has_pharma_contact: boolean;
  has_other_contact: boolean;
}

export interface ActivityListResponse {
  activities: ActivityListItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ActivityFilters {
  owner_ids?: string[];
  start_date?: string;
  end_date?: string;
  search_text?: string;
  has_contact?: boolean;
  has_md_contact?: boolean;
  has_pharma_contact?: boolean;
  contact_specialties?: string[];
  mno_types?: string[];
  mno_subtypes?: string[];
  statuses?: string[];
  types?: string[];
}

export interface FilterOptions {
  owners: Array<{ id: string; name: string }>;
  contact_specialties: string[];
  mno_types: string[];
  mno_subtypes: string[];
  statuses: string[];
  types: string[];
}