export interface Bundle {
  id: string;
  name: string;
  description: string | null;
  activity_ids: string[];
  activity_count: number;
  token_count: number | null;
  created_by: string | null;
  created_at: string;
  updated_at: string | null;
  conversation_count: number;
}

export interface BundleListResponse {
  bundles: Bundle[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BundleDetailResponse {
  bundle: Bundle;
  activities: ActivityDetail[];
  total_tokens: number;
}

export interface ActivityDetail {
  activity_id: string;
  subject: string;
  description: string;
  activity_date: string | null;
  owner_name: string;
  mno_type: string;
  mno_subtype: string;
  contact_count: number;
  contact_names: string[];
  llm_context: any;
}

export interface BundleStatsResponse {
  activity_count: number;
  total_characters: number;
  estimated_tokens: number;
  unique_owners: string[];
  date_range: {
    start: string | null;
    end: string | null;
  };
  activity_types: Record<string, number>;
}

export interface ActivitySelectionResponse {
  selected_count: number;
  activity_ids: string[];
  llm_contexts: any[];
  estimated_tokens: number;
  bundle_id: string | null;
  message: string;
}

export interface BundleDeleteResponse {
  success: boolean;
  message: string;
}