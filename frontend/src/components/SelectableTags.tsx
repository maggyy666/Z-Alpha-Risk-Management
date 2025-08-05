import React, { useState } from 'react';
import './SelectableTags.css';

interface SelectableTagsProps {
  title: string;
  selectedItems: string[];
  availableItems: string[];
  onSelectionChange: (items: string[]) => void;
  placeholder?: string;
}

const SelectableTags: React.FC<SelectableTagsProps> = ({
  title,
  selectedItems,
  availableItems,
  onSelectionChange,
  placeholder = "Add"
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const handleRemoveItem = (item: string) => {
    onSelectionChange(selectedItems.filter(i => i !== item));
  };

  const handleAddItem = (item: string) => {
    if (!selectedItems.includes(item)) {
      onSelectionChange([...selectedItems, item]);
    }
    setIsDropdownOpen(false);
  };

  const unselectedItems = availableItems.filter(item => !selectedItems.includes(item));

  return (
    <div className="selectable-tags">
      <label className="selectable-tags-label">{title}</label>
      <div className="input-field-container">
        <div className="selected-items-display">
          {selectedItems.map(item => (
            <span 
              key={item} 
              className="selected-item"
              onClick={() => handleRemoveItem(item)}
              style={{ cursor: 'pointer' }}
            >
              {item}
            </span>
          ))}
        </div>
        
        {unselectedItems.length > 0 && (
          <div className="dropdown-container">
            <button
              className="dropdown-toggle"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              aria-label="Add item"
            >
              <span className="gear-icon">⚙️</span>
              <span className="dropdown-arrow">▼</span>
            </button>

            {isDropdownOpen && (
              <div className="dropdown-menu">
                {unselectedItems.map(item => (
                  <button
                    key={item}
                    className="dropdown-item"
                    onClick={() => handleAddItem(item)}
                  >
                    {item}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SelectableTags; 