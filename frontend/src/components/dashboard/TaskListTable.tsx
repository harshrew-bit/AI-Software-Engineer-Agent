import React, { useState, useMemo } from 'react';
import {
  ExternalLink,
  GitPullRequest,
  GitBranch,
  RefreshCw,
  Terminal,
  Search,
} from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';
import type { TaskResponse } from '../../types/task';


interface TaskListTableProps {
  tasks: TaskResponse[];
  loading: boolean;
  onSelectTask: (taskId: string) => void;
  onRefresh: () => void;
}

export const TaskListTable: React.FC<TaskListTableProps> = ({
  tasks,
  loading,
  onSelectTask,
  onRefresh,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const getRepoName = (url: string) => {
    try {
      const parts = url.replace(/\/+$/, '').split('/');
      if (parts.length >= 2) {
        return `${parts[parts.length - 2]}/${parts[parts.length - 1]}`;
      }
      return url;
    } catch {
      return url;
    }
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      const matchesSearch =
        searchQuery.trim() === '' ||
        task.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.repository_url.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.user_instruction.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus =
        statusFilter === 'all' || task.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [tasks, searchQuery, statusFilter]);

  return (
    <div className="glass-panel overflow-hidden relative">
      {/* Subtle top edge warm champagne specular highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-champagne-300/30 to-transparent pointer-events-none" />

      {/* Table Header Bar */}
      <div className="p-5 md:p-6 border-b border-white/[0.06] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-copper-400"></span>
            <span className="text-[11px] font-mono text-mist-400 uppercase tracking-widest">
              Execution Registry
            </span>
          </div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 mt-1">
            <Terminal className="w-4 h-4 text-copper-400" />
            <span>Agent Task Runs</span>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-champagne-200">
              {tasks.length} total
            </span>
          </h3>
          <p className="text-xs text-mist-300 mt-0.5">
            Audit history of autonomous repository clones, diffs, tests, and pull requests.
          </p>
        </div>

        {/* Search, Filter & Refresh Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Quick text filter */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-mist-500 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter tasks..."
              className="pl-8 pr-3 py-1.5 bg-midnight-950/80 border border-white/[0.08] rounded-xl text-xs text-slate-200 placeholder-mist-600 focus:outline-none focus:border-copper-400/70 w-36 sm:w-48 font-mono shadow-inner-copper"
            />
          </div>

          {/* Status filter dropdown */}
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-midnight-950/80 border border-white/[0.08] rounded-xl text-xs text-mist-300 focus:outline-none focus:border-copper-400/70 font-mono"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="paused_for_approval">Awaiting Approval</option>
              <option value="failed">Failed</option>
              <option value="pending">Queued</option>
            </select>
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-xl bg-white/[0.04] border border-white/[0.08] text-mist-300 hover:text-white hover:bg-white/[0.08] transition-all shadow-sm"
            title="Refresh task list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-copper-400' : ''}`} />
          </button>
        </div>
      </div>

      {tasks.length === 0 ? (
        <div className="p-12 text-center">
          <div className="w-12 h-12 rounded-xl bg-graphite-900/80 border border-white/[0.06] flex items-center justify-center mx-auto mb-3 text-mist-500">
            <Terminal className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-semibold text-slate-200">No agent tasks registered</h4>
          <p className="text-xs text-mist-400 mt-1 max-w-sm mx-auto">
            Launch your first engineering task above to initialize the autonomous LangGraph runner.
          </p>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="p-8 text-center text-xs text-mist-500 italic">
          No tasks matched the current filter query.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-midnight-950/80 border-b border-white/[0.06] text-mist-400 uppercase tracking-wider font-mono text-[11px]">
                <th className="py-3 px-4 font-medium">Task ID</th>
                <th className="py-3 px-4 font-medium">Repository &amp; Instruction</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium">Phase</th>
                <th className="py-3 px-4 font-medium">Deliverables</th>
                <th className="py-3 px-4 font-medium">Created</th>
                <th className="py-3 px-4 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {filteredTasks.map((task) => (
                <tr
                  key={task.id}
                  onClick={() => onSelectTask(task.id)}
                  className="hover:bg-white/[0.03] cursor-pointer transition-colors group"
                >
                  <td className="py-3.5 px-4 font-mono font-medium text-champagne-300 whitespace-nowrap">
                    <span className="group-hover:underline">{task.id}</span>
                  </td>

                  <td className="py-3.5 px-4 max-w-md">
                    <div className="font-medium text-slate-200 truncate font-mono text-xs">
                      {getRepoName(task.repository_url)}
                    </div>
                    <div className="text-mist-400 text-[11px] truncate mt-0.5 font-sans">
                      {task.user_instruction}
                    </div>
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <StatusBadge status={task.status} size="sm" />
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <StatusBadge phase={task.current_phase} size="sm" />
                  </td>

                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {task.pull_request_url ? (
                        <a
                          href={task.pull_request_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-emerald-950/50 text-emerald-300 border border-emerald-700/60 hover:bg-emerald-900/60 transition-colors shadow-sm"
                        >
                          <GitPullRequest className="w-3 h-3 text-emerald-400" />
                          <span>PR Created</span>
                          <ExternalLink className="w-2.5 h-2.5 text-emerald-400/80" />
                        </a>
                      ) : task.commit_sha ? (
                        <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-white/[0.04] text-mist-300 font-mono border border-white/[0.06]">
                          <GitBranch className="w-3 h-3 text-copper-400" />
                          <span>{task.commit_sha.substring(0, 7)}</span>
                        </span>
                      ) : (
                        <span className="text-mist-600 text-[11px] font-mono">—</span>
                      )}
                    </div>
                  </td>

                  <td className="py-3.5 px-4 text-mist-400 whitespace-nowrap text-[11px] font-mono">
                    {formatDate(task.created_at)}
                  </td>

                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectTask(task.id);
                      }}
                      className="text-xs px-2.5 py-1 rounded-lg bg-white/[0.04] text-mist-300 group-hover:bg-[#d9825b] group-hover:text-white border border-white/[0.08] group-hover:border-copper-400/50 transition-all font-mono"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
