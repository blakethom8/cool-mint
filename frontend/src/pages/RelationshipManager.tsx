import React, { useState, useEffect, useCallback } from 'react';
import {
  RelationshipListItem,
  RelationshipDetail,
  RelationshipFilters,
  FilterOptionsResponse,
  RelationshipManagerState,
  RelationshipTableState
} from '../types/relationship';
import relationshipService from '../services/relationshipService';
import RelationshipFiltersComponent from '../components/RelationshipFilters';
import RelationshipList from '../components/RelationshipList';
import RelationshipDetailComponent from '../components/RelationshipDetail';
import './RelationshipManager.css';

const RelationshipManager: React.FC = () => {
  // State management
  const [state, setState] = useState<RelationshipManagerState>({
    filters: {},
    relationships: [],
    selectedRelationship: undefined,
    filterOptions: undefined,
    loading: false,
    error: undefined,
    tableState: {
      selectedIds: new Set<string>(),
      sortBy: 'last_activity_date',
      sortOrder: 'desc',
      page: 1,
      pageSize: 20
    },
    rightPanelOpen: false
  });

  // Panel visibility states
  const [showFilters, setShowFilters] = useState(true);
  const [showDetails, setShowDetails] = useState(true);

  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Load relationships when filters or pagination changes
  useEffect(() => {
    loadRelationships();
  }, [state.filters, state.tableState.page, state.tableState.pageSize, state.tableState.sortBy, state.tableState.sortOrder]);

  // Load filter options
  const loadFilterOptions = async () => {
    try {
      const options = await relationshipService.getFilterOptions();
      setState(prev => ({ ...prev, filterOptions: options }));
    } catch (error) {
      console.error('Failed to load filter options:', error);
      setState(prev => ({ ...prev, error: 'Failed to load filter options' }));
    }
  };

  // Load relationships
  const loadRelationships = async () => {
    setState(prev => ({ ...prev, loading: true, error: undefined }));
    
    try {
      const response = await relationshipService.listRelationships(
        state.tableState.page,
        state.tableState.pageSize,
        state.tableState.sortBy,
        state.tableState.sortOrder,
        state.filters
      );
      
      setState(prev => ({
        ...prev,
        relationships: response.items,
        loading: false
      }));
    } catch (error) {
      console.error('Failed to load relationships:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load relationships'
      }));
    }
  };

  // Handle filter changes
  const handleFilterChange = useCallback((newFilters: RelationshipFilters) => {
    setState(prev => ({
      ...prev,
      filters: newFilters,
      tableState: { ...prev.tableState, page: 1 } // Reset to first page
    }));
  }, []);

  // Handle relationship selection
  const handleRelationshipSelect = useCallback(async (relationship: RelationshipListItem) => {
    setState(prev => ({ ...prev, rightPanelOpen: true, loading: true }));
    
    try {
      const detail = await relationshipService.getRelationshipDetail(relationship.relationship_id);
      setState(prev => ({
        ...prev,
        selectedRelationship: detail,
        loading: false
      }));
    } catch (error) {
      console.error('Failed to load relationship details:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load relationship details'
      }));
    }
  }, []);

  // Handle table state changes
  const handleTableStateChange = useCallback((updates: Partial<RelationshipTableState>) => {
    setState(prev => ({
      ...prev,
      tableState: { ...prev.tableState, ...updates }
    }));
  }, []);

  // Handle relationship updates
  const handleRelationshipUpdate = useCallback(async (updatedRelationship: RelationshipDetail) => {
    // Update the selected relationship
    setState(prev => ({
      ...prev,
      selectedRelationship: updatedRelationship
    }));
    
    // Update the relationship in the list
    setState(prev => ({
      ...prev,
      relationships: prev.relationships.map(rel =>
        rel.relationship_id === updatedRelationship.relationship_id
          ? {
              ...rel,
              relationship_status: updatedRelationship.relationship_status,
              loyalty_status: updatedRelationship.loyalty_status,
              lead_score: updatedRelationship.lead_score,
              next_steps: updatedRelationship.next_steps,
              engagement_frequency: updatedRelationship.engagement_frequency
            }
          : rel
      )
    }));
  }, []);

  // Handle bulk operations
  const handleBulkUpdate = useCallback(async (selectedIds: Set<string>, updates: any) => {
    try {
      const response = await relationshipService.bulkUpdateRelationships({
        relationship_ids: Array.from(selectedIds),
        updates
      });
      
      // Reload relationships to get updated data
      await loadRelationships();
      
      // Clear selection
      setState(prev => ({
        ...prev,
        tableState: { ...prev.tableState, selectedIds: new Set() }
      }));
      
      // Show success message (would use a toast/notification system)
      console.log(`Successfully updated ${response.updated_count} relationships`);
    } catch (error) {
      console.error('Failed to update relationships:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to update relationships'
      }));
    }
  }, []);

  // Toggle right panel
  const toggleRightPanel = useCallback(() => {
    setState(prev => ({ ...prev, rightPanelOpen: !prev.rightPanelOpen }));
  }, []);

  // Close right panel
  const closeRightPanel = useCallback(() => {
    setState(prev => ({
      ...prev,
      rightPanelOpen: false,
      selectedRelationship: undefined
    }));
  }, []);

  return (
    <div className="relationship-manager">
      {/* Main Header */}
      <div className="relationship-manager__header">
        <div className="relationship-manager__header-title">
          <h1>Relationship Manager</h1>
          <p className="relationship-manager__header-subtitle">
            Manage physician and provider relationships
          </p>
        </div>
        <div className="relationship-manager__header-controls">
          <button 
            className="relationship-manager__toggle-button"
            onClick={() => setShowFilters(!showFilters)}
            title={showFilters ? 'Hide Filters' : 'Show Filters'}
          >
            <span className="icon">🔍</span>
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
          <button 
            className="relationship-manager__toggle-button"
            onClick={() => setShowDetails(!showDetails)}
            title={showDetails ? 'Hide Details' : 'Show Details'}
          >
            <span className="icon">📋</span>
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
      </div>

      <div className="relationship-manager__content">
        {/* Left Panel - Filters */}
        {showFilters && (
          <div className="relationship-manager__left-panel">
            <div className="relationship-manager__panel-header">
              <h3>Filters</h3>
            </div>
            {state.filterOptions && (
              <RelationshipFiltersComponent
                filters={state.filters}
                filterOptions={state.filterOptions}
                onChange={handleFilterChange}
              />
            )}
          </div>
        )}

        {/* Middle Panel - Relationship List */}
        <div className="relationship-manager__middle-panel">
          <div className="relationship-manager__panel-header">
            <h2>Relationships</h2>
            <div className="relationship-manager__actions">
              {/* Export button - commented out until backend implementation
              <button 
                className="btn btn-primary"
                onClick={() => relationshipService.downloadExport(state.filters)}
              >
                Export
              </button>
              */}
            </div>
          </div>
        
        {state.error && (
          <div className="relationship-manager__error">
            {state.error}
          </div>
        )}
        
        <RelationshipList
          relationships={state.relationships}
          tableState={state.tableState}
          loading={state.loading}
          onRelationshipSelect={handleRelationshipSelect}
          onTableStateChange={handleTableStateChange}
          onBulkUpdate={handleBulkUpdate}
          filterOptions={state.filterOptions}
        />
        </div>

        {/* Right Panel - Details/Actions */}
        {showDetails && (
          <div className="relationship-manager__right-panel open">
            {state.selectedRelationship ? (
              <>
                <div className="relationship-manager__panel-header">
                  <h3>{state.selectedRelationship.entity_name}</h3>
                  <button 
                    className="close-button"
                    onClick={closeRightPanel}
                    aria-label="Close panel"
                  >
                    ×
                  </button>
                </div>
                
                <RelationshipDetailComponent
                  relationship={state.selectedRelationship}
                  onUpdate={handleRelationshipUpdate}
                  onClose={closeRightPanel}
                />
              </>
            ) : (
              <div className="relationship-manager__empty-state">
                <div className="relationship-manager__empty-icon">👥</div>
                <h3>No Relationship Selected</h3>
                <p>Select a relationship from the list to view details, activities, and campaigns.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default RelationshipManager;