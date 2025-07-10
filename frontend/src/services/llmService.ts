import axios from 'axios';
import {
  LLMMessage,
  Conversation,
  ConversationListResponse,
  MessageResponse,
  SavedResponse,
  SavedResponsesResponse
} from '../types/llm';

const API_BASE_URL = '';

export const llmService = {
  // Create a new conversation
  async createConversation(
    bundleId: string,
    model: string = 'claude-3-5-sonnet-20241022',
    systemPrompt?: string
  ): Promise<Conversation> {
    const response = await axios.post(`/api/llm/conversations`, {
      bundle_id: bundleId,
      model,
      system_prompt: systemPrompt,
    });
    return response.data;
  },

  // List conversations
  async listConversations(bundleId?: string): Promise<ConversationListResponse> {
    const params = bundleId ? `?bundle_id=${bundleId}` : '';
    const response = await axios.get(`/api/llm/conversations${params}`);
    return response.data;
  },

  // Get conversation details
  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await axios.get(`/api/llm/conversations/${conversationId}`);
    return response.data;
  },

  // Send a message to the LLM
  async sendMessage(
    conversationId: string,
    message: string,
    model?: string,
    temperature?: number,
    maxTokens?: number
  ): Promise<MessageResponse> {
    const response = await axios.post(
      `/api/llm/conversations/${conversationId}/messages`,
      {
        message,
        model,
        temperature,
        max_tokens: maxTokens,
      }
    );
    return response.data;
  },

  // Save a response
  async saveResponse(
    conversationId: string,
    prompt: string,
    response: string,
    note?: string,
    metadata?: Record<string, any>
  ): Promise<SavedResponse> {
    const res = await axios.post(`/api/llm/responses/save`, {
      conversation_id: conversationId,
      prompt,
      response,
      note,
      response_metadata: metadata,
    });
    return res.data;
  },

  // List saved responses
  async listSavedResponses(
    conversationId?: string,
    bundleId?: string
  ): Promise<SavedResponsesResponse> {
    const params = new URLSearchParams();
    if (conversationId) params.append('conversation_id', conversationId);
    if (bundleId) params.append('bundle_id', bundleId);

    const response = await axios.get(
      `/api/llm/responses/saved?${params}`
    );
    return response.data;
  },
};