import React from 'react';
import { EmailAction } from '../types/emailActions';
import EmailActionCard from './EmailActionCard';
import './EmailActionsList.css';

interface EmailActionsListProps {
  actions: EmailAction[];
  loading: boolean;
  error?: string;
  onActionSelect: (action: EmailAction) => void;
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSortChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
}

const EmailActionsList: React.FC<EmailActionsListProps> = ({
  actions,
  loading,
  error,
  onActionSelect,
  page,
  pageSize,
  totalPages,
  onPageChange,
  sortBy,
  sortOrder,
  onSortChange
}) => {
  if (loading && (!actions || actions.length === 0)) {
    return (
      <div className="actions-list-loading">
        <div className="loading-spinner"></div>
        <p>Loading actions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="actions-list-error">
        <h3>⚠️ Error</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!actions || actions.length === 0) {
    return (
      <div className="actions-list-empty">
        <div className="empty-icon">📭</div>
        <h3>No Actions Found</h3>
        <p>There are no email actions matching your current filters.</p>
        <p className="empty-hint">
          Forward an email to <strong>thomsonblakecrm@gmail.com</strong> with instructions to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="email-actions-list">
      <div className="actions-list-header">
        <div className="list-info">
          Showing {actions.length > 0 ? `${(page - 1) * pageSize + 1} - ${Math.min(page * pageSize, (page - 1) * pageSize + actions.length)}` : '0'} actions
        </div>
        
        <div className="list-controls">
          <label htmlFor="sort-select">Sort by:</label>
          <select
            id="sort-select"
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [newSortBy, newSortOrder] = e.target.value.split('-');
              onSortChange(newSortBy, newSortOrder as 'asc' | 'desc');
            }}
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="confidence_score-desc">Highest Confidence</option>
            <option value="confidence_score-asc">Lowest Confidence</option>
            <option value="action_type-asc">Action Type</option>
          </select>
        </div>
      </div>

      <div className="actions-grid">
        {actions.map((action) => (
          <EmailActionCard
            key={action.id}
            action={action}
            onClick={() => onActionSelect(action)}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="actions-pagination">
          <button
            className="pagination-btn"
            onClick={() => onPageChange(1)}
            disabled={page === 1}
          >
            First
          </button>
          
          <button
            className="pagination-btn"
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
          >
            Previous
          </button>
          
          <span className="pagination-info">
            Page {page} of {totalPages}
          </span>
          
          <button
            className="pagination-btn"
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
          >
            Next
          </button>
          
          <button
            className="pagination-btn"
            onClick={() => onPageChange(totalPages)}
            disabled={page === totalPages}
          >
            Last
          </button>
        </div>
      )}
    </div>
  );
};

export default EmailActionsList;