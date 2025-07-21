import React from 'react';
import { ViewMode } from '../types/claims';
import './ViewModeSelector.css';

interface ViewModeSelectorProps {
  currentMode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
}

const ViewModeSelector: React.FC<ViewModeSelectorProps> = ({
  currentMode,
  onModeChange,
}) => {
  const modes: Array<{ value: ViewMode; label: string; icon: string; description: string }> = [
    {
      value: 'sites',
      label: 'Sites',
      icon: '🏥',
      description: 'Sites of Service'
    },
    {
      value: 'providers',
      label: 'Providers',
      icon: '👨‍⚕️',
      description: 'Healthcare Providers'
    },
    {
      value: 'groups',
      label: 'Groups',
      icon: '🏢',
      description: 'Provider Groups'
    },
  ];

  return (
    <div className="view-mode-selector">
      <div className="mode-buttons">
        {modes.map((mode) => (
          <button
            key={mode.value}
            className={`mode-button ${currentMode === mode.value ? 'active' : ''}`}
            onClick={() => onModeChange(mode.value)}
            title={mode.description}
          >
            <span className="mode-icon">{mode.icon}</span>
            <span className="mode-label">{mode.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ViewModeSelector;