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
    <div className="rounded-xl border border-amber-500/50 bg-[#161208]/85 p-6 shadow-2xl backdrop-blur-xl relative overflow-hidden ring-1 ring-amber-500/30">
      {/* Subtle top amber highlight beam */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-amber-400/50 to-transparent pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-amber-900/40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 flex-shrink-0 shadow-glow-amber/20">
            <ShieldAlert className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm md:text-base font-bold text-white tracking-tight">
                Human Approval Checkpoint
              </h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-700/60">
                Action: {approval.tool_name}
              </span>
            </div>
            <p className="text-xs text-amber-200/80 mt-0.5 font-sans">
              Autonomous execution paused. A critical operation requires human engineering sign-off.
            </p>
          </div>
        </div>

        <div className="text-[11px] font-mono text-amber-400/80 bg-amber-950/40 px-2 py-1 rounded border border-amber-900/40">
          ID: {approvalId}
        </div>
      </div>

      <div className="mt-4 space-y-4">
        <div>
          <span className="text-[10px] font-mono font-medium text-amber-300 uppercase tracking-widest block mb-1">
            Safety Assessment &amp; Reason
          </span>
          <div className="text-xs text-slate-100 bg-[#070a11] p-3 rounded-lg border border-white/[0.08] leading-relaxed font-sans shadow-inner-glow">
            {approval.reason || `Action '${approval.tool_name}' requires human approval before proceeding.`}
          </div>
        </div>

        {approval.payload && Object.keys(approval.payload).length > 0 && (
          <div>
            <span className="text-[10px] font-mono font-medium text-amber-300 uppercase tracking-widest block mb-1">
              Action Payload Parameters
            </span>
            <CodeBlock
              code={approval.payload}
              language="json"
              maxHeight="max-h-48"
              title="payload.json"
            />
          </div>
        )}

        <div>
          <label className="block text-[10px] font-mono font-medium text-mist-300 uppercase tracking-widest mb-1.5">
            Reviewer Guidance (Optional)
          </label>
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Provide optional corrective instructions to the agent..."
            disabled={isBusy}
            className="w-full px-3.5 py-2 bg-[#070a11] border border-white/[0.08] rounded-lg text-xs text-slate-100 placeholder-mist-600 focus:outline-none focus:border-amber-500 font-sans shadow-inner-glow"
          />
        </div>

        <div className="pt-2 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => handleDecision(false)}
            disabled={isBusy}
            className="px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-rose-950/80 hover:text-rose-300 hover:border-rose-800/80 border border-white/[0.08] text-mist-300 text-xs font-medium flex items-center gap-1.5 transition-all disabled:opacity-50 shadow-sm"
          >
            {isBusy ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <X className="w-3.5 h-3.5 text-rose-400" />
            )}
            <span>Reject Action</span>
          </button>

          <button
            type="button"
            onClick={() => handleDecision(true)}
            disabled={isBusy}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-950/60 border border-emerald-400/30 transition-all disabled:opacity-50"
          >
            {isBusy ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Check className="w-3.5 h-3.5" />
            )}
            <span>Approve &amp; Continue Run</span>
          </button>
        </div>
      </div>
    </div>
  );
};
