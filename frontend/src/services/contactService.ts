import axios from 'axios';
import {
  ContactMapResponse,
  ContactListResponse,
  ContactDetail,
  ContactFilterOptions,
  ContactFilters,
} from '../types/contact';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

class ContactService {
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes

  private getCached<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data as T;
    }
    return null;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  async getMapData(filters?: ContactFilters): Promise<ContactMapResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters) {
        if (filters.north) params.append('north', filters.north.toString());
        if (filters.south) params.append('south', filters.south.toString());
        if (filters.east) params.append('east', filters.east.toString());
        if (filters.west) params.append('west', filters.west.toString());
        if (filters.specialty) params.append('specialty', filters.specialty);
        if (filters.organization) params.append('organization', filters.organization);
        if (filters.city) params.append('city', filters.city);
        if (filters.state) params.append('state', filters.state);
        if (filters.is_physician !== undefined) params.append('is_physician', filters.is_physician.toString());
        if (filters.active !== undefined) params.append('active', filters.active.toString());
        if (filters.search) params.append('search', filters.search);
      }

      const cacheKey = `map-data-${params.toString()}`;
      const cached = this.getCached<ContactMapResponse>(cacheKey);
      if (cached) return cached;

      const response = await axios.get<ContactMapResponse>(
        `${API_BASE_URL}/api/contacts/map-data`,
        { params }
      );

      this.setCache(cacheKey, response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching map data:', error);
      throw error;
    }
  }

  async getContacts(
    page: number = 1,
    pageSize: number = 50,
    filters?: ContactFilters,
    sortBy: string = 'name',
    sortOrder: 'asc' | 'desc' = 'asc'
  ): Promise<ContactListResponse> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      if (filters) {
        if (filters.search) params.append('search', filters.search);
        if (filters.specialty) params.append('specialty', filters.specialty);
        if (filters.organization) params.append('organization', filters.organization);
        if (filters.city) params.append('city', filters.city);
        if (filters.state) params.append('state', filters.state);
        if (filters.geography) params.append('geography', filters.geography);
        if (filters.is_physician !== undefined) params.append('is_physician', filters.is_physician.toString());
        if (filters.active !== undefined) params.append('active', filters.active.toString());
        if (filters.panel_status) params.append('panel_status', filters.panel_status);
      }

      const response = await axios.get<ContactListResponse>(
        `${API_BASE_URL}/api/contacts`,
        { params }
      );

      return response.data;
    } catch (error) {
      console.error('Error fetching contacts:', error);
      throw error;
    }
  }

  async getContactDetail(contactId: string): Promise<ContactDetail> {
    try {
      const cacheKey = `contact-detail-${contactId}`;
      const cached = this.getCached<ContactDetail>(cacheKey);
      if (cached) return cached;

      const response = await axios.get<ContactDetail>(
        `${API_BASE_URL}/api/contacts/${contactId}`
      );

      this.setCache(cacheKey, response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching contact detail:', error);
      throw error;
    }
  }

  async getFilterOptions(): Promise<ContactFilterOptions> {
    try {
      const cacheKey = 'contact-filter-options';
      const cached = this.getCached<ContactFilterOptions>(cacheKey);
      if (cached) return cached;

      const response = await axios.get<ContactFilterOptions>(
        `${API_BASE_URL}/api/contacts/filter-options`
      );

      this.setCache(cacheKey, response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching filter options:', error);
      throw error;
    }
  }

  clearCache(): void {
    this.cache.clear();
  }
}

export default new ContactService();