import React from 'react';
import { 
  EmailAction, 
  ACTION_TYPE_ICONS, 
  ACTION_TYPE_LABELS,
  STATUS_COLORS,
  STATUS_LABELS,
  isCallLogStaging,
  isNoteStaging,
  isReminderStaging
} from '../types/emailActions';
import emailActionsService from '../services/emailActionsService';
import './EmailActionCard.css';

interface EmailActionCardProps {
  action: EmailAction;
  onClick: () => void;
}

const EmailActionCard: React.FC<EmailActionCardProps> = ({ action, onClick }) => {
  const getActionPreview = () => {
    if (!action.staging_data) return action.action_parameters?.description || 'No preview available';
    
    if (isCallLogStaging(action.staging_data)) {
      return action.staging_data.subject || 'Call log';
    } else if (isNoteStaging(action.staging_data)) {
      const preview = action.staging_data.note_content || '';
      return preview.length > 150 ? preview.substring(0, 150) + '...' : preview;
    } else if (isReminderStaging(action.staging_data)) {
      return action.staging_data.reminder_text || 'Reminder';
    }
    
    return 'Action details available';
  };

  const getEntityInfo = () => {
    if (!action.staging_data) return null;
    
    if (isCallLogStaging(action.staging_data)) {
      return action.staging_data.primary_contact_id 
        ? `Contact: ${action.staging_data.primary_contact_id}`
        : null;
    } else if (isNoteStaging(action.staging_data)) {
      return action.staging_data.related_entity_name 
        ? `${action.staging_data.related_entity_type}: ${action.staging_data.related_entity_name}`
        : null;
    } else if (isReminderStaging(action.staging_data)) {
      return action.staging_data.due_date 
        ? `Due: ${emailActionsService.formatDate(action.staging_data.due_date)}`
        : null;
    }
    
    return null;
  };

  return (
    <div className="email-action-card" onClick={onClick}>
      <div className="action-card-header">
        <div className="action-type">
          <span className="action-icon">{ACTION_TYPE_ICONS[action.action_type]}</span>
          <span className="action-label">{ACTION_TYPE_LABELS[action.action_type]}</span>
        </div>
        
        <div 
          className="action-status"
          style={{ backgroundColor: STATUS_COLORS[action.status] }}
        >
          {STATUS_LABELS[action.status]}
        </div>
      </div>
      
      <div className="action-card-body">
        <div className="action-preview">
          {getActionPreview()}
        </div>
        
        {getEntityInfo() && (
          <div className="action-entity">
            {getEntityInfo()}
          </div>
        )}
        
        <div className="action-email-info">
          <div className="email-from">
            From: {action.email.from_email}
          </div>
          <div className="email-subject">
            Re: {action.email.subject}
          </div>
        </div>
        
        <div className="action-metadata">
          <div className="confidence-score">
            <span className="confidence-label">Confidence:</span>
            <div className="confidence-bar">
              <div 
                className="confidence-fill"
                style={{ 
                  width: `${action.confidence_score * 100}%`,
                  backgroundColor: action.confidence_score > 0.8 ? '#28a745' : 
                                 action.confidence_score > 0.6 ? '#ffc107' : '#dc3545'
                }}
              />
            </div>
            <span className="confidence-value">
              {emailActionsService.formatConfidence(action.confidence_score)}
            </span>
          </div>
          
          <div className="action-time">
            {emailActionsService.getTimeSince(action.created_at)}
          </div>
        </div>
      </div>
      
      <div className="action-card-footer">
        <button className="action-button review">
          Review & Edit
        </button>
      </div>
    </div>
  );
};

export default EmailActionCard;