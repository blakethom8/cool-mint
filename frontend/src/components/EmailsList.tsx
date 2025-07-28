import React from 'react';
import { Email, EmailFilters } from '../types/emails';
import './EmailsList.css';

interface EmailsListProps {
  emails: Email[];
  loading: boolean;
  error?: string;
  selectedEmails: string[];
  processingEmails: string[];
  onEmailSelect: (emailId: string) => void;
  onSelectAll: (selected: boolean) => void;
  onSync: () => void;
  onProcess: () => void;
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  filters: EmailFilters;
  onFiltersChange: (filters: EmailFilters) => void;
}

const EmailsList: React.FC<EmailsListProps> = ({
  emails,
  loading,
  error,
  selectedEmails,
  processingEmails,
  onEmailSelect,
  onSelectAll,
  onSync,
  onProcess,
  page,
  pageSize,
  totalPages,
  onPageChange,
  filters,
  onFiltersChange
}) => {
  const allSelected = emails.length > 0 && emails.every(email => selectedEmails.includes(email.id));
  const someSelected = selectedEmails.length > 0;

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    }
    if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' });
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const truncateText = (text: string | null, maxLength: number) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="emails-list">
      <div className="emails-toolbar">
        <div className="toolbar-left">
          <button
            className="juno-button primary"
            onClick={onSync}
            disabled={loading}
          >
            <span className="icon">🔄</span> Refresh Emails
          </button>
          <button
            className="juno-button secondary"
            onClick={onProcess}
            disabled={!someSelected || processingEmails.length > 0}
          >
            <span className="icon">🤖</span> Process with Juno ({selectedEmails.length})
          </button>
        </div>
        <div className="toolbar-right">
          <input
            type="text"
            placeholder="Search emails..."
            value={filters.search_text || ''}
            onChange={(e) => onFiltersChange({ ...filters, search_text: e.target.value })}
            className="email-search"
          />
          <select
            value={filters.processed?.toString() || 'all'}
            onChange={(e) => onFiltersChange({ 
              ...filters, 
              processed: e.target.value === 'all' ? undefined : e.target.value === 'true' 
            })}
            className="email-filter-select"
          >
            <option value="all">All Emails</option>
            <option value="false">Unprocessed</option>
            <option value="true">Processed</option>
          </select>
        </div>
      </div>

      {loading && (
        <div className="emails-loading">
          <div className="juno-loader"></div>
          <p>Loading emails...</p>
        </div>
      )}

      {error && (
        <div className="emails-error">
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && emails.length === 0 && (
        <div className="emails-empty">
          <p>No emails found. Click "Refresh Emails" to sync from your inbox.</p>
        </div>
      )}

      {!loading && !error && emails.length > 0 && (
        <>
          <table className="emails-table">
            <thead>
              <tr>
                <th className="checkbox-column">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={(e) => onSelectAll(e.target.checked)}
                  />
                </th>
                <th>From</th>
                <th>Subject</th>
                <th>Snippet</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {emails.map(email => (
                <tr 
                  key={email.id}
                  className={`email-row ${selectedEmails.includes(email.id) ? 'selected' : ''} ${processingEmails.includes(email.id) ? 'processing' : ''}`}
                >
                  <td className="checkbox-column">
                    <input
                      type="checkbox"
                      checked={selectedEmails.includes(email.id)}
                      onChange={() => onEmailSelect(email.id)}
                      disabled={processingEmails.includes(email.id)}
                    />
                  </td>
                  <td className="from-column">
                    <div className="from-info">
                      <div className="from-name">{email.from_name || 'Unknown'}</div>
                      <div className="from-email">{email.from_email || ''}</div>
                    </div>
                  </td>
                  <td className="subject-column">
                    <div className="subject-text">
                      {email.unread && <span className="unread-indicator">●</span>}
                      {email.subject}
                      {email.is_forwarded && <span className="forwarded-badge">FWD</span>}
                      {email.has_attachments && <span className="attachment-icon">📎</span>}
                    </div>
                  </td>
                  <td className="snippet-column">
                    {truncateText(email.snippet, 100)}
                  </td>
                  <td className="date-column">
                    {formatDate(email.date)}
                  </td>
                  <td className="status-column">
                    {processingEmails.includes(email.id) ? (
                      <span className="status-badge processing">Processing...</span>
                    ) : email.processed ? (
                      <span className="status-badge processed">Processed</span>
                    ) : (
                      <span className="status-badge unprocessed">Unprocessed</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="emails-pagination">
              <button
                onClick={() => onPageChange(page - 1)}
                disabled={page === 1}
                className="page-button"
              >
                Previous
              </button>
              <span className="page-info">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => onPageChange(page + 1)}
                disabled={page === totalPages}
                className="page-button"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EmailsList;