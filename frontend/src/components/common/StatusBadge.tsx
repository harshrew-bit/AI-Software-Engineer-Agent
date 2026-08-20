import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  PauseCircle,
  XCircle,
  PlayCircle,
  Cpu,
} from 'lucide-react';
import type { TaskStatus, WorkflowPhase } from '../../types/task';

interface StatusBadgeProps {
  status?: TaskStatus;
  phase?: WorkflowPhase;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  phase,
  size = 'md',
  showIcon = true,
}) => {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3 py-1.5 gap-2 font-medium',
  }[size];

  if (status) {
    switch (status) {
      case 'completed':
        return (
          <span className={`inline-flex items-center rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 ${sizeClasses}`}>
            {showIcon && <CheckCircle2 className="w-3.5 h-3.5" />}
            Completed
          </span>
        );
      case 'running':
        return (
          <span className={`inline-flex items-center rounded-full bg-primary-950/80 text-primary-300 border border-primary-800/80 ${sizeClasses}`}>
            {showIcon && <PlayCircle className="w-3.5 h-3.5 animate-spin" />}
            Running
          </span>
        );
      case 'paused_for_approval':
        return (
          <span className={`inline-flex items-center rounded-full bg-amber-950/80 text-amber-300 border border-amber-800/80 ${sizeClasses}`}>
            {showIcon && <PauseCircle className="w-3.5 h-3.5" />}
            Paused for Approval
          </span>
        );
      case 'failed':
        return (
          <span className={`inline-flex items-center rounded-full bg-rose-950/80 text-rose-300 border border-rose-800/80 ${sizeClasses}`}>
            {showIcon && <AlertCircle className="w-3.5 h-3.5" />}
            Failed
          </span>
        );
      case 'cancelled':
        return (
          <span className={`inline-flex items-center rounded-full bg-slate-800 text-slate-400 border border-slate-700 ${sizeClasses}`}>
            {showIcon && <XCircle className="w-3.5 h-3.5" />}
            Cancelled
          </span>
        );
      case 'pending':
      default:
        return (
          <span className={`inline-flex items-center rounded-full bg-slate-900 text-slate-400 border border-slate-800 ${sizeClasses}`}>
            {showIcon && <Clock className="w-3.5 h-3.5" />}
            Pending
          </span>
        );
    }
  }

  if (phase) {
    const formattedPhase = phase
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');

    return (
      <span className={`inline-flex items-center rounded-md bg-slate-800/90 text-slate-300 border border-slate-700/80 font-mono ${sizeClasses}`}>
        {showIcon && <Cpu className="w-3.5 h-3.5 text-primary-400" />}
        {formattedPhase}
      </span>
    );
  }

  return null;
};
