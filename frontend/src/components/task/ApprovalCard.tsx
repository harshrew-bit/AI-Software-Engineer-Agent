import React, { useState } from 'react';
import { ShieldAlert, Check, X, Loader2 } from 'lucide-react';
import { CodeBlock } from '../common/CodeBlock';
import type { PendingApproval } from '../../types/task';

interface ApprovalCardProps {
  approval: PendingApproval;
  onSubmitDecision: (approvalId: string, approved: boolean, feedback?: string) => Promise<void>;
  actionLoading?: boolean;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  approval,
  onSubmitDecision,
  actionLoading = false,
}) => {
  const [feedback, setFeedback] = useState<string>('');
  const [localSubmitting, setLocalSubmitting] = useState<boolean>(false);

  const approvalId = approval.approval_id || approval.id || `appr_${approval.tool_name}`;

  const handleDecision = async (approved: boolean) => {
    setLocalSubmitting(true);
    try {
      await onSubmitDecision(approvalId, approved, feedback.trim() || undefined);
    } catch (err) {
      console.error('Approval submission error:', err);
    } finally {
      setLocalSubmitting(false);
    }
  };

  const isBusy = actionLoading || localSubmitting;

  return (
    <div className="rounded-xl border-2 border-amber-500/80 bg-amber-950/30 p-6 shadow-2xl backdrop-blur-md relative overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-amber-800/60">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 flex-shrink-0">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">
                Human Approval Required
              </h3>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-900/60 text-amber-300 border border-amber-700/60">
                Action: {approval.tool_name}
              </span>
            </div>
            <p className="text-xs text-amber-200/80 mt-0.5">
              The agent has reached a safety checkpoint for a potentially destructive or external action.
            </p>
          </div>
        </div>

        <div className="text-xs font-mono text-amber-400/80">
          ID: {approvalId}
        </div>
      </div>

      <div className="mt-4 space-y-4">
        <div>
          <span className="text-[11px] font-semibold text-amber-300 uppercase tracking-wider block mb-1">
            Reason / Safety Assessment
          </span>
          <p className="text-xs text-slate-200 bg-[#070b14]/90 p-3 rounded-lg border border-slate-800 leading-relaxed font-sans">
            {approval.reason || `Action '${approval.tool_name}' requires human approval before proceeding.`}
          </p>
        </div>

        {approval.payload && Object.keys(approval.payload).length > 0 && (
          <div>
            <span className="text-[11px] font-semibold text-amber-300 uppercase tracking-wider block mb-1 font-mono">
              Action Payload / Parameters
            </span>
            <CodeBlock
              code={approval.payload}
              language="json"
              maxHeight="max-h-48"
            />
          </div>
        )}

        <div>
          <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Reviewer Feedback / Guidance (Optional)
          </label>
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Provide optional corrective guidance to the agent if rejecting or modifying..."
            disabled={isBusy}
            className="w-full px-3.5 py-2 bg-[#070b14] border border-slate-700/80 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-sans"
          />
        </div>

        <div className="pt-2 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => handleDecision(false)}
            disabled={isBusy}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-rose-950 hover:text-rose-300 hover:border-rose-800 border border-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {isBusy ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <X className="w-3.5 h-3.5" />
            )}
            <span>Reject Action</span>
          </button>

          <button
            type="button"
            onClick={() => handleDecision(true)}
            disabled={isBusy}
            className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-950 transition-colors disabled:opacity-50"
          >
            {isBusy ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Check className="w-3.5 h-3.5" />
            )}
            <span>Approve & Continue</span>
          </button>
        </div>
      </div>
    </div>
  );
};
