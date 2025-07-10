import React, { useState, useEffect, useRef } from 'react';
import { Conversation, LLMMessage, MessageResponse } from '../types/llm';
import { llmService } from '../services/llmService';
import './LLMChat.css';

interface LLMChatProps {
  conversation: Conversation;
  onMessageSent?: (message: MessageResponse) => void;
  onResponseSaved?: (responseId: string) => void;
}

export const LLMChat: React.FC<LLMChatProps> = ({
  conversation,
  onMessageSent,
  onResponseSaved,
}) => {
  const [messages, setMessages] = useState<LLMMessage[]>(conversation.messages);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(conversation.messages);
  }, [conversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || loading) {
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setLoading(true);
    setError(null);

    // Add user message to UI immediately
    const newUserMessage: LLMMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await llmService.sendMessage(
        conversation.id,
        userMessage,
        conversation.model
      );

      // Reload the conversation to get the updated messages from the database
      const updatedConversation = await llmService.getConversation(conversation.id);
      setMessages(updatedConversation.messages);

      if (onMessageSent) {
        onMessageSent(response);
      }
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Error sending message:', err);
      // Remove the user message on error
      setMessages(prev => prev.slice(0, -1));
      setInputMessage(userMessage); // Restore the input
    } finally {
      setLoading(false);
    }
  };

  const handleSaveResponse = async (prompt: string, response: string) => {
    try {
      const savedResponse = await llmService.saveResponse(
        conversation.id,
        prompt,
        response,
        `Saved from conversation on ${new Date().toLocaleDateString()}`
      );
      
      if (onResponseSaved) {
        onResponseSaved(savedResponse.id);
      }
      
      // Show success feedback
      alert('Response saved successfully!');
    } catch (err) {
      console.error('Error saving response:', err);
      alert('Failed to save response');
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content).then(() => {
      // Could add a toast notification here
      alert('Message copied to clipboard!');
    });
  };

  const renderMessage = (message: LLMMessage, index: number) => {
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';
    const previousMessage = index > 0 ? messages[index - 1] : null;

    return (
      <div key={index} className={`message-wrapper ${message.role}`}>
        <div className={`message ${message.role}`}>
          <div className="message-header">
            <span className="message-role">
              {message.role === 'system' ? '🔧 System' : 
               message.role === 'user' ? '👤 You' : '🤖 Assistant'}
            </span>
            <span className="message-timestamp">
              {formatTimestamp(message.timestamp)}
            </span>
            {message.tokens && (
              <span className="message-tokens">
                {message.tokens} tokens
              </span>
            )}
          </div>
          
          <div className="message-content">
            {message.content}
          </div>
          
          <div className="message-actions">
            <button
              className="message-action-btn"
              onClick={() => handleCopyMessage(message.content)}
              title="Copy message"
            >
              📋 Copy
            </button>
            
            {isAssistant && previousMessage?.role === 'user' && (
              <button
                className="message-action-btn"
                onClick={() => handleSaveResponse(previousMessage.content, message.content)}
                title="Save this response"
              >
                💾 Save
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="llm-chat">
      <div className="chat-header">
        <h3>Conversation</h3>
        <div className="chat-info">
          <span className="chat-model">Model: {conversation.model}</span>
          <span className="chat-tokens">Total tokens: {conversation.total_tokens_used.toLocaleString()}</span>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 1 ? (
          <div className="chat-welcome">
            <h4>Welcome! 👋</h4>
            <p>Start by asking a question about the activities in this bundle.</p>
            <p>The AI has access to all activity data including contacts, dates, descriptions, and structured context.</p>
            
            <div className="suggested-prompts">
              <h5>Try asking:</h5>
              <button onClick={() => setInputMessage("Summarize the key themes and patterns across all activities")}>
                Summarize key themes
              </button>
              <button onClick={() => setInputMessage("What are the most successful outcomes mentioned in these activities?")}>
                Find success stories
              </button>
              <button onClick={() => setInputMessage("Which contacts appear most frequently and in what context?")}>
                Analyze contacts
              </button>
              <button onClick={() => setInputMessage("What geographic patterns do you see in the activities?")}>
                Geographic insights
              </button>
            </div>
          </div>
        ) : (
          messages.map((message, index) => renderMessage(message, index))
        )}
        
        {loading && (
          <div className="message-wrapper assistant">
            <div className="message assistant loading">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        {error && (
          <div className="chat-error">
            {error}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(e);
              }
            }}
            placeholder="Ask a question about the activities..."
            rows={3}
            disabled={loading}
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={!inputMessage.trim() || loading}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
        <div className="chat-input-hint">
          Press Enter to send, Shift+Enter for new line
        </div>
      </form>
    </div>
  );
};