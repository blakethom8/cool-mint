import React, { useState, useEffect, useCallback } from 'react';
import {
  JunoAssistantState,
  EmailAction,
  EmailActionFilters,
  DashboardStats
} from '../types/emailActions';
import { Email, EmailFilters } from '../types/emails';
import emailActionsService from '../services/emailActionsService';
import { emailsApi } from '../services/emailsApi';
import JunoHeader from '../components/JunoHeader';
import EmailActionsList from '../components/EmailActionsList';
import EmailActionDetailModal from '../components/EmailActionDetailModal';
import EmailActionFiltersComponent from '../components/EmailActionFilters';
import EmailsList from '../components/EmailsList';
import { useNotification } from '../contexts/NotificationContext';
import './JunoAssistant.css';

const JunoAssistant: React.FC = () => {
  const { showSuccess, showError, showInfo } = useNotification();
  
  const [state, setState] = useState<JunoAssistantState>({
    actions: [],
    selectedAction: undefined,
    filters: {},
    loading: false,
    error: undefined,
    stats: undefined,
    activeTab: 'pending' as 'emails' | 'pending' | 'completed',
    page: 1,
    pageSize: 20,
    totalPages: 1,
    sortBy: 'created_at',
    sortOrder: 'desc'
  });

  const [showFilters, setShowFilters] = useState(true);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [emails, setEmails] = useState<Email[]>([]);
  const [emailsLoading, setEmailsLoading] = useState(false);
  const [emailFilters, setEmailFilters] = useState<EmailFilters>({});
  const [selectedEmails, setSelectedEmails] = useState<string[]>([]);
  const [processingEmails, setProcessingEmails] = useState<string[]>([]);

  // Load dashboard stats on mount
  useEffect(() => {
    loadDashboardStats();
  }, []);

  // Load actions when filters, tab, or pagination changes
  useEffect(() => {
    if (state.activeTab === 'emails') {
      loadEmails();
    } else {
      loadActions();
    }
  }, [state.filters, state.activeTab, state.page, state.pageSize, state.sortBy, state.sortOrder, emailFilters]);

  const loadDashboardStats = async () => {
    try {
      const stats = await emailActionsService.getDashboardStats();
      setState(prev => ({ ...prev, stats }));
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    }
  };

  const loadActions = async () => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));

    try {
      // Add status filter based on active tab
      const filters: EmailActionFilters = {
        ...state.filters,
        status: state.activeTab === 'pending' ? 'pending' : undefined
      };

      // If completed tab, filter for non-pending statuses
      if (state.activeTab === 'completed') {
        filters.status = undefined; // We'll handle this server-side with multiple statuses
      }

      const response = await emailActionsService.listEmailActions(
        state.page,
        state.pageSize,
        filters,
        state.sortBy,
        state.sortOrder
      );

      console.log('[DEBUG] API Response:', response);

      // Filter based on tab if needed
      let filteredActions = response.items || [];
      if (state.activeTab === 'completed') {
        filteredActions = filteredActions.filter(
          action => action.status !== 'pending'
        );
      }

      setState(prev => ({
        ...prev,
        actions: filteredActions,
        totalPages: response.total_pages || 1,
        loading: false
      }));
    } catch (error) {
      console.error('Failed to load actions:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load email actions. Please try again.'
      }));
    }
  };

  const handleFilterChange = useCallback((newFilters: EmailActionFilters) => {
    setState(prev => ({
      ...prev,
      filters: newFilters,
      page: 1 // Reset to first page when filters change
    }));
  }, []);

  const handleActionSelect = useCallback(async (action: EmailAction) => {
    setState(prev => ({ ...prev, loading: true }));
    
    try {
      // Get full action details
      const fullAction = await emailActionsService.getEmailAction(action.id);
      setState(prev => ({
        ...prev,
        selectedAction: fullAction,
        loading: false
      }));
      setShowDetailModal(true);
    } catch (error) {
      console.error('Failed to load action details:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load action details.'
      }));
    }
  }, []);

  const handleActionUpdate = useCallback(async (actionId: string, updates: any) => {
    try {
      const updatedAction = await emailActionsService.updateEmailAction(actionId, updates);
      
      // Update action in list
      setState(prev => ({
        ...prev,
        actions: prev.actions.map(a => a.id === actionId ? updatedAction : a),
        selectedAction: updatedAction
      }));
      
      // Reload stats
      loadDashboardStats();
      
      return updatedAction;
    } catch (error) {
      console.error('Failed to update action:', error);
      throw error;
    }
  }, []);

  const handleActionApprove = useCallback(async (actionId: string) => {
    try {
      const result = await emailActionsService.approveAction(actionId);
      
      // Reload actions and stats
      await loadActions();
      await loadDashboardStats();
      
      setShowDetailModal(false);
      
      // Show success message (you might want to add a toast notification here)
      alert(result.message);
    } catch (error) {
      console.error('Failed to approve action:', error);
      alert('Failed to approve action. Please try again.');
    }
  }, [state.activeTab, state.filters, state.page, state.pageSize, state.sortBy, state.sortOrder]);

  const handleActionReject = useCallback(async (actionId: string, reason?: string) => {
    try {
      const result = await emailActionsService.rejectAction(actionId, reason);
      
      // Reload actions and stats
      await loadActions();
      await loadDashboardStats();
      
      setShowDetailModal(false);
      
      // Show success message
      alert(result.message);
    } catch (error) {
      console.error('Failed to reject action:', error);
      alert('Failed to reject action. Please try again.');
    }
  }, [state.activeTab, state.filters, state.page, state.pageSize, state.sortBy, state.sortOrder]);

  const loadEmails = async () => {
    setEmailsLoading(true);
    
    try {
      const response = await emailsApi.listEmails(
        state.page,
        state.pageSize,
        emailFilters
      );
      
      setEmails(response.items);
      setState(prev => ({
        ...prev,
        totalPages: response.total_pages
      }));
    } catch (error) {
      console.error('Failed to load emails:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to load emails. Please try again.'
      }));
    } finally {
      setEmailsLoading(false);
    }
  };

  const handleEmailSync = async () => {
    try {
      showInfo('Syncing emails...');
      const result = await emailsApi.syncEmails();
      showSuccess(`Synced ${result.new_emails} new emails successfully!`);
      // Reload emails
      if (state.activeTab === 'emails') {
        loadEmails();
      }
      // Reload stats to update counts
      loadDashboardStats();
    } catch (error) {
      console.error('Failed to sync emails:', error);
      showError('Failed to sync emails. Please try again.');
    }
  };

  const handleProcessEmails = async () => {
    if (selectedEmails.length === 0) {
      showError('Please select at least one email to process.');
      return;
    }
    
    setProcessingEmails(selectedEmails);
    showInfo(`Processing ${selectedEmails.length} email${selectedEmails.length > 1 ? 's' : ''}...`);
    
    try {
      const results = await emailsApi.processEmails(selectedEmails);
      const successCount = results.filter(r => r.success).length;
      const failCount = results.length - successCount;
      
      if (successCount > 0) {
        showSuccess(`Successfully queued ${successCount} email${successCount > 1 ? 's' : ''} for processing by Juno!`);
      }
      if (failCount > 0) {
        showError(`Failed to process ${failCount} email${failCount > 1 ? 's' : ''}.`);
      }
      
      // Clear selection and reload
      setSelectedEmails([]);
      loadEmails();
      
      // Also reload stats to show new pending actions
      loadDashboardStats();
      
      // Switch to pending tab after a short delay to allow processing
      setTimeout(() => {
        setState(prev => ({ ...prev, activeTab: 'pending' }));
        showInfo('Check the Pending Actions tab to review Juno\'s suggestions!');
      }, 1500);
    } catch (error) {
      console.error('Failed to process emails:', error);
      showError('Failed to process emails. Please try again.');
    } finally {
      setProcessingEmails([]);
    }
  };

  const handleTabChange = useCallback((tab: 'emails' | 'pending' | 'completed') => {
    setState(prev => ({
      ...prev,
      activeTab: tab,
      page: 1 // Reset to first page when switching tabs
    }));
  }, []);

  const handlePageChange = useCallback((newPage: number) => {
    setState(prev => ({ ...prev, page: newPage }));
  }, []);

  const handleSortChange = useCallback((sortBy: string, sortOrder: 'asc' | 'desc') => {
    setState(prev => ({ ...prev, sortBy, sortOrder }));
  }, []);

  return (
    <div className="juno-assistant">
      <JunoHeader stats={state.stats} />
      
      <div className="juno-content">
        <div className={`juno-filters-panel ${showFilters ? '' : 'collapsed'}`}>
          <button 
            className="filters-toggle"
            onClick={() => setShowFilters(!showFilters)}
            title={showFilters ? 'Hide filters' : 'Show filters'}
          >
            {showFilters ? '◀' : '▶'}
          </button>
          
          {showFilters && (
            <EmailActionFiltersComponent
              filters={state.filters}
              onFiltersChange={handleFilterChange}
            />
          )}
        </div>
        
        <div className="juno-main">
          <div className="juno-tabs">
            <button
              className={`tab-button ${state.activeTab === 'emails' ? 'active' : ''}`}
              onClick={() => handleTabChange('emails')}
            >
              Emails
            </button>
            <button
              className={`tab-button ${state.activeTab === 'pending' ? 'active' : ''}`}
              onClick={() => handleTabChange('pending')}
            >
              Pending Actions
              {state.stats && state.stats.pending_actions > 0 && (
                <span className="tab-badge">{state.stats.pending_actions}</span>
              )}
            </button>
            <button
              className={`tab-button ${state.activeTab === 'completed' ? 'active' : ''}`}
              onClick={() => handleTabChange('completed')}
            >
              Completed Actions
            </button>
          </div>
          
          {state.activeTab === 'emails' ? (
            <EmailsList
              emails={emails}
              loading={emailsLoading}
              error={state.error}
              selectedEmails={selectedEmails}
              processingEmails={processingEmails}
              onEmailSelect={(emailId) => {
                if (selectedEmails.includes(emailId)) {
                  setSelectedEmails(selectedEmails.filter(id => id !== emailId));
                } else {
                  setSelectedEmails([...selectedEmails, emailId]);
                }
              }}
              onSelectAll={(selected) => {
                if (selected) {
                  setSelectedEmails(emails.map(e => e.id));
                } else {
                  setSelectedEmails([]);
                }
              }}
              onSync={handleEmailSync}
              onProcess={handleProcessEmails}
              page={state.page}
              pageSize={state.pageSize}
              totalPages={state.totalPages}
              onPageChange={handlePageChange}
              filters={emailFilters}
              onFiltersChange={setEmailFilters}
            />
          ) : (
            <EmailActionsList
              actions={state.actions}
              loading={state.loading}
              error={state.error}
              onActionSelect={handleActionSelect}
              page={state.page}
              pageSize={state.pageSize}
              totalPages={state.totalPages}
              onPageChange={handlePageChange}
              sortBy={state.sortBy}
              sortOrder={state.sortOrder}
              onSortChange={handleSortChange}
            />
          )}
        </div>
      </div>
      
      {showDetailModal && state.selectedAction && (
        <EmailActionDetailModal
          action={state.selectedAction}
          onClose={() => setShowDetailModal(false)}
          onUpdate={handleActionUpdate}
          onApprove={handleActionApprove}
          onReject={handleActionReject}
        />
      )}
    </div>
  );
};

export default JunoAssistant;