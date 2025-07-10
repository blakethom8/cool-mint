export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp?: string;
  tokens?: number;
}

export interface Conversation {
  id: string;
  bundle_id: string;
  model: string;
  messages: LLMMessage[];
  total_tokens_used: number;
  created_at: string;
  updated_at: string | null;
  message_count: number;
  saved_responses_count: number;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total_count: number;
}

export interface ConversationCreateRequest {
  bundle_id: string;
  model?: string;
  system_prompt?: string;
}

export interface MessageRequest {
  message: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface MessageResponse {
  message: string;
  tokens_used: number;
  total_tokens: number;
}

export interface SavedResponse {
  id: string;
  conversation_id: string;
  prompt: string;
  response: string;
  note: string | null;
  response_metadata: Record<string, any> | null;
  saved_at: string;
}

export interface SaveResponseRequest {
  conversation_id: string;
  prompt: string;
  response: string;
  note?: string;
  response_metadata?: Record<string, any>;
}

export interface SavedResponsesResponse {
  responses: SavedResponse[];
  total_count: number;
}

export interface PredefinedPrompt {
  id: string;
  category: string;
  title: string;
  prompt: string;
  description?: string;
  variables?: string[];
}