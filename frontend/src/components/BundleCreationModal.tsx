import React, { useState, useEffect } from 'react';
import { bundleService } from '../services/bundleService';
import { BundleStatsResponse } from '../types/bundle';
import './BundleCreationModal.css';

interface BundleCreationModalProps {
  isOpen: boolean;
  selectedActivityIds: string[];
  onClose: () => void;
  onSuccess: (bundleId: string) => void;
}

export const BundleCreationModal: React.FC<BundleCreationModalProps> = ({
  isOpen,
  selectedActivityIds,
  onClose,
  onSuccess,
}) => {
  const [bundleName, setBundleName] = useState('');
  const [bundleDescription, setBundleDescription] = useState('');
  const [stats, setStats] = useState<BundleStatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && selectedActivityIds.length > 0) {
      fetchStats();
    }
  }, [isOpen, selectedActivityIds]);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const statsData = await bundleService.getBundleStats(selectedActivityIds);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to fetch bundle stats:', err);
      setError('Failed to load activity statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!bundleName.trim()) {
      setError('Please enter a bundle name');
      return;
    }

    setCreating(true);
    setError(null);
    try {
      const response = await bundleService.createBundle(
        selectedActivityIds,
        bundleName,
        bundleDescription || undefined
      );
      
      if (response.bundle_id) {
        onSuccess(response.bundle_id);
      }
    } catch (err) {
      console.error('Failed to create bundle:', err);
      setError('Failed to create bundle');
    } finally {
      setCreating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create Activity Bundle</h2>
          <button className="close-button" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading">Loading activity statistics...</div>
          ) : stats ? (
            <>
              <div className="stats-section">
                <h3>Bundle Statistics</h3>
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-label">Activities</div>
                    <div className="stat-value">{stats.activity_count}</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-label">Estimated Tokens</div>
                    <div className="stat-value">{stats.estimated_tokens.toLocaleString()}</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-label">Characters</div>
                    <div className="stat-value">{stats.total_characters.toLocaleString()}</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-label">Unique Owners</div>
                    <div className="stat-value">{stats.unique_owners.length}</div>
                  </div>
                </div>

                {stats.date_range.start && stats.date_range.end && (
                  <div className="date-range">
                    <strong>Date Range:</strong> {stats.date_range.start} to {stats.date_range.end}
                  </div>
                )}

                {Object.keys(stats.activity_types).length > 0 && (
                  <div className="activity-types">
                    <strong>Activity Types:</strong>
                    <div className="type-list">
                      {Object.entries(stats.activity_types).map(([type, count]) => (
                        <span key={type} className="type-badge">
                          {type}: {count as number}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="form-section">
                <div className="form-group">
                  <label htmlFor="bundle-name">Bundle Name*</label>
                  <input
                    id="bundle-name"
                    type="text"
                    value={bundleName}
                    onChange={(e) => setBundleName(e.target.value)}
                    placeholder="e.g., Sleep Related Activities Q1 2025"
                    maxLength={255}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="bundle-description">Description (Optional)</label>
                  <textarea
                    id="bundle-description"
                    value={bundleDescription}
                    onChange={(e) => setBundleDescription(e.target.value)}
                    placeholder="Describe what this bundle contains or why it was created..."
                    rows={3}
                  />
                </div>
              </div>
            </>
          ) : null}

          {error && <div className="error-message">{error}</div>}
        </div>

        <div className="modal-footer">
          <button className="cancel-button" onClick={onClose} disabled={creating}>
            Cancel
          </button>
          <button
            className="create-button"
            onClick={handleCreate}
            disabled={creating || loading || !bundleName.trim()}
          >
            {creating ? 'Creating...' : 'Create Bundle'}
          </button>
        </div>
      </div>
    </div>
  );
};