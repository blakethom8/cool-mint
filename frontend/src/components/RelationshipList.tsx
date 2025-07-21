import React, { useState, useCallback } from 'react';
import {
  RelationshipListItem,
  RelationshipTableState,
  FilterOptionsResponse,
  RELATIONSHIP_STATUS_COLORS,
  LEAD_SCORE_LABELS
} from '../types/relationship';
import './RelationshipList.css';

interface RelationshipListProps {
  relationships: RelationshipListItem[];
  tableState: RelationshipTableState;
  loading: boolean;
  filterOptions?: FilterOptionsResponse;
  onRelationshipSelect: (relationship: RelationshipListItem) => void;
  onTableStateChange: (updates: Partial<RelationshipTableState>) => void;
  onBulkUpdate: (selectedIds: Set<string>, updates: any) => void;
}

const RelationshipList: React.FC<RelationshipListProps> = ({
  relationships,
  tableState,
  loading,
  filterOptions,
  onRelationshipSelect,
  onTableStateChange,
  onBulkUpdate
}) => {
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [bulkStatusId, setBulkStatusId] = useState<number | null>(null);
  const [bulkLoyaltyId, setBulkLoyaltyId] = useState<number | null>(null);

  // Handle select all
  const handleSelectAll = useCallback((checked: boolean) => {
    if (checked) {
      const allIds = new Set(relationships.map(r => r.relationship_id));
      onTableStateChange({ selectedIds: allIds });
    } else {
      onTableStateChange({ selectedIds: new Set() });
    }
  }, [relationships, onTableStateChange]);

  // Handle individual selection
  const handleSelectOne = useCallback((relationshipId: string, checked: boolean) => {
    const newSelectedIds = new Set(tableState.selectedIds);
    if (checked) {
      newSelectedIds.add(relationshipId);
    } else {
      newSelectedIds.delete(relationshipId);
    }
    onTableStateChange({ selectedIds: newSelectedIds });
  }, [tableState.selectedIds, onTableStateChange]);

  // Handle sorting
  const handleSort = useCallback((column: string) => {
    if (tableState.sortBy === column) {
      onTableStateChange({
        sortOrder: tableState.sortOrder === 'asc' ? 'desc' : 'asc'
      });
    } else {
      onTableStateChange({
        sortBy: column,
        sortOrder: 'desc'
      });
    }
  }, [tableState.sortBy, tableState.sortOrder, onTableStateChange]);

  // Apply bulk updates
  const applyBulkUpdates = useCallback(() => {
    const updates: any = {};
    if (bulkStatusId !== null) updates.relationship_status_id = bulkStatusId;
    if (bulkLoyaltyId !== null) updates.loyalty_status_id = bulkLoyaltyId;
    
    if (Object.keys(updates).length > 0) {
      onBulkUpdate(tableState.selectedIds, updates);
      setShowBulkActions(false);
      setBulkStatusId(null);
      setBulkLoyaltyId(null);
    }
  }, [bulkStatusId, bulkLoyaltyId, tableState.selectedIds, onBulkUpdate]);

  // Format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };


  // Render sort indicator
  const renderSortIndicator = (column: string) => {
    if (tableState.sortBy !== column) return null;
    return (
      <span className="relationship-list__sort-indicator">
        {tableState.sortOrder === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  // Render star rating
  const renderStarRating = (score?: number) => {
    if (!score) return <span className="relationship-list__no-score">-</span>;
    return (
      <span className="relationship-list__stars" title={LEAD_SCORE_LABELS[score]}>
        {'★'.repeat(score)}{'☆'.repeat(5 - score)}
      </span>
    );
  };

  if (loading && relationships.length === 0) {
    return (
      <div className="relationship-list__loading">
        <div className="spinner"></div>
        <p>Loading relationships...</p>
      </div>
    );
  }

  return (
    <div className="relationship-list">
      {/* Bulk Actions Bar */}
      {tableState.selectedIds.size > 0 && (
        <div className="relationship-list__bulk-actions">
          <span className="relationship-list__selected-count">
            {tableState.selectedIds.size} selected
          </span>
          
          {!showBulkActions ? (
            <button 
              className="btn btn-secondary"
              onClick={() => setShowBulkActions(true)}
            >
              Bulk Actions
            </button>
          ) : (
            <div className="relationship-list__bulk-controls">
              <select 
                value={bulkStatusId || ''}
                onChange={(e) => setBulkStatusId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">Relationship Status...</option>
                {filterOptions?.relationship_statuses.map(status => (
                  <option key={status.id} value={status.id}>
                    {status.display_name}
                  </option>
                ))}
              </select>
              
              <select 
                value={bulkLoyaltyId || ''}
                onChange={(e) => setBulkLoyaltyId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">Loyalty Status...</option>
                {filterOptions?.loyalty_statuses.map(status => (
                  <option key={status.id} value={status.id}>
                    {status.display_name}
                  </option>
                ))}
              </select>
              
              <button 
                className="btn btn-primary"
                onClick={applyBulkUpdates}
                disabled={bulkStatusId === null && bulkLoyaltyId === null}
              >
                Apply
              </button>
              
              <button 
                className="btn btn-secondary"
                onClick={() => {
                  setShowBulkActions(false);
                  setBulkStatusId(null);
                  setBulkLoyaltyId(null);
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}

      {/* Table */}
      <div className="relationship-list__table-wrapper">
        <table className="relationship-list__table">
          <thead>
            <tr>
              <th className="relationship-list__checkbox-column">
                <input
                  type="checkbox"
                  checked={relationships.length > 0 && tableState.selectedIds.size === relationships.length}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
              </th>
              <th 
                className="relationship-list__sortable"
                onClick={() => handleSort('entity_name')}
              >
                Name {renderSortIndicator('entity_name')}
              </th>
              <th>Type</th>
              <th>User</th>
              <th 
                className="relationship-list__sortable"
                onClick={() => handleSort('relationship_status')}
              >
                Status {renderSortIndicator('relationship_status')}
              </th>
              <th>Loyalty</th>
              <th 
                className="relationship-list__sortable"
                onClick={() => handleSort('lead_score')}
              >
                Score {renderSortIndicator('lead_score')}
              </th>
              <th 
                className="relationship-list__sortable"
                onClick={() => handleSort('last_activity_date')}
              >
                Last Activity {renderSortIndicator('last_activity_date')}
              </th>
              <th 
                className="relationship-list__sortable"
                onClick={() => handleSort('activity_count')}
              >
                Activities {renderSortIndicator('activity_count')}
              </th>
              <th>Campaigns</th>
            </tr>
          </thead>
          <tbody>
            {relationships.map(relationship => (
              <tr 
                key={relationship.relationship_id}
                className={tableState.selectedIds.has(relationship.relationship_id) ? 'selected' : ''}
              >
                <td className="relationship-list__checkbox-column">
                  <input
                    type="checkbox"
                    checked={tableState.selectedIds.has(relationship.relationship_id)}
                    onChange={(e) => handleSelectOne(relationship.relationship_id, e.target.checked)}
                  />
                </td>
                <td 
                  className="relationship-list__name-cell"
                  onClick={() => onRelationshipSelect(relationship)}
                >
                  <div className="relationship-list__name">
                    {relationship.entity_name}
                  </div>
                  {relationship.entity_details.specialty && (
                    <div className="relationship-list__subtitle">
                      {relationship.entity_details.specialty}
                    </div>
                  )}
                </td>
                <td>
                  <span className="relationship-list__entity-type">
                    {relationship.entity_type.common_name}
                  </span>
                </td>
                <td>{relationship.user_name}</td>
                <td>
                  <span 
                    className="relationship-list__status-badge"
                    style={{ 
                      backgroundColor: RELATIONSHIP_STATUS_COLORS[relationship.relationship_status.code] || '#6c757d' 
                    }}
                  >
                    {relationship.relationship_status.display_name}
                  </span>
                </td>
                <td>
                  {relationship.loyalty_status && (
                    <span 
                      className="relationship-list__loyalty-badge"
                      style={{
                        borderLeft: `3px solid ${relationship.loyalty_status.color_hex || '#ccc'}`
                      }}
                    >
                      {relationship.loyalty_status.display_name}
                    </span>
                  )}
                </td>
                <td>{renderStarRating(relationship.lead_score)}</td>
                <td>
                  <div className="relationship-list__date">
                    {formatDate(relationship.last_activity_date)}
                  </div>
                  {relationship.days_since_activity !== undefined && (
                    <div className="relationship-list__days-ago">
                      {relationship.days_since_activity}d ago
                    </div>
                  )}
                </td>
                <td className="relationship-list__activity-count">
                  {relationship.activity_count || 0}
                </td>
                <td>
                  {relationship.campaign_count > 0 && (
                    <span className="relationship-list__campaign-count">
                      {relationship.campaign_count}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {relationships.length === 0 && !loading && (
          <div className="relationship-list__empty">
            <p>No relationships found matching your filters.</p>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="relationship-list__pagination">
        <div className="relationship-list__page-info">
          Showing {((tableState.page - 1) * tableState.pageSize) + 1} to{' '}
          {Math.min(tableState.page * tableState.pageSize, relationships.length)} of{' '}
          {relationships.length} relationships
        </div>
        
        <div className="relationship-list__page-controls">
          <button
            className="btn btn-sm"
            disabled={tableState.page === 1}
            onClick={() => onTableStateChange({ page: tableState.page - 1 })}
          >
            Previous
          </button>
          
          <span className="relationship-list__page-number">
            Page {tableState.page}
          </span>
          
          <button
            className="btn btn-sm"
            disabled={relationships.length < tableState.pageSize}
            onClick={() => onTableStateChange({ page: tableState.page + 1 })}
          >
            Next
          </button>
        </div>
        
        <div className="relationship-list__page-size">
          <label>
            Show:
            <select
              value={tableState.pageSize}
              onChange={(e) => onTableStateChange({ 
                pageSize: Number(e.target.value),
                page: 1 
              })}
            >
              <option value={15}>15</option>
              <option value={20}>20</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
        </div>
      </div>
    </div>
  );
};

export default RelationshipList;