import React from 'react';
import { ExternalLink, GitPullRequest, GitBranch, RefreshCw, Terminal } from 'lucide-react';
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

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-6 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            Recent Agent Executions
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            History of automated branches, commits, and pull requests.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title="Refresh task list"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="p-12 text-center">
          <Terminal className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <h4 className="text-sm font-medium text-slate-300">No tasks found</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Launch your first engineering task above to see autonomous repository workflows in action.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Task ID</th>
                <th className="py-3 px-4">Repository & Instruction</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Phase</th>
                <th className="py-3 px-4">Deliverables</th>
                <th className="py-3 px-4">Created</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {tasks.map((task) => (
                <tr
                  key={task.id}
                  onClick={() => onSelectTask(task.id)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                >
                  <td className="py-3.5 px-4 font-mono font-medium text-primary-400 whitespace-nowrap">
                    {task.id}
                  </td>

                  <td className="py-3.5 px-4 max-w-md">
                    <div className="font-medium text-slate-200 truncate">
                      {getRepoName(task.repository_url)}
                    </div>
                    <div className="text-slate-400 text-[11px] truncate mt-0.5">
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
                          className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 hover:bg-emerald-900 transition-colors"
                        >
                          <GitPullRequest className="w-3 h-3" />
                          <span>PR Created</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      ) : task.commit_sha ? (
                        <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          <GitBranch className="w-3 h-3 text-primary-400" />
                          {task.commit_sha.substring(0, 7)}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">—</span>
                      )}
                    </div>
                  </td>

                  <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap text-[11px]">
                    {formatDate(task.created_at)}
                  </td>

                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectTask(task.id);
                      }}
                      className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 group-hover:bg-primary-600 group-hover:text-white transition-colors"
                    >
                      View
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
