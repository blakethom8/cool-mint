/**
 * Relationship Management Service
 * 
 * Handles all API interactions for relationship management features.
 */

import axios from 'axios';
import {
  RelationshipListResponse,
  RelationshipDetail,
  RelationshipFilters,
  RelationshipUpdate,
  BulkRelationshipUpdate,
  RelationshipUpdateResponse,
  ActivityLogCreate,
  ActivityLogResponse,
  FilterOptionsResponse,
  ExportRequest,
  ActivityLogItem,
  CreateRelationshipFromProvider
} from '../types/relationship';

// Base API configuration
const API_BASE_URL = '/api/relationships';

// Helper to convert filters to URL params
const buildFilterParams = (filters: RelationshipFilters): URLSearchParams => {
  const params = new URLSearchParams();
  
  // Add array parameters
  filters.user_ids?.forEach(id => params.append('user_ids', id.toString()));
  filters.entity_type_ids?.forEach(id => params.append('entity_type_ids', id.toString()));
  filters.entity_ids?.forEach(id => params.append('entity_ids', id));
  filters.relationship_status_ids?.forEach(id => params.append('relationship_status_ids', id.toString()));
  filters.loyalty_status_ids?.forEach(id => params.append('loyalty_status_ids', id.toString()));
  filters.lead_scores?.forEach(score => params.append('lead_scores', score.toString()));
  filters.campaign_ids?.forEach(id => params.append('campaign_ids', id));
  filters.geographies?.forEach(geo => params.append('geographies', geo));
  filters.cities?.forEach(city => params.append('cities', city));
  filters.specialties?.forEach(spec => params.append('specialties', spec));
  
  // Add single value parameters
  if (filters.my_relationships_only) params.append('my_relationships_only', 'true');
  if (filters.last_activity_after) params.append('last_activity_after', filters.last_activity_after);
  if (filters.last_activity_before) params.append('last_activity_before', filters.last_activity_before);
  if (filters.days_since_activity_min) params.append('days_since_activity_min', filters.days_since_activity_min.toString());
  if (filters.days_since_activity_max) params.append('days_since_activity_max', filters.days_since_activity_max.toString());
  if (filters.search_text) params.append('search_text', filters.search_text);
  
  return params;
};

class RelationshipService {
  /**
   * List relationships with filtering and pagination
   */
  async listRelationships(
    page: number = 1,
    pageSize: number = 50,
    sortBy: string = 'last_activity_date',
    sortOrder: 'asc' | 'desc' = 'desc',
    filters: RelationshipFilters = {}
  ): Promise<RelationshipListResponse> {
    const params = buildFilterParams(filters);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    params.append('sort_by', sortBy);
    params.append('sort_order', sortOrder);
    
    const response = await axios.get<RelationshipListResponse>(
      `${API_BASE_URL}/?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Get filter options for dropdowns
   */
  async getFilterOptions(): Promise<FilterOptionsResponse> {
    const response = await axios.get<FilterOptionsResponse>(
      `${API_BASE_URL}/filter-options`
    );
    return response.data;
  }

  /**
   * Get detailed information for a specific relationship
   */
  async getRelationshipDetail(relationshipId: string): Promise<RelationshipDetail> {
    const response = await axios.get<RelationshipDetail>(
      `${API_BASE_URL}/${relationshipId}`
    );
    return response.data;
  }

  /**
   * Update a relationship
   */
  async updateRelationship(
    relationshipId: string,
    updates: RelationshipUpdate
  ): Promise<RelationshipDetail> {
    const response = await axios.patch<RelationshipDetail>(
      `${API_BASE_URL}/${relationshipId}`,
      updates
    );
    return response.data;
  }

  /**
   * Bulk update multiple relationships
   */
  async bulkUpdateRelationships(
    bulkUpdate: BulkRelationshipUpdate
  ): Promise<RelationshipUpdateResponse> {
    const response = await axios.post<RelationshipUpdateResponse>(
      `${API_BASE_URL}/bulk-update`,
      bulkUpdate
    );
    return response.data;
  }

  /**
   * Get activities for a relationship
   */
  async getRelationshipActivities(
    relationshipId: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<{ activities: ActivityLogItem[]; total_count: number; page: number; page_size: number }> {
    const response = await axios.get(
      `${API_BASE_URL}/${relationshipId}/activities`,
      {
        params: { page, page_size: pageSize }
      }
    );
    return response.data;
  }

  /**
   * Log a new activity for a relationship
   */
  async logActivity(
    relationshipId: string,
    activity: ActivityLogCreate
  ): Promise<ActivityLogResponse> {
    const response = await axios.post<ActivityLogResponse>(
      `${API_BASE_URL}/${relationshipId}/activities`,
      activity
    );
    return response.data;
  }

  /**
   * Get metrics for a relationship
   */
  async getRelationshipMetrics(relationshipId: string): Promise<any> {
    const response = await axios.get(
      `${API_BASE_URL}/${relationshipId}/metrics`
    );
    return response.data;
  }

  /**
   * Export relationships data
   */
  async exportRelationships(exportRequest: ExportRequest): Promise<Blob> {
    const response = await axios.post(
      `${API_BASE_URL}/export`,
      exportRequest,
      {
        responseType: 'blob'
      }
    );
    return response.data;
  }

  /**
   * Quick update methods for common operations
   */
  async updateRelationshipStatus(
    relationshipId: string,
    statusId: number
  ): Promise<RelationshipDetail> {
    return this.updateRelationship(relationshipId, {
      relationship_status_id: statusId
    });
  }

  async updateLoyaltyStatus(
    relationshipId: string,
    loyaltyId: number
  ): Promise<RelationshipDetail> {
    return this.updateRelationship(relationshipId, {
      loyalty_status_id: loyaltyId
    });
  }

  async updateLeadScore(
    relationshipId: string,
    leadScore: number
  ): Promise<RelationshipDetail> {
    return this.updateRelationship(relationshipId, {
      lead_score: leadScore
    });
  }

  async updateNextSteps(
    relationshipId: string,
    nextSteps: string
  ): Promise<RelationshipDetail> {
    return this.updateRelationship(relationshipId, {
      next_steps: nextSteps
    });
  }

  /**
   * Create a relationship from a provider (Market Explorer integration)
   */
  async createRelationshipFromProvider(
    data: CreateRelationshipFromProvider
  ): Promise<RelationshipDetail> {
    const response = await axios.post<RelationshipDetail>(
      `${API_BASE_URL}/from-provider`,
      data
    );
    return response.data;
  }

  /**
   * Helper method to download export file
   */
  async downloadExport(
    filters: RelationshipFilters = {},
    format: 'csv' | 'excel' = 'csv',
    includeActivities: boolean = false,
    includeMetrics: boolean = true
  ): Promise<void> {
    const exportRequest: ExportRequest = {
      filters,
      format,
      include_activities: includeActivities,
      include_metrics: includeMetrics
    };

    const blob = await this.exportRelationships(exportRequest);
    
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `relationships_export_${new Date().toISOString().split('T')[0]}.${format === 'csv' ? 'csv' : 'xlsx'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

// Export singleton instance
export default new RelationshipService();