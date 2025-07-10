import React, { useState, useEffect } from 'react';
import { Bundle, BundleListResponse } from '../types/bundle';
import { bundleService } from '../services/bundleService';
import './BundleList.css';

interface BundleListProps {
  selectedBundleId?: string;
  onBundleSelect: (bundle: Bundle) => void;
  onBundleDelete?: (bundleId: string) => void;
}

export const BundleList: React.FC<BundleListProps> = ({
  selectedBundleId,
  onBundleSelect,
  onBundleDelete,
}) => {
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [sortBy, setSortBy] = useState<'created_at' | 'name' | 'activity_count'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    loadBundles();
  }, [currentPage, searchTerm, sortBy, sortOrder]);

  const loadBundles = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await bundleService.listBundles(
        currentPage,
        50,
        searchTerm || undefined,
        sortBy,
        sortOrder
      );
      setBundles(response.bundles);
      setTotalPages(response.total_pages);
      setTotalCount(response.total_count);
    } catch (err) {
      setError('Failed to load bundles');
      console.error('Error loading bundles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, bundleId: string) => {
    e.stopPropagation(); // Prevent bundle selection
    if (!window.confirm('Are you sure you want to delete this bundle? This will also delete all associated conversations.')) {
      return;
    }

    try {
      await bundleService.deleteBundle(bundleId);
      await loadBundles(); // Reload the list
      if (onBundleDelete) {
        onBundleDelete(bundleId);
      }
    } catch (err) {
      console.error('Error deleting bundle:', err);
      alert('Failed to delete bundle');
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1); // Reset to first page on search
  };

  const handleSortChange = (newSortBy: typeof sortBy) => {
    if (newSortBy === sortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
    setCurrentPage(1);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading && bundles.length === 0) {
    return <div className="bundle-list-loading">Loading bundles...</div>;
  }

  return (
    <div className="bundle-list">
      <div className="bundle-list-header">
        <h2>Activity Bundles</h2>
        <div className="bundle-count">{totalCount} bundles</div>
      </div>

      <div className="bundle-list-controls">
        <input
          type="text"
          className="bundle-search"
          placeholder="Search bundles..."
          value={searchTerm}
          onChange={handleSearchChange}
        />
        
        <div className="bundle-sort">
          <label>Sort by:</label>
          <select 
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortBy(field as typeof sortBy);
              setSortOrder(order as typeof sortOrder);
            }}
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="name-asc">Name (A-Z)</option>
            <option value="name-desc">Name (Z-A)</option>
            <option value="activity_count-desc">Most Activities</option>
            <option value="activity_count-asc">Least Activities</option>
          </select>
        </div>
      </div>

      {error && <div className="bundle-list-error">{error}</div>}

      <div className="bundle-list-items">
        {bundles.length === 0 ? (
          <div className="bundle-list-empty">
            {searchTerm ? 'No bundles found matching your search.' : 'No bundles created yet.'}
          </div>
        ) : (
          bundles.map((bundle) => (
            <div
              key={bundle.id}
              className={`bundle-item ${selectedBundleId === bundle.id ? 'selected' : ''}`}
              onClick={() => onBundleSelect(bundle)}
            >
              <div className="bundle-item-header">
                <h3 className="bundle-name">{bundle.name}</h3>
                <button
                  className="bundle-delete-btn"
                  onClick={(e) => handleDelete(e, bundle.id)}
                  title="Delete bundle"
                >
                  🗑️
                </button>
              </div>
              
              {bundle.description && (
                <p className="bundle-description">{bundle.description}</p>
              )}
              
              <div className="bundle-meta">
                <span className="bundle-activity-count">
                  {bundle.activity_count} activities
                </span>
                <span className="bundle-token-count">
                  ~{bundle.token_count?.toLocaleString() || '?'} tokens
                </span>
                {bundle.conversation_count > 0 && (
                  <span className="bundle-conversation-count">
                    {bundle.conversation_count} conversations
                  </span>
                )}
              </div>
              
              <div className="bundle-date">
                {formatDate(bundle.created_at)}
              </div>
            </div>
          ))
        )}
      </div>

      {totalPages > 1 && (
        <div className="bundle-list-pagination">
          <button
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};