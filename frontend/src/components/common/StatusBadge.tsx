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
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3 py-1.5 gap-2 font-medium',
  }[size];

  if (status) {
    switch (status) {
      case 'completed':
        return (
          <span className={`inline-flex items-center rounded-full bg-emerald-950/40 text-emerald-300 border border-emerald-700/50 shadow-sm ${sizeClasses}`}>
            {showIcon && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
            <span>Completed</span>
          </span>
        );
      case 'running':
        return (
          <span className={`inline-flex items-center rounded-full bg-sky-950/50 text-icy-300 border border-sky-600/50 shadow-glow-cyan/20 ${sizeClasses}`}>
            {showIcon && <PlayCircle className="w-3.5 h-3.5 text-icy-300 animate-spin" />}
            <span>Running</span>
          </span>
        );
      case 'paused_for_approval':
        return (
          <span className={`inline-flex items-center rounded-full bg-amber-950/40 text-amber-300 border border-amber-600/60 shadow-glow-amber/20 ${sizeClasses}`}>
            {showIcon && <PauseCircle className="w-3.5 h-3.5 text-amber-400" />}
            <span>Awaiting Approval</span>
          </span>
        );
      case 'failed':
        return (
          <span className={`inline-flex items-center rounded-full bg-rose-950/40 text-rose-300 border border-rose-700/60 ${sizeClasses}`}>
            {showIcon && <AlertCircle className="w-3.5 h-3.5 text-rose-400" />}
            <span>Failed</span>
          </span>
        );
      case 'cancelled':
        return (
          <span className={`inline-flex items-center rounded-full bg-graphite-800/80 text-mist-400 border border-white/[0.08] ${sizeClasses}`}>
            {showIcon && <XCircle className="w-3.5 h-3.5 text-mist-500" />}
            <span>Cancelled</span>
          </span>
        );
      case 'pending':
      default:
        return (
          <span className={`inline-flex items-center rounded-full bg-graphite-900/80 text-mist-400 border border-white/[0.06] ${sizeClasses}`}>
            {showIcon && <Clock className="w-3.5 h-3.5 text-mist-500" />}
            <span>Queued</span>
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
      <span className={`inline-flex items-center rounded-md bg-steel-900/70 text-mist-200 border border-white/[0.08] font-mono text-[11px] ${sizeClasses}`}>
        {showIcon && <Cpu className="w-3 h-3 text-icy-400" />}
        <span>{formattedPhase}</span>
      </span>
    );
  }

  return null;
};

