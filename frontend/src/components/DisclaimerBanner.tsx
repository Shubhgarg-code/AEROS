import React from 'react';
import { Info } from 'lucide-react';

interface DisclaimerBannerProps {
  type?: 'scenario' | 'observation' | 'uncertainty';
  customMessage?: string;
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({
  type = 'scenario',
  customMessage,
}) => {
  const messages = {
    scenario:
      'Scenario models represent estimated atmospheric responses under hypothetical emission controls, rather than guaranteed outcomes.',
    observation:
      'Continuous observations are sourced directly from Central Pollution Control Board (CPCB) monitoring stations. Unmonitored coordinates are spatial model estimates.',
    uncertainty:
      'Prediction intervals reflect 90% calibrated uncertainty bounds based on empirical post-Diwali validation datasets.',
  };

  const message = customMessage || messages[type];

  return (
    <div className="flex items-center gap-3 rounded-lg border border-[#EDE7D9] bg-[#FAF8F3] px-4 py-2.5 text-xs text-[#6B5A42] shadow-[0_1px_2px_rgba(0,0,0,0.01)]">
      <Info className="h-4 w-4 shrink-0 text-[#8C7351]" />
      <span className="leading-relaxed font-sans">{message}</span>
    </div>
  );
};
