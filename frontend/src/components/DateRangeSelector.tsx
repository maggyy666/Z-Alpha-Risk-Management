import React from 'react';
import './DateRangeSelector.css';

export type DateRange = 'YTD' | '1Y' | '3Y' | '5Y' | 'All';

interface DateRangeSelectorProps {
  selectedRange: DateRange;
  onRangeChange: (range: DateRange) => void;
}

const DateRangeSelector: React.FC<DateRangeSelectorProps> = ({
  selectedRange,
  onRangeChange
}) => {
  const ranges: DateRange[] = ['YTD', '1Y', '3Y', '5Y', 'All'];

  return (
    <div className="date-range-selector">
      <label className="date-range-label">Date Range:</label>
      <div className="range-buttons">
        {ranges.map((range) => (
          <button
            key={range}
            className={`range-button ${selectedRange === range ? 'active' : ''}`}
            onClick={() => onRangeChange(range)}
          >
            {range}
          </button>
        ))}
      </div>
    </div>
  );
};

export default DateRangeSelector; 