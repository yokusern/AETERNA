import React from 'react';

interface ProgressBarProps {
  percentage: number;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ 
  percentage, 
  className = "w-full bg-gray-200 rounded-full h-2"
}) => {
  const clampedPercentage = Math.min(Math.max(percentage, 0), 100);
  
  return (
    <div className={className}>
      <div 
        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
        style={{ width: `${clampedPercentage}%` }}
        role="progressbar"
        aria-valuenow={clampedPercentage}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
};
