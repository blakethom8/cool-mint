import {
  Email,
  EmailDetail,
  EmailsListResponse,
  SyncResponse,
  ProcessResponse,
  EmailFilters
} from '../types/emails';

const API_BASE = '/api/emails';

export const emailsApi = {
  // List emails with filters
  async listEmails(
    page: number = 1,
    pageSize: number = 20,
    filters?: EmailFilters
  ): Promise<EmailsListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });

    if (filters) {
      if (filters.search_text) params.append('search_text', filters.search_text);
      if (filters.from_email) params.append('from_email', filters.from_email);
      if (filters.processed !== undefined) params.append('processed', filters.processed.toString());
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.sort_by) params.append('sort_by', filters.sort_by);
      if (filters.sort_order) params.append('sort_order', filters.sort_order);
    }

    const response = await fetch(`${API_BASE}?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch emails');
    }
    return response.json();
  },

  // Get email detail
  async getEmailDetail(emailId: string): Promise<EmailDetail> {
    const response = await fetch(`${API_BASE}/${emailId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch email detail');
    }
    return response.json();
  },

  // Sync emails from Nylas
  async syncEmails(minutesBack: number = 30, limit: number = 50): Promise<SyncResponse> {
    const params = new URLSearchParams({
      minutes_back: minutesBack.toString(),
      limit: limit.toString()
    });

    const response = await fetch(`${API_BASE}/sync?${params}`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to sync emails');
    }
    return response.json();
  },

  // Process email with AI
  async processEmail(emailId: string): Promise<ProcessResponse> {
    const response = await fetch(`${API_BASE}/${emailId}/process`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to process email');
    }
    return response.json();
  },

  // Process multiple emails
  async processEmails(emailIds: string[]): Promise<ProcessResponse[]> {
    const promises = emailIds.map(id => this.processEmail(id));
    return Promise.all(promises);
  }
};