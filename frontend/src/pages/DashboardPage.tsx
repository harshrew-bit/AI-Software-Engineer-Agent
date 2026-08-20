import React from 'react';
import { CreateTaskForm } from '../components/dashboard/CreateTaskForm';
import { TaskListTable } from '../components/dashboard/TaskListTable';
import { useTaskList } from '../hooks/useTaskList';
import { Bot, CheckCircle2, GitPullRequest, Layers } from 'lucide-react';
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
    <div className="space-y-8 pb-12">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl glass-card p-8 md:p-10 border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-background/90">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-950/80 border border-primary-800/60 text-primary-300 text-xs font-mono mb-4">
            <Bot className="w-3.5 h-3.5" />
            <span>Autonomous Software Engineering Agent</span>
          </div>

          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Ship PRs autonomously from natural language prompts.
          </h1>

          <p className="text-sm md:text-base text-slate-300 mt-3 leading-relaxed">
            LangGraph deterministic state machine cloning GitHub repositories, writing code via LLM tool loops, executing tests inside Docker sandboxes, and submitting pull requests.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-slate-800/80 text-xs">
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="text-slate-400 font-medium">Total Tasks</div>
              <div className="text-xl font-bold text-white mt-1 font-mono">{tasks.length}</div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="text-slate-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Completed</span>
              </div>
              <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">{completedTasks}</div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="text-slate-400 font-medium flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-primary-400" />
                <span>In Progress</span>
              </div>
              <div className="text-xl font-bold text-primary-300 mt-1 font-mono">{runningTasks}</div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="text-slate-400 font-medium flex items-center gap-1">
                <GitPullRequest className="w-3.5 h-3.5 text-cyan-400" />
                <span>PRs Created</span>
              </div>
              <div className="text-xl font-bold text-cyan-400 mt-1 font-mono">{prsCreated}</div>
            </div>
          </div>
        </div>

        {/* Subtle background glow */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* Launch New Task Form */}
      <CreateTaskForm onTaskCreated={(task: TaskResponse) => onSelectTask(task.id)} />

      {/* Recent Tasks List */}
      <TaskListTable
        tasks={tasks}
        loading={loading}
        onSelectTask={onSelectTask}
        onRefresh={refresh}
      />
    </div>
  );
};
