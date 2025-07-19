/**
 * Claims Data Service
 * Handles API calls to the claims endpoints
 */

import {
  ClaimsFilters,
  ClaimsProvidersResponse,
  SitesOfServiceResponse,
  ProviderGroupsResponse,
  MapMarkersResponse,
  FilterOptions,
  ClaimsProvider,
  SiteOfService,
  SiteStatistics,
  ProviderStatistics,
  ViewMode,
} from '../types/claims';

class ClaimsService {
  private baseUrl = '/api/claims';
  private cache = new Map<string, { data: any; timestamp: number }>();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes

  private getCacheKey(endpoint: string, params?: Record<string, any>): string {
    const paramsStr = params ? new URLSearchParams(params).toString() : '';
    return `${endpoint}?${paramsStr}`;
  }

  private getFromCache<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  private async fetchWithCache<T>(
    endpoint: string,
    params?: Record<string, any>
  ): Promise<T> {
    const cacheKey = this.getCacheKey(endpoint, params);
    const cached = this.getFromCache<T>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => url.searchParams.append(key, v.toString()));
          } else {
            url.searchParams.append(key, value.toString());
          }
        }
      });
    }

    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    this.setCache(cacheKey, data);
    return data;
  }

  async getProviders(
    page: number = 1,
    perPage: number = 50,
    filters?: ClaimsFilters
  ): Promise<ClaimsProvidersResponse> {
    const params = {
      page: page.toString(),
      per_page: perPage.toString(),
      ...this.filtersToParams(filters),
    };

    return this.fetchWithCache<ClaimsProvidersResponse>('/providers', params);
  }

  async getProvider(id: string): Promise<ClaimsProvider> {
    return this.fetchWithCache<ClaimsProvider>(`/providers/${id}`);
  }

  async getProviderStatistics(id: string): Promise<ProviderStatistics> {
    return this.fetchWithCache<ProviderStatistics>(`/providers/${id}/statistics`);
  }

  async getSites(
    page: number = 1,
    perPage: number = 50,
    filters?: ClaimsFilters
  ): Promise<SitesOfServiceResponse> {
    const params = {
      page: page.toString(),
      per_page: perPage.toString(),
      ...this.filtersToParams(filters),
    };

    return this.fetchWithCache<SitesOfServiceResponse>('/sites', params);
  }

  async getSite(id: string): Promise<SiteOfService> {
    return this.fetchWithCache<SiteOfService>(`/sites/${id}`);
  }

  async getSiteStatistics(id: string): Promise<SiteStatistics> {
    return this.fetchWithCache<SiteStatistics>(`/sites/${id}/statistics`);
  }

  async getProviderGroups(
    page: number = 1,
    perPage: number = 50,
    filters?: ClaimsFilters
  ): Promise<ProviderGroupsResponse> {
    const params = {
      page: page.toString(),
      per_page: perPage.toString(),
      ...this.filtersToParams(filters),
    };

    return this.fetchWithCache<ProviderGroupsResponse>('/provider-groups', params);
  }

  async getMapMarkers(filters?: ClaimsFilters): Promise<MapMarkersResponse> {
    const params = this.filtersToParams(filters);
    return this.fetchWithCache<MapMarkersResponse>('/map-markers', params);
  }

  async getFilterOptions(): Promise<FilterOptions> {
    return this.fetchWithCache<FilterOptions>('/filter-options');
  }

  async getSiteProviders(
    siteId: string,
    page: number = 1,
    perPage: number = 100
  ): Promise<ClaimsProvidersResponse> {
    const params = {
      page: page.toString(),
      per_page: perPage.toString(),
    };

    return this.fetchWithCache<ClaimsProvidersResponse>(`/sites/${siteId}/providers`, params);
  }

  async getSiteProviderGroups(
    siteId: string,
    page: number = 1,
    perPage: number = 100
  ): Promise<ProviderGroupsResponse> {
    const params = {
      page: page.toString(),
      per_page: perPage.toString(),
    };

    return this.fetchWithCache<ProviderGroupsResponse>(`/sites/${siteId}/provider-groups`, params);
  }

  async getSiteQuickView(siteId: string): Promise<SitesOfServiceResponse> {
    return this.fetchWithCache<SitesOfServiceResponse>(`/sites/${siteId}/site-details`);
  }

  private filtersToParams(filters?: ClaimsFilters): Record<string, any> {
    if (!filters) return {};

    const params: Record<string, any> = {};

    // Handle array filters
    if (filters.geomarket?.length) params.geomarket = filters.geomarket;
    if (filters.city?.length) params.city = filters.city;
    if (filters.county?.length) params.county = filters.county;
    if (filters.specialty?.length) params.specialty = filters.specialty;
    if (filters.provider_group?.length) params.provider_group = filters.provider_group;
    if (filters.site_type?.length) params.site_type = filters.site_type;

    // Handle numeric filters
    if (filters.north !== undefined) params.north = filters.north;
    if (filters.south !== undefined) params.south = filters.south;
    if (filters.east !== undefined) params.east = filters.east;
    if (filters.west !== undefined) params.west = filters.west;
    if (filters.min_visits !== undefined) params.min_visits = filters.min_visits;
    if (filters.max_visits !== undefined) params.max_visits = filters.max_visits;

    // Handle boolean filters
    if (filters.has_coordinates !== undefined) params.has_coordinates = filters.has_coordinates;
    if (filters.has_oncology !== undefined) params.has_oncology = filters.has_oncology;
    if (filters.has_surgery !== undefined) params.has_surgery = filters.has_surgery;
    if (filters.has_inpatient !== undefined) params.has_inpatient = filters.has_inpatient;

    // Handle search
    if (filters.search) params.search = filters.search;

    return params;
  }

  // Utility method to get data for a specific view mode
  async getDataForViewMode(
    viewMode: ViewMode,
    page: number = 1,
    perPage: number = 50,
    filters?: ClaimsFilters
  ): Promise<ClaimsProvidersResponse | SitesOfServiceResponse | ProviderGroupsResponse> {
    switch (viewMode) {
      case 'providers':
        return this.getProviders(page, perPage, filters);
      case 'sites':
        return this.getSites(page, perPage, filters);
      case 'groups':
        return this.getProviderGroups(page, perPage, filters);
      default:
        throw new Error(`Unknown view mode: ${viewMode}`);
    }
  }

  // Clear cache (useful for forced refresh)
  clearCache(): void {
    this.cache.clear();
  }

  // Clear specific cache entries
  clearCacheForEndpoint(endpoint: string): void {
    const keysToDelete = Array.from(this.cache.keys()).filter(key => 
      key.startsWith(`${endpoint}?`)
    );
    keysToDelete.forEach(key => this.cache.delete(key));
  }

  // Helper method to format numbers
  static formatNumber(num: number): string {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  // Helper method to format visit counts
  static formatVisits(visits: number): string {
    return `${this.formatNumber(visits)} visit${visits !== 1 ? 's' : ''}`;
  }

  // Helper method to get marker size based on visit count
  static getMarkerSize(visits: number, maxVisits: number = 50000): number {
    const minSize = 8;
    const maxSize = 24;
    const ratio = Math.min(visits / maxVisits, 1);
    return minSize + (maxSize - minSize) * ratio;
  }

  // Helper method to get color for site type
  static getSiteTypeColor(siteType?: string): string {
    const colors: Record<string, string> = {
      'Hospital': '#e74c3c',
      'Clinic': '#3498db',
      'Practice': '#2ecc71',
      'Surgery Center': '#f39c12',
      'Urgent Care': '#9b59b6',
      'Unknown Facility': '#95a5a6',
    };
    return colors[siteType || ''] || '#34495e';
  }
}

// Export singleton instance
const claimsService = new ClaimsService();
export default claimsService;