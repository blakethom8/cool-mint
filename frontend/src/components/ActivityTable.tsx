import React from 'react';
import { ActivityListItem } from '../types/activity';
import './ActivityTable.css';

interface ActivityTableProps {
  activities: ActivityListItem[];
  selectedActivityIds: Set<string>;
  onSelectionChange: (activityId: string, isSelected: boolean) => void;
  onSelectAll: (isSelected: boolean) => void;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalCount?: number;
}

export const ActivityTable: React.FC<ActivityTableProps> = ({
  activities,
  selectedActivityIds,
  onSelectionChange,
  onSelectAll,
  currentPage,
  totalPages,
  onPageChange,
  totalCount = 0,
}) => {
  const allSelected = activities.length > 0 && activities.every(a => selectedActivityIds.has(a.activity_id));

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="activity-table-container">
      <table className="activity-table">
        <thead>
          <tr>
            <th className="checkbox-column">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={(e) => onSelectAll(e.target.checked)}
              />
            </th>
            <th>Date</th>
            <th>Subject</th>
            <th>Owner</th>
            <th>Type</th>
            <th>Status</th>
            <th>Contacts</th>
            <th>Specialties</th>
          </tr>
        </thead>
        <tbody>
          {activities.map((activity) => (
            <tr key={activity.activity_id}>
              <td className="checkbox-column">
                <input
                  type="checkbox"
                  checked={selectedActivityIds.has(activity.activity_id)}
                  onChange={(e) => onSelectionChange(activity.activity_id, e.target.checked)}
                />
              </td>
              <td>{formatDate(activity.activity_date)}</td>
              <td className="subject-cell">
                <div className="subject">{activity.subject}</div>
                {activity.description && (
                  <div className="description">{activity.description}</div>
                )}
              </td>
              <td>{activity.owner_name || '-'}</td>
              <td>
                <div className="type-info">
                  {activity.mno_type || activity.type || '-'}
                  {activity.mno_subtype && (
                    <div className="subtype">{activity.mno_subtype}</div>
                  )}
                </div>
              </td>
              <td>
                <span className={`status ${activity.status?.toLowerCase()}`}>
                  {activity.status || '-'}
                </span>
              </td>
              <td>
                <div className="contact-info">
                  {activity.contact_count > 0 ? (
                    <>
                      <div className="contact-count">{activity.contact_count} contacts</div>
                      {activity.contact_names.length > 0 && (
                        <div className="contact-names">
                          {activity.contact_names.slice(0, 2).join(', ')}
                          {activity.contact_names.length > 2 && ' ...'}
                        </div>
                      )}
                    </>
                  ) : (
                    '-'
                  )}
                </div>
              </td>
              <td>
                {activity.contact_specialties.length > 0 ? (
                  <div className="specialties">
                    {activity.contact_specialties.slice(0, 2).join(', ')}
                    {activity.contact_specialties.length > 2 && ' ...'}
                  </div>
                ) : (
                  '-'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {activities.length === 0 && (
        <div className="no-results">No activities found</div>
      )}

      <div className="pagination">
        <div className="pagination-info">
          Showing {activities.length} of {totalCount.toLocaleString()} activities
          {totalPages > 1 && (
            <span className="page-details">
              (Page {currentPage} of {totalPages})
            </span>
          )}
        </div>
        <div className="pagination-controls">
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
          >
            First
          </button>
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span className="page-info">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage === totalPages}
          >
            Last
          </button>
        </div>
      </div>
    </div>
  );
};