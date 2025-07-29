// Email Action Types
export interface EmailAction {
  id: string;
  email_id: string;
  action_type: 'add_note' | 'log_call' | 'set_reminder';
  action_parameters: Record<string, any>;
  confidence_score: number;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed' | 'failed';
  reviewed_at?: string;
  reviewed_by?: string;
  review_notes?: string;
  created_at: string;
  updated_at: string;
  email: EmailSummary;
  staging_data?: StagingData;
}

export interface EmailSummary {
  id?: string;
  subject: string;
  from_email: string;
  to_email?: string;
  date?: string;
  content?: string;
  parsed_content?: string;
  user_instruction?: string;
  is_forwarded?: boolean;
}

// Staging Data Types
export type StagingData = CallLogStaging | NoteStaging | ReminderStaging;

export interface CallLogStaging {
  type: 'call_log';
  id: string;
  subject: string;
  description?: string;
  activity_date?: string;
  duration_minutes?: number;
  mno_type?: string;
  mno_subtype?: string;
  mno_setting?: string;
  contact_ids?: string[];
  primary_contact_id?: string;
  approval_status: string;
}

export interface NoteStaging {
  type: 'note';
  id: string;
  note_content: string;
  note_type?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  related_entity_name?: string;
  approval_status: string;
}

export interface ReminderStaging {
  type: 'reminder';
  id: string;
  reminder_text: string;
  due_date: string;
  priority: 'high' | 'normal' | 'low';
  assignee?: string;
  assignee_id?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  related_entity_name?: string;
  approval_status: string;
}

// API Response Types
export interface EmailActionsListResponse {
  items: EmailAction[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DashboardStats {
  total_actions: number;
  pending_actions: number;
  approved_actions: number;
  rejected_actions: number;
  completed_actions: number;
  action_type_breakdown: {
    add_note: number;
    log_call: number;
    set_reminder: number;
  };
  recent_actions_7_days: number;
  average_confidence_score: number;
  last_updated: string;
}

export interface ActionResultResponse {
  success: boolean;
  message: string;
  action_id: string;
}

// Filter Types
export interface EmailActionFilters {
  status?: string;
  action_types?: string[];
  user_email?: string;
  start_date?: string;
  end_date?: string;
  search_text?: string;
}

// Update Request Types
export interface EmailActionUpdateRequest {
  status?: string;
  review_notes?: string;
  staging_updates?: Record<string, any>;
}

// Transfer API Types
export interface TransferRequest {
  user_id: string;
  final_values: Record<string, any>;
  additional_data?: Record<string, any>;
}

export interface TransferResponse {
  success: boolean;
  message: string;
  activity_id?: string;
  note_id?: string;
  reminder_id?: string;
  staging_id: string;
  transfer_details?: {
    delta_fields?: Record<string, any>;
    original_values?: Record<string, any>;
  };
}

// Component State Types
export interface JunoAssistantState {
  actions: EmailAction[];
  selectedAction?: EmailAction;
  filters: EmailActionFilters;
  loading: boolean;
  error?: string;
  stats?: DashboardStats;
  activeTab: 'emails' | 'pending' | 'completed';
  page: number;
  pageSize: number;
  totalPages: number;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

// Helper type guards
export function isCallLogStaging(data: StagingData): data is CallLogStaging {
  return data.type === 'call_log';
}

export function isNoteStaging(data: StagingData): data is NoteStaging {
  return data.type === 'note';
}

export function isReminderStaging(data: StagingData): data is ReminderStaging {
  return data.type === 'reminder';
}

// Display helpers
export const ACTION_TYPE_LABELS: Record<string, string> = {
  add_note: 'Add Note',
  log_call: 'Log Call',
  set_reminder: 'Set Reminder'
};

export const ACTION_TYPE_ICONS: Record<string, string> = {
  add_note: '📝',
  log_call: '📞',
  set_reminder: '⏰'
};

export const STATUS_COLORS: Record<string, string> = {
  pending: '#ffa500',
  approved: '#28a745',
  rejected: '#dc3545',
  completed: '#007bff',
  failed: '#6c757d'
};

export const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending Review',
  approved: 'Approved',
  rejected: 'Rejected',
  completed: 'Completed',
  failed: 'Failed'
};