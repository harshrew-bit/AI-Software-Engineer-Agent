import React, { useState } from 'react';
import {
  GitFork,
  GitBranch,
  GitPullRequest,
  ExternalLink,
  Ban,
  Clock,
  RotateCw,
  Copy,
  Check,
  Terminal,
} from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import type { TaskDetailResponse } from '../../types/task';

interface TaskHeaderProps {
  task: TaskDetailResponse;
  onRefresh: () => void;
  onCancel: () => void;
  actionLoading?: boolean;
}

export const TaskHeader: React.FC<TaskHeaderProps> = ({
  task,
  onRefresh,
  onCancel,
  actionLoading = false,
}) => {
  const [copiedId, setCopiedId] = useState<boolean>(false);
  const isRunning = task.status === 'running' || task.status === 'pending';

  const copyTaskId = async () => {
    try {
      await navigator.clipboard.writeText(task.id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    } catch (err) {
      console.error('Failed to copy task ID:', err);
    }
  };

  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      {/* Top subtle highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-icy-400/30 to-transparent pointer-events-none" />

      {/* Top Bar: Task ID, Status & Primary Actions */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-white/[0.06]">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 bg-[#070a11] px-2.5 py-1 rounded-lg border border-white/[0.08]">
            <Terminal className="w-3.5 h-3.5 text-icy-400" />
            <span className="font-mono text-xs md:text-sm font-bold text-icy-300">
              {task.id}
            </span>
            <button
              onClick={copyTaskId}
              className="p-1 text-mist-500 hover:text-white transition-colors"
              title="Copy Task ID"
            >
              {copiedId ? (
                <Check className="w-3 h-3 text-emerald-400" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </button>
          </div>

          <StatusBadge status={task.status} size="md" />
          <StatusBadge phase={task.current_phase} size="md" />

          {task.retry_count > 0 && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-700/50">
              Retry Cycle #{task.retry_count}
            </span>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {task.pull_request_url && (
            <a
              href={task.pull_request_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-950/60 border border-emerald-400/40 transition-all group"
            >
              <GitPullRequest className="w-3.5 h-3.5 text-white" />
              <span>Inspect Pull Request</span>
              <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </a>
          )}

          {isRunning && (
            <button
              onClick={onCancel}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg bg-graphite-900 hover:bg-rose-950 hover:text-rose-300 hover:border-rose-800/80 border border-white/[0.08] text-mist-300 text-xs font-medium flex items-center gap-1.5 transition-all shadow-sm disabled:opacity-50"
              title="Cancel running task execution"
            >
              <Ban className="w-3.5 h-3.5 text-rose-400" />
              <span>Abort Run</span>
            </button>
          )}

          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg bg-steel-900/60 border border-white/[0.08] text-mist-400 hover:text-white hover:bg-steel-800 transition-all shadow-sm"
            title="Refresh status & telemetry"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Grid: Target Repo & Branch Topology */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-3 rounded-lg bg-[#070a11] border border-white/[0.05]">
          <span className="text-[10px] font-mono font-medium text-mist-500 uppercase tracking-widest block mb-1">
            Target Repository
          </span>
          <a
            href={task.repository_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-mono text-icy-300 hover:underline flex items-center gap-1.5 truncate group"
          >
            <GitFork className="w-3.5 h-3.5 text-icy-400 flex-shrink-0" />
            <span className="truncate">{task.repository_url}</span>
            <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-60 group-hover:opacity-100" />
          </a>
        </div>

        <div className="p-3 rounded-lg bg-[#070a11] border border-white/[0.05]">
          <span className="text-[10px] font-mono font-medium text-mist-500 uppercase tracking-widest block mb-1">
            Git Topology &amp; Commit
          </span>
          <div className="flex items-center gap-3 text-xs font-mono text-mist-300 flex-wrap">
            <span className="flex items-center gap-1.5">
              <GitBranch className="w-3.5 h-3.5 text-mist-500" />
              <span className="text-mist-400">{task.base_branch}</span>
              <span className="text-mist-600">&rarr;</span>
              <span className="text-icy-300">{task.working_branch}</span>
            </span>
            {task.commit_sha && (
              <span className="px-1.5 py-0.5 rounded bg-graphite-900 border border-white/[0.08] text-[11px] text-emerald-300">
                {task.commit_sha.substring(0, 7)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* User Instruction Block */}
      <div className="mt-4 pt-3 border-t border-white/[0.06]">
        <span className="text-[10px] font-mono font-medium text-mist-500 uppercase tracking-widest block mb-1.5">
          Execution Prompt &amp; Specification
        </span>
        <div className="text-xs text-slate-200 bg-[#070a11] p-3.5 rounded-lg border border-white/[0.06] leading-relaxed font-sans select-text shadow-inner-glow">
          {task.user_instruction}
        </div>
      </div>

      {/* Timestamps */}
      <div className="mt-3 flex items-center justify-between text-[11px] text-mist-500 font-mono">
        <span className="flex items-center gap-1.5">
          <Clock className="w-3 h-3 text-mist-600" />
          <span>Initialized: {new Date(task.created_at).toLocaleString()}</span>
        </span>
        <span>Telemetry Synced: {new Date(task.updated_at).toLocaleTimeString()}</span>
      </div>
    </div>
  );
};
