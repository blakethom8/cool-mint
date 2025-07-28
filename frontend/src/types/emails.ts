export interface Email {
  id: string;
  nylas_id: string;
  subject: string;
  snippet: string | null;
  from_email: string | null;
  from_name: string | null;
  to_emails: string[] | null;
  date: string | null;
  unread: boolean;
  has_attachments: boolean;
  processed: boolean;
  processing_status: string | null;
  classification: string | null;
  is_forwarded: boolean;
  user_instruction: string | null;
  created_at: string;
  body_preview: string | null;
}

export interface EmailDetail extends Email {
  grant_id: string;
  thread_id: string;
  cc_emails: string[] | null;
  bcc_emails: string[] | null;
  body: string | null;
  body_plain: string | null;
  starred: boolean;
  attachments_count: number;
  extracted_thread: string | null;
  folders: string[] | null;
  labels: string[] | null;
  updated_at: string;
}

export interface EmailsListResponse {
  items: Email[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SyncResponse {
  success: boolean;
  message: string;
  total_fetched: number;
  new_emails: number;
  updated_emails: number;
  sync_mode: string;
  sync_time: string;
}

export interface ProcessResponse {
  success: boolean;
  message: string;
  email_id: string;
  workflow_triggered: boolean;
}

export interface EmailFilters {
  search_text?: string;
  from_email?: string;
  processed?: boolean;
  start_date?: string;
  end_date?: string;
  sort_by?: 'date' | 'subject' | 'from_email';
  sort_order?: 'asc' | 'desc';
}