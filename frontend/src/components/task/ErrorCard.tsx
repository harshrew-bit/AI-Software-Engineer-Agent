import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';
import type { WorkflowPhase } from '../../types/task';

interface ErrorCardProps {
  errorMessage: string | null | undefined;
  lastPhase?: WorkflowPhase;
  onRetry?: () => void;
}

export const ErrorCard: React.FC<ErrorCardProps> = ({
  errorMessage,
  lastPhase,
  onRetry,
}) => {
  return (
    <div className="rounded-xl border border-rose-600/50 bg-[#160b0e]/85 p-6 shadow-2xl backdrop-blur-xl relative overflow-hidden ring-1 ring-rose-500/20">
      {/* Top subtle crimson highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-rose-500/40 to-transparent pointer-events-none" />

      <div className="flex items-start gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 flex-shrink-0 shadow-sm">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h3 className="text-sm md:text-base font-bold text-white tracking-tight">
              Task Execution Interrupted
            </h3>
            {lastPhase && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-700/60 self-start sm:self-auto">
                Terminated Phase: {lastPhase}
              </span>
            )}
          </div>
          <p className="text-xs text-rose-200/80 mt-1 font-sans">
            The autonomous LangGraph engine encountered an unhandled exception or reached maximum failure retries.
          </p>

          <div className="mt-3 p-3.5 rounded-lg bg-[#070a11] border border-rose-900/60 text-xs font-mono text-rose-300 whitespace-pre-wrap leading-relaxed select-text shadow-inner-glow max-h-60 overflow-y-auto">
            {errorMessage || 'Unknown error occurred during task execution.'}
          </div>

          {onRetry && (
            <div className="mt-4 flex justify-end">
              <button
                onClick={onRetry}
                className="px-4 py-2 rounded-lg bg-rose-700 hover:bg-rose-600 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-lg shadow-rose-950/60 border border-rose-500/30"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Return to Workspace</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
