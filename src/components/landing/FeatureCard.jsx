import React, { useState } from 'react';
import Card from '../common/Card';

/**
 * Feature card component with interactive custom hover outlines.
 * Matches figma hover state highlights dynamically using inline styling.
 * 
 * @param {Object} props
 * @param {React.ReactNode|string} props.icon - Icon representation (Unicode/Emoji or Lucide icon component).
 * @param {string} props.title - Title of the feature.
 * @param {string} props.description - Detailed description.
 * @param {string} [props.color='#2563EB'] - Custom color highlight on hover.
 * @returns {JSX.Element}
 */
export const FeatureCard = ({ icon, title, description, color = '#2563EB' }) => {
  const [isHovered, setIsHovered] = useState(false);

  // Custom styling matching the Figma prototype hover overrides
  const cardStyle = {
    borderColor: isHovered ? `${color}40` : '#E2E8F0',
    transform: isHovered ? 'translateY(-4px)' : 'none',
    boxShadow: isHovered 
      ? `0 12px 32px ${color}20, 0 2px 8px rgba(0, 0, 0, 0.06)`
      : '0 2px 12px rgba(0, 0, 0, 0.05)',
  };

  const iconContainerStyle = {
    background: `${color}12`,
    color: color,
  };

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={cardStyle}
      className="bg-white rounded-2xl p-6 border transition-smooth cursor-default flex flex-col items-start text-left"
    >
      <div 
        style={iconContainerStyle}
        className="w-11 h-11 rounded-xl flex items-center justify-center text-lg mb-4 flex-shrink-0"
      >
        {icon}
      </div>
      <h3 className="text-[15px] font-bold text-slate-900 mb-2 tracking-tight">
        {title}
      </h3>
      <p className="text-xs sm:text-sm text-slate-500 leading-relaxed">
        {description}
      </p>
    </div>
  );
};

export default FeatureCard;
