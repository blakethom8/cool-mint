/**
 * TypeScript types for Relationship Management
 * 
 * These types mirror the backend Pydantic schemas to ensure
 * type safety across the full stack.
 */

// Base types
export interface RelationshipStatusInfo {
  id: number;
  code: string;
  display_name: string;
}

export interface LoyaltyStatusInfo {
  id: number;
  code: string;
  display_name: string;
  color_hex?: string;
}

export interface EntityTypeInfo {
  id: number;
  code: string;
  common_name: string;
}

// Entity details interface
export interface EntityDetails {
  name?: string;
  email?: string;
  phone?: string;
  specialty?: string;
  geography?: string;
  title?: string;
  account?: string;
  employment_status?: string;
  provider_group?: string;
  // Site of Service fields
  city?: string;
  state?: string;
  site_type?: string;
  site_specialty?: string;
  // Claims Provider fields
  npi?: string;
}

// List/Table types
export interface RelationshipListItem {
  relationship_id: string;
  user_id: number;
  user_name: string;
  entity_type: EntityTypeInfo;
  linked_entity_id: string;
  entity_name: string;
  entity_details: EntityDetails;
  relationship_status: RelationshipStatusInfo;
  loyalty_status?: LoyaltyStatusInfo;
  lead_score?: number;
  last_activity_date?: string;
  days_since_activity?: number;
  engagement_frequency?: string;
  activity_count: number;
  campaign_count: number;
  next_steps?: string;
  created_at: string;
  updated_at: string;
}

export interface RelationshipListResponse {
  items: RelationshipListItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Detail types
export interface ActivityLogItem {
  activity_id: string;
  activity_date: string;
  subject: string;
  description?: string;
  activity_type: string;
  mno_type?: string;
  mno_subtype?: string;
  status: string;
  owner_name: string;
  contact_names: string[];
}

export interface RelationshipMetrics {
  total_activities: number;
  activities_last_30_days: number;
  activities_last_90_days: number;
  average_days_between_activities?: number;
  most_common_activity_type?: string;
  last_activity_days_ago?: number;
  referral_count: number;
  meeting_count: number;
  call_count: number;
  email_count: number;
}

export interface CampaignInfo {
  campaign_id: string;
  campaign_name: string;
  status: string;
  start_date: string;
  end_date?: string;
}

export interface RelationshipDetail {
  relationship_id: string;
  user_id: number;
  user_name: string;
  user_email?: string;
  entity_type: EntityTypeInfo;
  linked_entity_id: string;
  entity_name: string;
  entity_details: EntityDetails;
  relationship_status: RelationshipStatusInfo;
  loyalty_status?: LoyaltyStatusInfo;
  lead_score?: number;
  last_activity_date?: string;
  next_steps?: string;
  engagement_frequency?: string;
  campaigns: CampaignInfo[];
  metrics?: RelationshipMetrics;
  recent_activities: ActivityLogItem[];
  created_at: string;
  updated_at: string;
}

// Filter types
export interface RelationshipFilters {
  user_ids?: number[];
  my_relationships_only?: boolean;
  entity_type_ids?: number[];
  entity_ids?: string[];
  relationship_status_ids?: number[];
  loyalty_status_ids?: number[];
  lead_scores?: number[];
  last_activity_after?: string;
  last_activity_before?: string;
  days_since_activity_min?: number;
  days_since_activity_max?: number;
  campaign_ids?: string[];
  search_text?: string;
  geographies?: string[];
  cities?: string[];
  specialties?: string[];
}

export interface FilterOption {
  id: string | number;
  name: string;
  count?: number;
}

export interface FilterOptionsResponse {
  users: Array<{
    id: number;
    name: string;
    relationship_count: number;
  }>;
  entity_types: EntityTypeInfo[];
  relationship_statuses: RelationshipStatusInfo[];
  loyalty_statuses: LoyaltyStatusInfo[];
  campaigns: Array<{
    id: string;
    name: string;
  }>;
  geographies: string[];
  specialties: string[];
}

// Update types
export interface RelationshipUpdate {
  relationship_status_id?: number;
  loyalty_status_id?: number;
  lead_score?: number;
  next_steps?: string;
  engagement_frequency?: string;
}

export interface BulkRelationshipUpdate {
  relationship_ids: string[];
  updates: RelationshipUpdate;
}

export interface RelationshipUpdateResponse {
  updated_count: number;
  relationships: RelationshipListItem[];
  message: string;
}

// Activity logging types
export interface ActivityLogCreate {
  activity_date: string;
  subject: string;
  description?: string;
  activity_type: string;
  status?: string;
}

export interface ActivityLogResponse {
  activity_id: string;
  relationship_id: string;
  message: string;
  updated_relationship: RelationshipListItem;
}

// Export types
export interface ExportRequest {
  filters?: RelationshipFilters;
  format: 'csv' | 'excel';
  include_activities?: boolean;
  include_metrics?: boolean;
}

// Create Relationship types
export interface CreateRelationshipRequest {
  user_id: number;
  entity_type_id: number;
  linked_entity_id: string;
  relationship_status_id: number;
  loyalty_status_id?: number;
  lead_score?: number;
  next_steps?: string;
  engagement_frequency?: string;
  notes?: {
    content: string;
    title?: string;
  };
}

export interface CreateRelationshipFromProvider {
  provider_id: string;
  user_id: number;
  relationship_status_id: number;
  loyalty_status_id?: number;
  lead_score?: number;
  next_steps?: string;
  note_content?: string;
}

// UI State types
export interface RelationshipTableState {
  selectedIds: Set<string>;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  page: number;
  pageSize: number;
}

export interface RelationshipManagerState {
  filters: RelationshipFilters;
  relationships: RelationshipListItem[];
  selectedRelationship?: RelationshipDetail;
  filterOptions?: FilterOptionsResponse;
  loading: boolean;
  error?: string;
  tableState: RelationshipTableState;
  rightPanelOpen: boolean;
}

// Constants
export const RELATIONSHIP_STATUS_COLORS: Record<string, string> = {
  'ESTABLISHED': '#28a745',
  'BUILDING': '#17a2b8',
  'PROSPECTING': '#ffc107',
  'DEPRIORITIZED': '#6c757d'
};

export const LEAD_SCORE_LABELS: Record<number, string> = {
  1: 'Very Low',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Very High'
};

export const ENGAGEMENT_FREQUENCY_OPTIONS = [
  'Weekly',
  'Monthly',
  'Quarterly',
  'Sporadic'
];

// Type guards
export function isRelationshipListItem(obj: any): obj is RelationshipListItem {
  return obj && 
    typeof obj.relationship_id === 'string' &&
    typeof obj.user_id === 'number' &&
    obj.entity_type && 
    typeof obj.entity_type.id === 'number';
}

export function isRelationshipDetail(obj: any): obj is RelationshipDetail {
  return obj &&
    isRelationshipListItem(obj) &&
    Array.isArray(obj.campaigns) &&
    Array.isArray(obj.recent_activities);
}