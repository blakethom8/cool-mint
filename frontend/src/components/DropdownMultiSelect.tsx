import React, { useState, useRef, useEffect } from 'react';
import './DropdownMultiSelect.css';

interface DropdownMultiSelectProps {
  label: string;
  options: string[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  searchable?: boolean;
  maxHeight?: number;
  showSelectAll?: boolean;
}

const DropdownMultiSelect: React.FC<DropdownMultiSelectProps> = ({
  label,
  options,
  selectedValues,
  onChange,
  placeholder = 'Select...',
  searchable = true,
  maxHeight = 300,
  showSelectAll = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen, searchable]);

  const filteredOptions = searchTerm
    ? options.filter(option => 
        option.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setSearchTerm('');
    }
  };

  const handleOptionToggle = (option: string) => {
    const newValues = selectedValues.includes(option)
      ? selectedValues.filter(v => v !== option)
      : [...selectedValues, option];
    onChange(newValues);
  };

  const handleSelectAll = () => {
    if (selectedValues.length === options.length) {
      onChange([]);
    } else {
      onChange([...options]);
    }
  };

  const handleClear = () => {
    onChange([]);
    setSearchTerm('');
  };

  const getDisplayText = () => {
    if (selectedValues.length === 0) return placeholder;
    if (selectedValues.length === 1) return selectedValues[0];
    if (selectedValues.length === options.length) return `All ${label} (${selectedValues.length})`;
    return `${selectedValues.length} selected`;
  };

  return (
    <div className="dropdown-multi-select" ref={dropdownRef}>
      <label className="dropdown-label">{label}</label>
      
      <div 
        className={`dropdown-trigger ${isOpen ? 'open' : ''}`}
        onClick={handleToggle}
      >
        <span className="dropdown-value">{getDisplayText()}</span>
        <div className="dropdown-actions">
          {selectedValues.length > 0 && (
            <button
              className="clear-btn"
              onClick={(e) => {
                e.stopPropagation();
                handleClear();
              }}
              title="Clear selection"
            >
              ×
            </button>
          )}
          <span className="dropdown-arrow">▾</span>
        </div>
      </div>

      {isOpen && (
        <div className="dropdown-menu" style={{ maxHeight }}>
          {searchable && (
            <div className="dropdown-search">
              <input
                ref={searchInputRef}
                type="text"
                className="search-input"
                placeholder={`Search ${label.toLowerCase()}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}

          {showSelectAll && filteredOptions.length > 1 && (
            <div className="dropdown-option select-all" onClick={handleSelectAll}>
              <input
                type="checkbox"
                checked={selectedValues.length === options.length}
                onChange={() => {}}
                className="option-checkbox"
              />
              <span className="option-label">
                {selectedValues.length === options.length ? 'Deselect All' : 'Select All'}
              </span>
            </div>
          )}

          <div className="dropdown-options">
            {filteredOptions.length === 0 ? (
              <div className="no-options">No options found</div>
            ) : (
              filteredOptions.map(option => (
                <div
                  key={option}
                  className="dropdown-option"
                  onClick={() => handleOptionToggle(option)}
                >
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(option)}
                    onChange={() => {}}
                    className="option-checkbox"
                  />
                  <span className="option-label">{option}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DropdownMultiSelect;