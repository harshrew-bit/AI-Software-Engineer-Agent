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
    <div className="rounded-xl border-2 border-rose-600/80 bg-rose-950/30 p-6 shadow-2xl backdrop-blur-md">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400 flex-shrink-0">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">
              Task Execution Failed
            </h3>
            {lastPhase && (
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-900/60 text-rose-300 border border-rose-700/60">
                Failed at: {lastPhase}
              </span>
            )}
          </div>
          <p className="text-xs text-rose-200/80 mt-1">
            The autonomous workflow was interrupted. Details and logs below:
          </p>

          <div className="mt-3 p-3.5 rounded-lg bg-[#070b14]/90 border border-rose-900/80 text-xs font-mono text-rose-300 whitespace-pre-wrap leading-relaxed select-text">
            {errorMessage || 'Unknown error occurred during execution.'}
          </div>

          {onRetry && (
            <div className="mt-4 flex justify-end">
              <button
                onClick={onRetry}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-rose-950"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Relaunch Task</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
