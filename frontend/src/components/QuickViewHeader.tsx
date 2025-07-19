import React from 'react';

interface QuickViewHeaderProps {
  siteName: string;
  onClose: () => void;
}

const QuickViewHeader: React.FC<QuickViewHeaderProps> = ({ siteName, onClose }) => {
  return (
    <div style={{
      backgroundColor: '#3498db',
      color: 'white',
      padding: '12px 16px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderBottom: '2px solid #2980b9',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div>
        <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '2px' }}>
          QUICK VIEW MODE
        </div>
        <div style={{ fontSize: '16px', fontWeight: '500' }}>
          {siteName}
        </div>
        <div style={{ fontSize: '12px', opacity: 0.9, marginTop: '2px' }}>
          Showing all providers at this location
        </div>
      </div>
      
      <button
        onClick={onClose}
        style={{
          background: 'rgba(255, 255, 255, 0.2)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          color: 'white',
          padding: '6px 12px',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '500',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}
        onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)'}
        onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'}
      >
        <span style={{ fontSize: '16px' }}>×</span>
        Clear Quick View
      </button>
    </div>
  );
};

export default QuickViewHeader;