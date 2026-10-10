import React from 'react';
import { CreateTaskForm } from '../components/dashboard/CreateTaskForm';
import { TaskListTable } from '../components/dashboard/TaskListTable';
import { useTaskList } from '../hooks/useTaskList';
import { CheckCircle2, GitPullRequest, Layers } from 'lucide-react';
import type { TaskResponse } from '../types/task';


interface DashboardPageProps {
  onSelectTask: (taskId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onSelectTask }) => {
  const { tasks, loading, refresh } = useTaskList(true, 4000);

  const completedTasks = tasks.filter((t) => t.status === 'completed').length;
  const runningTasks = tasks.filter((t) => t.status === 'running' || t.status === 'pending').length;
  const prsCreated = tasks.filter((t) => !!t.pull_request_url).length;

  return (
    <div className="space-y-6 pb-8">
      {/* Editorial Workspace Telemetry HUD */}
      <div className="glass-panel p-6 md:p-7 relative overflow-hidden">
        {/* Subtle top edge technical highlight */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-icy-400/25 to-transparent pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-steel-900/60 border border-white/[0.08] text-icy-300 text-[11px] font-mono mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-icy-400 animate-pulse"></span>
              <span>Topographic Intelligence Workspace</span>
            </div>

            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight leading-tight">
              Autonomous Software Engineering
            </h1>

            <p className="text-xs md:text-sm text-mist-400 mt-2 leading-relaxed">
              LangGraph deterministic state machine cloning GitHub repositories, writing code via LLM tool loops, executing tests inside Docker sandboxes, and submitting pull requests.
            </p>
          </div>

          {/* Compact Telemetry Counters Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs w-full md:w-auto">
            <div className="p-3 rounded-lg bg-[#070a11] border border-white/[0.06] shadow-sm min-w-[110px]">
              <div className="text-mist-400 font-mono text-[11px]">Total Tasks</div>
              <div className="text-xl font-bold text-white mt-1 font-mono">{tasks.length}</div>
            </div>

            <div className="p-3 rounded-lg bg-[#070a11] border border-white/[0.06] shadow-sm min-w-[110px]">
              <div className="text-mist-400 font-mono text-[11px] flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Completed</span>
              </div>
              <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">{completedTasks}</div>
            </div>

            <div className="p-3 rounded-lg bg-[#070a11] border border-white/[0.06] shadow-sm min-w-[110px]">
              <div className="text-mist-400 font-mono text-[11px] flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-icy-300" />
                <span>In Progress</span>
              </div>
              <div className="text-xl font-bold text-icy-300 mt-1 font-mono">{runningTasks}</div>
            </div>

            <div className="p-3 rounded-lg bg-[#070a11] border border-white/[0.06] shadow-sm min-w-[110px]">
              <div className="text-mist-400 font-mono text-[11px] flex items-center gap-1">
                <GitPullRequest className="w-3.5 h-3.5 text-sky-400" />
                <span>PRs Delivered</span>
              </div>
              <div className="text-xl font-bold text-sky-400 mt-1 font-mono">{prsCreated}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Task Launch Panel */}
      <CreateTaskForm onTaskCreated={(task: TaskResponse) => onSelectTask(task.id)} />

      {/* Task Execution Registry Table */}
      <TaskListTable
        tasks={tasks}
        loading={loading}
        onSelectTask={onSelectTask}
        onRefresh={refresh}
      />
    </div>
  );
};
