import axios from 'axios';
import { ActivityListResponse, ActivityFilters, FilterOptions } from '../types/activity';

const API_BASE = '/activities';

// No authentication needed for direct FastAPI connection during development

export const activityService = {
  async getActivities(
    page: number = 1,
    pageSize: number = 50,
    filters: ActivityFilters = {},
    sortBy: string = 'activity_date',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<ActivityListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    // Add filters to params
    if (filters.owner_ids?.length) {
      filters.owner_ids.forEach(id => params.append('owner_ids', id));
    }
    if (filters.start_date) {
      params.append('start_date', filters.start_date);
    }
    if (filters.end_date) {
      params.append('end_date', filters.end_date);
    }
    if (filters.search_text) {
      params.append('search_text', filters.search_text);
    }
    if (filters.has_contact !== undefined) {
      params.append('has_contact', filters.has_contact.toString());
    }
    if (filters.has_md_contact !== undefined) {
      params.append('has_md_contact', filters.has_md_contact.toString());
    }
    if (filters.has_pharma_contact !== undefined) {
      params.append('has_pharma_contact', filters.has_pharma_contact.toString());
    }
    if (filters.contact_specialties?.length) {
      filters.contact_specialties.forEach(spec => params.append('contact_specialties', spec));
    }
    if (filters.mno_types?.length) {
      filters.mno_types.forEach(type => params.append('mno_types', type));
    }
    if (filters.mno_subtypes?.length) {
      filters.mno_subtypes.forEach(subtype => params.append('mno_subtypes', subtype));
    }
    if (filters.statuses?.length) {
      filters.statuses.forEach(status => params.append('statuses', status));
    }
    if (filters.types?.length) {
      filters.types.forEach(type => params.append('types', type));
    }

    const response = await axios.get<ActivityListResponse>(`${API_BASE}?${params}`);
    return response.data;
  },

  async getFilterOptions(): Promise<FilterOptions> {
    const response = await axios.get<FilterOptions>(`${API_BASE}/filter-options`);
    return response.data;
  },

  async processSelection(activityIds: string[]): Promise<any> {
    const response = await axios.post(`${API_BASE}/selection`, {
      activity_ids: activityIds,
    });
    return response.data;
  },
};