import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ActivityTable } from './components/ActivityTable';
import { ActivityFilters } from './components/ActivityFilters';
import { BundleCreationModal } from './components/BundleCreationModal';
import { BundleManagement } from './pages/BundleManagement';
import { activityService } from './services/activityService';
import { ActivityListItem, ActivityFilters as IActivityFilters, FilterOptions } from './types/activity';
import './App.css';

function ActivitySelector() {
  const [activities, setActivities] = useState<ActivityListItem[]>([]);
  const [selectedActivityIds, setSelectedActivityIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [filters, setFilters] = useState<IActivityFilters>({});
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showBundleModal, setShowBundleModal] = useState(false);

  // Fetch filter options on mount
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const options = await activityService.getFilterOptions();
        setFilterOptions(options);
      } catch (err) {
        console.error('Failed to fetch filter options:', err);
      }
    };
    fetchFilterOptions();
  }, []);

  // Fetch activities
  const fetchActivities = useCallback(async () => {
    console.log('🔍 Fetching activities with filters:', filters);
    setLoading(true);
    setError(null);
    try {
      const response = await activityService.getActivities(
        currentPage,
        pageSize,
        filters,
        'activity_date',
        'desc'
      );
      console.log('✅ API Response:', { 
        total_count: response.total_count, 
        activities_count: response.activities.length,
        first_activity: response.activities[0]?.subject 
      });
      setActivities(response.activities);
      setTotalCount(response.total_count);
    } catch (err) {
      console.error('❌ Failed to fetch activities:', err);
      setError('Failed to fetch activities');
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, filters]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  const handleFilterChange = (newFilters: IActivityFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleSelectionChange = (activityId: string, isSelected: boolean) => {
    setSelectedActivityIds(prev => {
      const newSet = new Set(prev);
      if (isSelected) {
        newSet.add(activityId);
      } else {
        newSet.delete(activityId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (isSelected: boolean) => {
    if (isSelected) {
      const allIds = new Set(activities.map(a => a.activity_id));
      setSelectedActivityIds(allIds);
    } else {
      setSelectedActivityIds(new Set());
    }
  };

  const handleProcessSelection = async () => {
    if (selectedActivityIds.size === 0) {
      alert('Please select at least one activity');
      return;
    }

    setShowBundleModal(true);
  };

  const handleBundleSuccess = (bundleId: string) => {
    setShowBundleModal(false);
    setSelectedActivityIds(new Set());
    // Navigate to bundle management page
    window.location.href = `/bundles`;
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Activity Selector</h1>
        <p>Select activities to share with the large language model</p>
      </header>

      <div className="app-content">
        <aside className={`filters-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <div className="sidebar-header">
            <h2>Filters</h2>
            <button 
              className="collapse-button"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              aria-label={sidebarCollapsed ? 'Expand filters' : 'Collapse filters'}
            >
              {sidebarCollapsed ? '▶' : '◀'}
            </button>
          </div>
          {!sidebarCollapsed && filterOptions && (
            <ActivityFilters
              filters={filters}
              filterOptions={filterOptions}
              onFilterChange={handleFilterChange}
            />
          )}
        </aside>
        
        {sidebarCollapsed && (
          <div className="collapsed-sidebar-indicator">
            <button 
              className="expand-button"
              onClick={() => setSidebarCollapsed(false)}
              aria-label="Expand filters"
            >
              ⚙️
            </button>
          </div>
        )}

        <main className="main-content">
          <div className="actions-bar">
            <div className="selection-info">
              {selectedActivityIds.size} activities selected
            </div>
            <button 
              className="process-button"
              onClick={handleProcessSelection}
              disabled={selectedActivityIds.size === 0}
            >
              Create Bundle
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          {loading ? (
            <div className="loading">Loading activities...</div>
          ) : (
            <ActivityTable
              activities={activities}
              selectedActivityIds={selectedActivityIds}
              onSelectionChange={handleSelectionChange}
              onSelectAll={handleSelectAll}
              currentPage={currentPage}
              totalPages={Math.ceil(totalCount / pageSize)}
              onPageChange={setCurrentPage}
            />
          )}
        </main>
      </div>

      <BundleCreationModal
        isOpen={showBundleModal}
        selectedActivityIds={Array.from(selectedActivityIds)}
        onClose={() => setShowBundleModal(false)}
        onSuccess={handleBundleSuccess}
      />
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ActivitySelector />} />
        <Route path="/bundles" element={<BundleManagement />} />
        <Route path="/bundles/:bundleId" element={<BundleManagement />} />
      </Routes>
    </Router>
  );
}

export default App;