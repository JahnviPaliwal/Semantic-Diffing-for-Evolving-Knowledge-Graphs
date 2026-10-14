import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingSpinner: React.FC<{ message?: string; className?: string }> = ({
  message = 'Loading data...',
  className = 'py-16',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
      <p className="text-sm text-slate-400 font-medium tracking-wide">{message}</p>
    </div>
  );
};
