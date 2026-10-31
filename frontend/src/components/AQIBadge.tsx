import React from 'react';

interface AQIBadgeProps {
  aqi?: number;
  category?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const AQIBadge: React.FC<AQIBadgeProps> = ({ aqi, category, size = 'md' }) => {
  let cat = category;
  let colorClass = 'bg-[#F2F2EC] text-[#5A626A] border-[#E5E5DF]';
  let dotColor = 'bg-[#8C959D]';

  if (aqi !== undefined && !cat) {
    if (aqi <= 50) cat = 'Good';
    else if (aqi <= 100) cat = 'Satisfactory';
    else if (aqi <= 200) cat = 'Moderate';
    else if (aqi <= 300) cat = 'Poor';
    else if (aqi <= 400) cat = 'Very Poor';
    else cat = 'Severe';
  }

  switch (cat?.toLowerCase()) {
    case 'good':
      colorClass = 'bg-[#EAF4F1] text-[#285D52] border-[#CDE5DF]';
      dotColor = 'bg-[#3D8B7A]';
      break;
    case 'satisfactory':
      colorClass = 'bg-[#F0F6EB] text-[#476C32] border-[#D6E7CD]';
      dotColor = 'bg-[#6B9E4E]';
      break;
    case 'moderate':
      colorClass = 'bg-[#FDF6E9] text-[#865914] border-[#F5E2BE]';
      dotColor = 'bg-[#C48A2C]';
      break;
    case 'poor':
      colorClass = 'bg-[#FDF1EB] text-[#8C431F] border-[#F6D0BE]';
      dotColor = 'bg-[#C26738]';
      break;
    case 'very poor':
      colorClass = 'bg-[#FCEEEE] text-[#8A2424] border-[#F5C2C2]';
      dotColor = 'bg-[#B83E3E]';
      break;
    case 'severe':
      colorClass = 'bg-[#F9EAEF] text-[#631427] border-[#ECC0CE]';
      dotColor = 'bg-[#7A2338]';
      break;
  }

  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 gap-1.5',
    md: 'text-xs px-2.5 py-1 gap-2',
    lg: 'text-sm px-3.5 py-1.5 gap-2.5 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border font-sans tracking-tight font-medium ${sizeClasses[size]} ${colorClass}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{cat || 'Unknown'}</span>
      {aqi !== undefined && <span className="font-mono opacity-80">({aqi})</span>}
    </span>
  );
};
