import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BundleList } from '../components/BundleList';
import { BundleDetail } from '../components/BundleDetail';
import { LLMChat } from '../components/LLMChat';
import { Bundle } from '../types/bundle';
import { Conversation, ConversationListResponse } from '../types/llm';
import { llmService } from '../services/llmService';
import './BundleManagement.css';

export const BundleManagement: React.FC = () => {
  const { bundleId } = useParams();
  const navigate = useNavigate();
  
  const [selectedBundle, setSelectedBundle] = useState<Bundle | null>(null);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showBundleDetail, setShowBundleDetail] = useState(true);

  // Load conversations when bundle is selected
  useEffect(() => {
    if (selectedBundle) {
      loadConversations(selectedBundle.id);
    } else {
      setConversations([]);
      setCurrentConversation(null);
    }
  }, [selectedBundle]);

  // Handle URL bundle ID
  useEffect(() => {
    if (bundleId && !selectedBundle) {
      // This would need to load the bundle from the API
      // For now, we'll just navigate to the base bundles page
      navigate('/bundles');
    }
  }, [bundleId, selectedBundle, navigate]);

  const loadConversations = async (bundleId: string) => {
    try {
      const response = await llmService.listConversations(bundleId);
      setConversations(response.conversations);
      
      // If there's an existing conversation, load the most recent one
      if (response.conversations.length > 0 && !currentConversation) {
        const latestConversation = response.conversations[0];
        setCurrentConversation(latestConversation);
        setShowBundleDetail(false);
      }
    } catch (err) {
      console.error('Error loading conversations:', err);
    }
  };

  const handleBundleSelect = (bundle: Bundle) => {
    setSelectedBundle(bundle);
    setShowBundleDetail(true);
    setCurrentConversation(null);
    setError(null);
    
    // Update URL
    navigate(`/bundles/${bundle.id}`);
  };

  const handleBundleDelete = (deletedBundleId: string) => {
    if (selectedBundle?.id === deletedBundleId) {
      setSelectedBundle(null);
      setCurrentConversation(null);
      setShowBundleDetail(true);
      navigate('/bundles');
    }
  };

  const handleStartConversation = async () => {
    if (!selectedBundle) return;

    setLoading(true);
    setError(null);
    
    try {
      const conversation = await llmService.createConversation(
        selectedBundle.id,
        'claude-3-5-sonnet-20241022'
      );
      
      setCurrentConversation(conversation);
      setConversations(prev => [conversation, ...prev]);
      setShowBundleDetail(false);
    } catch (err) {
      setError('Failed to start conversation');
      console.error('Error creating conversation:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConversationSelect = async (conversationId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const conversation = await llmService.getConversation(conversationId);
      setCurrentConversation(conversation);
      setShowBundleDetail(false);
    } catch (err) {
      setError('Failed to load conversation');
      console.error('Error loading conversation:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToBundleDetail = () => {
    setShowBundleDetail(true);
    setCurrentConversation(null);
  };

  return (
    <div className="bundle-management">
      <div className="bundle-sidebar">
        <BundleList
          selectedBundleId={selectedBundle?.id}
          onBundleSelect={handleBundleSelect}
          onBundleDelete={handleBundleDelete}
        />
      </div>

      <div className="bundle-main">
        {!selectedBundle ? (
          <div className="no-bundle-selected">
            <h2>Select a Bundle</h2>
            <p>Choose an activity bundle from the list to begin analysis</p>
          </div>
        ) : (
          <>
            {showBundleDetail ? (
              <>
                <BundleDetail
                  bundle={selectedBundle}
                  onStartConversation={handleStartConversation}
                />
                
                {conversations.length > 0 && (
                  <div className="existing-conversations">
                    <h3>Existing Conversations</h3>
                    <div className="conversation-list">
                      {conversations.map((conv) => (
                        <button
                          key={conv.id}
                          className="conversation-item"
                          onClick={() => handleConversationSelect(conv.id)}
                        >
                          <span className="conversation-date">
                            {new Date(conv.created_at).toLocaleDateString()}
                          </span>
                          <span className="conversation-messages">
                            {conv.message_count} messages
                          </span>
                          <span className="conversation-tokens">
                            {conv.total_tokens_used.toLocaleString()} tokens
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : currentConversation ? (
              <div className="conversation-view">
                <div className="conversation-header">
                  <button
                    className="back-button"
                    onClick={handleBackToBundleDetail}
                  >
                    ← Back to Bundle Details
                  </button>
                  <h2>{selectedBundle.name}</h2>
                </div>
                
                <LLMChat
                  conversation={currentConversation}
                  onMessageSent={async (response) => {
                    // Reload the full conversation to get updated messages
                    try {
                      const updatedConversation = await llmService.getConversation(currentConversation.id);
                      setCurrentConversation(updatedConversation);
                    } catch (err) {
                      console.error('Error refreshing conversation:', err);
                    }
                  }}
                />
              </div>
            ) : (
              <div className="loading-conversation">
                {loading ? 'Starting conversation...' : 'Loading...'}
              </div>
            )}
            
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};