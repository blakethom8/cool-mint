import React, { useState } from 'react';
import {
  EmailAction,
  ACTION_TYPE_ICONS,
  ACTION_TYPE_LABELS,
  isCallLogStaging,
  isNoteStaging,
  isReminderStaging
} from '../types/emailActions';
import emailActionsService from '../services/emailActionsService';
import { useNotification } from '../contexts/NotificationContext';
import './EmailActionDetailModal.css';

interface EmailActionDetailModalProps {
  action: EmailAction;
  onClose: () => void;
  onUpdate: (actionId: string, updates: any) => Promise<EmailAction>;
  onApprove: (actionId: string) => Promise<void>;
  onReject: (actionId: string, reason?: string) => Promise<void>;
}

const EmailActionDetailModal: React.FC<EmailActionDetailModalProps> = ({
  action,
  onClose,
  onUpdate,
  onApprove,
  onReject
}) => {
  const { showSuccess, showError } = useNotification();
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState<any>({});
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleEdit = () => {
    // Initialize edited data with current staging data
    if (action.staging_data) {
      setEditedData({ ...action.staging_data });
    }
    setIsEditing(true);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await onUpdate(action.id, { staging_updates: editedData });
      setIsEditing(false);
      setEditedData({});
    } catch (error) {
      console.error('Failed to save changes:', error);
      alert('Failed to save changes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedData({});
  };

  const handleApprove = async () => {
    if (window.confirm('Are you sure you want to approve this action? It will be processed by Juno.')) {
      setLoading(true);
      try {
        await onApprove(action.id);
        showSuccess('Action approved successfully!');
        onClose();
      } catch (error) {
        console.error('Failed to approve action:', error);
        showError('Failed to approve action. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleReject = async () => {
    setLoading(true);
    try {
      await onReject(action.id, rejectReason);
      setShowRejectDialog(false);
      showSuccess('Action rejected successfully.');
      onClose();
    } catch (error) {
      console.error('Failed to reject action:', error);
      showError('Failed to reject action. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStagingDataForm = () => {
    if (!action.staging_data) return null;

    if (isCallLogStaging(action.staging_data)) {
      return (
        <div className="staging-data-form">
          <div className="form-group">
            <label>Subject</label>
            <input
              type="text"
              value={editedData.subject || ''}
              onChange={(e) => setEditedData({ ...editedData, subject: e.target.value })}
              disabled={!isEditing}
            />
          </div>
          
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={editedData.description || ''}
              onChange={(e) => setEditedData({ ...editedData, description: e.target.value })}
              disabled={!isEditing}
              rows={4}
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>Activity Date</label>
              <input
                type="datetime-local"
                value={editedData.activity_date ? editedData.activity_date.slice(0, 16) : ''}
                onChange={(e) => setEditedData({ ...editedData, activity_date: e.target.value })}
                disabled={!isEditing}
              />
            </div>
            
            <div className="form-group">
              <label>Duration (minutes)</label>
              <input
                type="number"
                value={editedData.duration_minutes || ''}
                onChange={(e) => setEditedData({ ...editedData, duration_minutes: parseInt(e.target.value) })}
                disabled={!isEditing}
              />
            </div>
          </div>
        </div>
      );
    }

    if (isNoteStaging(action.staging_data)) {
      return (
        <div className="staging-data-form">
          <div className="form-group">
            <label>Note Content</label>
            <textarea
              value={editedData.note_content || ''}
              onChange={(e) => setEditedData({ ...editedData, note_content: e.target.value })}
              disabled={!isEditing}
              rows={6}
            />
          </div>
          
          <div className="form-group">
            <label>Related To</label>
            <input
              type="text"
              value={editedData.related_entity_name || ''}
              onChange={(e) => setEditedData({ ...editedData, related_entity_name: e.target.value })}
              disabled={!isEditing}
            />
          </div>
        </div>
      );
    }

    if (isReminderStaging(action.staging_data)) {
      return (
        <div className="staging-data-form">
          <div className="form-group">
            <label>Reminder Text</label>
            <textarea
              value={editedData.reminder_text || ''}
              onChange={(e) => setEditedData({ ...editedData, reminder_text: e.target.value })}
              disabled={!isEditing}
              rows={3}
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>Due Date</label>
              <input
                type="datetime-local"
                value={editedData.due_date ? editedData.due_date.slice(0, 16) : ''}
                onChange={(e) => setEditedData({ ...editedData, due_date: e.target.value })}
                disabled={!isEditing}
              />
            </div>
            
            <div className="form-group">
              <label>Priority</label>
              <select
                value={editedData.priority || 'normal'}
                onChange={(e) => setEditedData({ ...editedData, priority: e.target.value })}
                disabled={!isEditing}
              >
                <option value="high">High</option>
                <option value="normal">Normal</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="action-icon">{ACTION_TYPE_ICONS[action.action_type]}</span>
            <h2>{ACTION_TYPE_LABELS[action.action_type]} - Review & Approve</h2>
          </div>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          {/* AI Analysis Section */}
          <div className="section ai-analysis">
            <h3>🤖 Juno's Analysis</h3>
            <div className="ai-confidence">
              <span>Confidence Score:</span>
              <strong>{emailActionsService.formatConfidence(action.confidence_score)}</strong>
            </div>
            <div className="ai-reasoning">
              <p>{action.reasoning}</p>
            </div>
          </div>
          
          {/* Original Email Section */}
          <div className="section email-context">
            <h3>📧 Email Context</h3>
            <div className="email-details">
              <div className="email-meta">
                <div><strong>From:</strong> {action.email.from_email}</div>
                <div><strong>Subject:</strong> {action.email.subject}</div>
                {action.email.date && (
                  <div><strong>Date:</strong> {emailActionsService.formatDate(action.email.date)}</div>
                )}
              </div>
              
              {action.email.user_instruction && (
                <div className="user-instruction">
                  <strong>Your Instructions:</strong>
                  <p>{action.email.user_instruction}</p>
                </div>
              )}
              
              <div className="email-content">
                <strong>Email Content:</strong>
                <div className="content-box">
                  {action.email.parsed_content || action.email.content}
                </div>
              </div>
            </div>
          </div>
          
          {/* Extracted Data Section */}
          <div className="section extracted-data">
            <h3>📝 Extracted Information</h3>
            {renderStagingDataForm()}
          </div>
        </div>
        
        <div className="modal-footer">
          {action.status === 'pending' && (
            <>
              {!isEditing ? (
                <>
                  <button 
                    className="btn btn-secondary" 
                    onClick={handleEdit}
                    disabled={loading}
                  >
                    Edit Details
                  </button>
                  <button 
                    className="btn btn-danger" 
                    onClick={() => setShowRejectDialog(true)}
                    disabled={loading}
                  >
                    Reject
                  </button>
                  <button 
                    className="btn btn-primary" 
                    onClick={handleApprove}
                    disabled={loading}
                  >
                    {loading ? 'Processing...' : 'Approve & Execute'}
                  </button>
                </>
              ) : (
                <>
                  <button 
                    className="btn btn-secondary" 
                    onClick={handleCancel}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                  <button 
                    className="btn btn-primary" 
                    onClick={handleSave}
                    disabled={loading}
                  >
                    {loading ? 'Saving...' : 'Save Changes'}
                  </button>
                </>
              )}
            </>
          )}
        </div>
        
        {/* Reject Dialog */}
        {showRejectDialog && (
          <div className="reject-dialog">
            <div className="dialog-content">
              <h3>Reject Action</h3>
              <p>Please provide a reason for rejection (optional):</p>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="This will help Juno learn and improve..."
                rows={3}
              />
              <div className="dialog-actions">
                <button 
                  className="btn btn-secondary" 
                  onClick={() => setShowRejectDialog(false)}
                >
                  Cancel
                </button>
                <button 
                  className="btn btn-danger" 
                  onClick={handleReject}
                  disabled={loading}
                >
                  {loading ? 'Rejecting...' : 'Confirm Rejection'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailActionDetailModal;