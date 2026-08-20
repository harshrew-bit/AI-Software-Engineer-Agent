import React from 'react';
import {
  GitFork,
  GitBranch,
  GitPullRequest,
  ExternalLink,
  Ban,
  Clock,
  RotateCw,
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
  const isRunning = task.status === 'running' || task.status === 'pending';

  return (
    <div className="glass-card p-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-base font-bold text-primary-400">
            {task.id}
          </span>
          <StatusBadge status={task.status} size="md" />
          <StatusBadge phase={task.current_phase} size="md" />

          {task.retry_count > 0 && (
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-400 border border-amber-800/80">
              Retry #{task.retry_count}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {task.pull_request_url && (
            <a
              href={task.pull_request_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-lg shadow-emerald-950 transition-colors"
            >
              <GitPullRequest className="w-3.5 h-3.5" />
              <span>View Pull Request</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}

          {isRunning && (
            <button
              onClick={onCancel}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-950 hover:text-rose-300 hover:border-rose-800 border border-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
              title="Cancel running task"
            >
              <Ban className="w-3.5 h-3.5" />
              <span>Cancel</span>
            </button>
          )}

          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            title="Refresh details"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Target Repository
          </span>
          <a
            href={task.repository_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-mono text-cyan-400 hover:underline flex items-center gap-1.5 truncate"
          >
            <GitFork className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{task.repository_url}</span>
            <ExternalLink className="w-3 h-3 flex-shrink-0" />
          </a>
        </div>

        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Branches & Commit
          </span>
          <div className="flex items-center gap-3 text-xs font-mono text-slate-300">
            <span className="flex items-center gap-1 text-slate-400">
              <GitBranch className="w-3 h-3" />
              {task.base_branch} &rarr; <span className="text-primary-300">{task.working_branch}</span>
            </span>
            {task.commit_sha && (
              <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[11px]">
                {task.commit_sha.substring(0, 7)}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/80">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
          Instruction
        </span>
        <p className="text-xs text-slate-200 bg-[#070b14] p-3 rounded-lg border border-slate-800/80 leading-relaxed font-sans select-text">
          {task.user_instruction}
        </p>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 font-mono">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Started: {new Date(task.created_at).toLocaleString()}
        </span>
        <span>Updated: {new Date(task.updated_at).toLocaleTimeString()}</span>
      </div>
    </div>
  );
};
