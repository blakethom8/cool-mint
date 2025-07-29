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
  const [editedData, setEditedData] = useState<any>({});
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [loading, setLoading] = useState(false);

  const validateForm = (): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];
    const data = { ...action.staging_data, ...editedData };

    if (isCallLogStaging(action.staging_data)) {
      if (!data.mno_type) errors.push('Call Type is required');
      if (!data.mno_setting) errors.push('Setting is required');
      if (!data.subject) errors.push('Subject is required');
      if (!data.contact_ids || data.contact_ids.length === 0) {
        errors.push('At least one participant is required');
      }
      if (!data.activity_date) errors.push('Activity Date is required');
    } else if (isNoteStaging(action.staging_data)) {
      if (!data.note_content || data.note_content.trim() === '') {
        errors.push('Note Content is required');
      }
    } else if (isReminderStaging(action.staging_data)) {
      if (!data.reminder_text || data.reminder_text.trim() === '') {
        errors.push('Reminder Text is required');
      }
      if (!data.due_date) errors.push('Due Date is required');
    }

    return { isValid: errors.length === 0, errors };
  };

  const handleApprove = async () => {
    console.log('[DEBUG] Submit button clicked');
    
    // Validate form before proceeding
    const validation = validateForm();
    if (!validation.isValid) {
      showError(`Please fix the following errors:\n${validation.errors.join('\n')}`);
      return;
    }

    if (window.confirm('Are you sure you want to submit this action?')) {
      console.log('[DEBUG] User confirmed submission');
      setLoading(true);
      try {
        // Get the final values - either edited data or original staging data
        const finalValues = Object.keys(editedData).length > 0 
          ? { ...action.staging_data, ...editedData }
          : { ...action.staging_data };
        
        // Get staging ID and determine which transfer method to call
        console.log('[DEBUG] Action staging data:', action.staging_data);
        const stagingId = action.staging_data?.id;
        if (!stagingId) {
          console.error('[ERROR] No staging ID found in:', action);
          throw new Error('No staging data ID found');
        }
        console.log('[DEBUG] Using staging ID:', stagingId);

        // TODO: Get actual user ID from auth context or props
        const userId = 'current-user-id';
        
        // Call the appropriate transfer API based on action type
        console.log('[DEBUG] Calling transfer API:', {
          action_type: action.action_type,
          staging_id: stagingId,
          user_id: userId,
          final_values: finalValues
        });
        
        let result;
        switch (action.action_type) {
          case 'log_call':
            result = await emailActionsService.transferCallLog(stagingId, userId, finalValues);
            break;
          case 'add_note':
            result = await emailActionsService.transferNote(stagingId, userId, finalValues);
            break;
          case 'set_reminder':
            result = await emailActionsService.transferReminder(stagingId, userId, finalValues);
            break;
          default:
            throw new Error(`Unknown action type: ${action.action_type}`);
        }
        
        console.log('[DEBUG] Transfer API response:', result);
        
        showSuccess('Action submitted successfully!');
        
        // Just close the modal - the parent will handle refreshing
        onClose();
      } catch (error) {
        console.error('Failed to submit action:', error);
        showError('Failed to submit action. Please try again.');
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
          {/* Call Type and Setting */}
          <div className="form-row">
            <div className="form-group">
              <label>Call Type*</label>
              <select
                value={editedData.mno_type || action.staging_data.mno_type || ''}
                onChange={(e) => setEditedData({ ...editedData, mno_type: e.target.value })}
              >
                <option value="">Select Type</option>
                <option value="BD_Outreach">BD Outreach</option>
                <option value="MD_to_MD_Visits">MD to MD Visits</option>
                <option value="Client_Maintenance">Client Maintenance</option>
                <option value="Internal_Meeting">Internal Meeting</option>
                <option value="Marketing_Event">Marketing Event</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Setting*</label>
              <select
                value={editedData.mno_setting || action.staging_data.mno_setting || ''}
                onChange={(e) => setEditedData({ ...editedData, mno_setting: e.target.value })}
              >
                <option value="">Select Setting</option>
                <option value="In-Person">In-Person</option>
                <option value="Virtual">Virtual</option>
                <option value="Phone">Phone</option>
                <option value="Email">Email</option>
              </select>
            </div>
          </div>

          {/* Subject */}
          <div className="form-group">
            <label>Subject*</label>
            <input
              type="text"
              value={editedData.subject || action.staging_data.subject || ''}
              onChange={(e) => setEditedData({ ...editedData, subject: e.target.value })}
              placeholder="Brief description of the call"
            />
          </div>

          {/* Contacts */}
          <div className="form-group">
            <label>Participants*</label>
            <div className="contact-list">
              {(editedData.contact_ids || action.staging_data.contact_ids || []).map((contact, index) => (
                <div key={index} className="contact-chip">
                  {contact}
                  <button
                    className="remove-contact"
                    onClick={() => {
                      const newContacts = [...(editedData.contact_ids || action.staging_data.contact_ids || [])];
                      newContacts.splice(index, 1);
                      setEditedData({ ...editedData, contact_ids: newContacts });
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
              <input
                type="text"
                placeholder="Add participant..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value) {
                    const newContacts = [...(editedData.contact_ids || action.staging_data.contact_ids || [])];
                    newContacts.push(e.currentTarget.value);
                    setEditedData({ ...editedData, contact_ids: newContacts });
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>

          {/* Primary Contact */}
          <div className="form-group">
            <label>Primary Contact</label>
            <select
              value={editedData.primary_contact_id || action.staging_data.primary_contact_id || ''}
              onChange={(e) => setEditedData({ ...editedData, primary_contact_id: e.target.value })}
            >
              <option value="">Select Primary Contact</option>
              {(editedData.contact_ids || action.staging_data.contact_ids || []).map((contact, index) => (
                <option key={index} value={contact}>{contact}</option>
              ))}
            </select>
          </div>
          
          {/* Description */}
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={editedData.description || action.staging_data.description || ''}
              onChange={(e) => setEditedData({ ...editedData, description: e.target.value })}
              rows={4}
              placeholder="Detailed notes about the conversation..."
            />
          </div>
          
          {/* Date and Duration */}
          <div className="form-row">
            <div className="form-group">
              <label>Activity Date*</label>
              <input
                type="datetime-local"
                value={editedData.activity_date ? editedData.activity_date.slice(0, 16) : 
                       (action.staging_data.activity_date ? action.staging_data.activity_date.slice(0, 16) : '')}
                onChange={(e) => setEditedData({ ...editedData, activity_date: e.target.value })}
              />
            </div>
            
            <div className="form-group">
              <label>Duration (minutes)</label>
              <input
                type="number"
                value={editedData.duration_minutes || action.staging_data.duration_minutes || ''}
                onChange={(e) => setEditedData({ ...editedData, duration_minutes: parseInt(e.target.value) })}
                min="0"
                placeholder="30"
              />
            </div>
          </div>

          {/* Call Subtype - shown only for certain types */}
          {(editedData.mno_type === 'MD_to_MD_Visits' || action.staging_data.mno_type === 'MD_to_MD_Visits') && (
            <div className="form-group">
              <label>Subtype</label>
              <select
                value={editedData.mno_subtype || action.staging_data.mno_subtype || ''}
                onChange={(e) => setEditedData({ ...editedData, mno_subtype: e.target.value })}
              >
                <option value="">Select Subtype</option>
                <option value="MD_to_MD_w_Cedars">MD to MD with Cedars</option>
                <option value="MD_to_MD_General">MD to MD General</option>
                <option value="MD_to_MD_Referral">MD to MD Referral Discussion</option>
              </select>
            </div>
          )}
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
              rows={6}
            />
          </div>
          
          <div className="form-group">
            <label>Related To</label>
            <input
              type="text"
              value={editedData.related_entity_name || ''}
              onChange={(e) => setEditedData({ ...editedData, related_entity_name: e.target.value })}
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
              />
            </div>
            
            <div className="form-group">
              <label>Priority</label>
              <select
                value={editedData.priority || 'normal'}
                onChange={(e) => setEditedData({ ...editedData, priority: e.target.value })}
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
          {/* Extracted Data Section - Moved to top */}
          <div className="section extracted-data">
            <h3>📝 Action Details</h3>
            {renderStagingDataForm()}
          </div>
          
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
        </div>
        
        <div className="modal-footer">
          {action.status === 'pending' && (
            <>
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
                {loading ? 'Submitting...' : 'Submit'}
              </button>
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