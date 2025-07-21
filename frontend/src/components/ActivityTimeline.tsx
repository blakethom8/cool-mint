import React, { useState } from 'react';
import { ActivityLogItem } from '../types/relationship';
import './ActivityTimeline.css';

interface ActivityTimelineProps {
  activities: ActivityLogItem[];
  relationshipId: string;
}

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
  activities,
  relationshipId
}) => {
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());

  // Toggle activity expansion
  const toggleActivity = (activityId: string) => {
    setExpandedActivities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(activityId)) {
        newSet.delete(activityId);
      } else {
        newSet.add(activityId);
      }
      return newSet;
    });
  };

  // Format activity date
  const formatActivityDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Check if today
    if (date.toDateString() === today.toDateString()) {
      return `Today at ${date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit' 
      })}`;
    }
    
    // Check if yesterday
    if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday at ${date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit' 
      })}`;
    }
    
    // Otherwise show full date
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  // Get activity icon based on type
  const getActivityIcon = (type?: string, mnoType?: string) => {
    if (mnoType) {
      switch (mnoType.toLowerCase()) {
        case 'meeting':
          return '📅';
        case 'call':
          return '📞';
        case 'email':
          return '✉️';
        case 'event':
          return '🎫';
        case 'note':
          return '📝';
        default:
          return '📌';
      }
    }
    
    switch (type?.toLowerCase()) {
      case 'task':
        return '✓';
      case 'meeting':
        return '📅';
      case 'call':
        return '📞';
      default:
        return '📌';
    }
  };

  // Get activity type label
  const getActivityTypeLabel = (activity: ActivityLogItem) => {
    if (activity.mno_type && activity.mno_subtype) {
      return `${activity.mno_type} - ${activity.mno_subtype}`;
    }
    return activity.mno_type || activity.activity_type;
  };

  if (activities.length === 0) {
    return (
      <div className="activity-timeline__empty">
        <p>No activities recorded yet</p>
        <button className="btn btn-primary">
          Log First Activity
        </button>
      </div>
    );
  }

  return (
    <div className="activity-timeline">
      <div className="activity-timeline__header">
        <h3>Activity History</h3>
        <button className="btn btn-primary btn-sm">
          + Log Activity
        </button>
      </div>
      
      <div className="activity-timeline__list">
        {activities.map((activity, index) => (
          <div 
            key={activity.activity_id} 
            className={`activity-timeline__item ${index === 0 ? 'first' : ''}`}
          >
            <div className="activity-timeline__marker">
              <span className="icon">
                {getActivityIcon(activity.activity_type, activity.mno_type)}
              </span>
            </div>
            
            <div className="activity-timeline__content">
              <div 
                className="activity-timeline__header-row"
                onClick={() => toggleActivity(activity.activity_id)}
              >
                <div className="activity-timeline__title">
                  <h4>{activity.subject}</h4>
                  <span className="activity-timeline__type">
                    {getActivityTypeLabel(activity)}
                  </span>
                  {activity.status && (
                    <span className={`activity-timeline__status ${activity.status.toLowerCase()}`}>
                      {activity.status}
                    </span>
                  )}
                </div>
                <div className="activity-timeline__meta">
                  <span className="date">{formatActivityDate(activity.activity_date)}</span>
                  <span className="owner">by {activity.owner_name}</span>
                </div>
              </div>
              
              {expandedActivities.has(activity.activity_id) && activity.description && (
                <div className="activity-timeline__description">
                  <p>{activity.description}</p>
                  {activity.contact_names.length > 0 && (
                    <div className="activity-timeline__contacts">
                      <strong>Attendees:</strong> {activity.contact_names.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="activity-timeline__footer">
        <button className="btn btn-link">
          View All Activities →
        </button>
      </div>
    </div>
  );
};

export default ActivityTimeline;