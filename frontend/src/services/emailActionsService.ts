import axios from 'axios';
import {
  EmailAction,
  EmailActionsListResponse,
  DashboardStats,
  ActionResultResponse,
  EmailActionFilters,
  EmailActionUpdateRequest
} from '../types/emailActions';

const API_BASE_URL = '/api/email-actions';

class EmailActionsService {
  /**
   * List email actions with filtering and pagination
   */
  async listEmailActions(
    page: number = 1,
    pageSize: number = 20,
    filters: EmailActionFilters = {},
    sortBy: string = 'created_at',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<EmailActionsListResponse> {
    const params: any = {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder
    };

    // Add filters to params
    if (filters.status) params.status = filters.status;
    if (filters.action_types?.length) params.action_types = filters.action_types;
    if (filters.user_email) params.user_email = filters.user_email;
    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;
    if (filters.search_text) params.search_text = filters.search_text;

    try {
      const response = await axios.get<EmailActionsListResponse>(API_BASE_URL, { params });
      console.log('[DEBUG] Raw API response:', response);
      return response.data;
    } catch (error) {
      console.error('[DEBUG] API call error:', error);
      throw error;
    }
  }

  /**
   * Get dashboard statistics
   */
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await axios.get<DashboardStats>(`${API_BASE_URL}/stats`);
    return response.data;
  }

  /**
   * Get detailed information about a specific email action
   */
  async getEmailAction(actionId: string): Promise<EmailAction> {
    const response = await axios.get<EmailAction>(`${API_BASE_URL}/${actionId}`);
    return response.data;
  }

  /**
   * Update an email action
   */
  async updateEmailAction(
    actionId: string,
    updates: EmailActionUpdateRequest
  ): Promise<EmailAction> {
    const response = await axios.patch<EmailAction>(
      `${API_BASE_URL}/${actionId}`,
      updates
    );
    return response.data;
  }

  /**
   * Approve an email action (placeholder)
   */
  async approveAction(actionId: string): Promise<ActionResultResponse> {
    const response = await axios.post<ActionResultResponse>(
      `${API_BASE_URL}/${actionId}/approve`
    );
    return response.data;
  }

  /**
   * Reject an email action (placeholder)
   */
  async rejectAction(actionId: string, reason?: string): Promise<ActionResultResponse> {
    const params = reason ? { reason } : undefined;
    const response = await axios.post<ActionResultResponse>(
      `${API_BASE_URL}/${actionId}/reject`,
      null,
      { params }
    );
    return response.data;
  }

  /**
   * Update staging data for an action
   */
  async updateStagingData(
    actionId: string,
    stagingUpdates: Record<string, any>
  ): Promise<EmailAction> {
    return this.updateEmailAction(actionId, { staging_updates: stagingUpdates });
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Format confidence score as percentage
   */
  formatConfidence(score: number): string {
    return `${Math.round(score * 100)}%`;
  }

  /**
   * Get action type color
   */
  getActionTypeColor(actionType: string): string {
    const colors: Record<string, string> = {
      add_note: '#17a2b8',
      log_call: '#28a745',
      set_reminder: '#ffc107'
    };
    return colors[actionType] || '#6c757d';
  }

  /**
   * Calculate time since action
   */
  getTimeSince(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 60) return `${diffMins} minutes ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  }
}

export default new EmailActionsService();