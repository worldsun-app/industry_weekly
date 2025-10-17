import React, { useState } from 'react';
import './PeRatioBar.css';

interface PeRatioBarProps {
  pe_today: number | null | undefined;
  pe_low_1y: number | null | undefined;
  pe_high_1y: number | null | undefined;
}

const PeRatioBar: React.FC<PeRatioBarProps> = ({ pe_today, pe_low_1y, pe_high_1y }) => {
  const [showMinMax, setShowMinMax] = useState(false);

  if (pe_today == null || pe_low_1y == null || pe_high_1y == null || pe_high_1y === pe_low_1y) {
    return <div className="pe-ratio-bar-container text-muted">N/A</div>;
  }

  const percentage = ((pe_today - pe_low_1y) / (pe_high_1y - pe_low_1y)) * 100;
  // Clamp the percentage between 0 and 100
  const clampedPercentage = Math.max(0, Math.min(100, percentage));

  return (
    <div 
      className="pe-ratio-bar-container"
      onMouseEnter={() => setShowMinMax(true)}
      onMouseLeave={() => setShowMinMax(false)}
    >
      <div className="pe-bar-wrapper">
        <div className="pe-today-value" style={{ left: `${clampedPercentage}%` }}>
          {pe_today.toFixed(2)}
        </div>
        <div className="pe-bar">
          <div className="pe-bar-dot" style={{ left: `${clampedPercentage}%` }} />
        </div>
        <div className={`pe-bar-labels ${showMinMax ? 'visible' : ''}`}>
          <span>{pe_low_1y.toFixed(2)}</span>
          <span>{pe_high_1y.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};

export default PeRatioBar;
