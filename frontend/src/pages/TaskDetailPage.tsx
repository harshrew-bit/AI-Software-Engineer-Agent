import React, { useState } from 'react';
import {
  Wrench,
  FileCode2,
  ShieldCheck,
  ListTodo,
  Radio,
  Loader2,
} from 'lucide-react';

import { useTaskDetail } from '../hooks/useTaskDetail';
import { TaskHeader } from '../components/task/TaskHeader';
import { PipelineTracker } from '../components/task/PipelineTracker';
import { ToolHistoryList } from '../components/task/ToolHistoryList';
import { ModifiedFilesView } from '../components/task/ModifiedFilesView';
import { TestResultsView } from '../components/task/TestResultsView';
import { ApprovalCard } from '../components/task/ApprovalCard';
import { ErrorCard } from '../components/task/ErrorCard';

interface TaskDetailPageProps {
  taskId: string;
  onBack: () => void;
}

export const TaskDetailPage: React.FC<TaskDetailPageProps> = ({ taskId, onBack }) => {
  const {
    task,
    diff,
    loading,
    diffLoading,
    error,
    events,
    actionLoading,
    refresh,
    submitApproval,
    submitCancel,
  } = useTaskDetail(taskId);

  const [activeTab, setActiveTab] = useState<'tools' | 'files' | 'tests' | 'plan' | 'events'>('tools');

  if (loading && !task) {
    return (
      <div className="py-24 text-center">
        <div className="w-14 h-14 rounded-2xl bg-midnight-950/80 border border-white/[0.08] flex items-center justify-center mx-auto mb-4 shadow-glass">
          <Loader2 className="w-7 h-7 animate-spin text-copper-400" />
        </div>
        <h3 className="text-sm font-bold text-slate-200 tracking-tight">Syncing Task Telemetry...</h3>
        <p className="text-xs text-mist-400 font-mono mt-1">{taskId}</p>
      </div>
    );
  }

  if (error && !task) {
    return (
      <div className="py-12 max-w-xl mx-auto">
        <div className="glass-panel p-6 border-rose-800/60 bg-rose-950/20 text-center">
          <h3 className="text-base font-bold text-rose-300">Failed to Load Task</h3>
          <p className="text-xs text-mist-400 mt-2 font-sans">{error}</p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <button onClick={onBack} className="btn-secondary text-xs">
              Return to Workspace
            </button>
            <button onClick={refresh} className="btn-primary text-xs">
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!task) return null;

  const isPausedForApproval =
    task.status === 'paused_for_approval' || !!task.pending_approval;
  const isFailed = task.status === 'failed';

  return (
    <div className="space-y-6 pb-16">
      {/* Task Header HUD */}
      <TaskHeader
        task={task}
        onRefresh={refresh}
        onCancel={submitCancel}
        actionLoading={actionLoading}
      />

      {/* Human-in-the-Loop Approval Banner */}
      {isPausedForApproval && task.pending_approval && (
        <ApprovalCard
          approval={task.pending_approval}
          onSubmitDecision={submitApproval}
          actionLoading={actionLoading}
        />
      )}

      {/* Error Card */}
      {isFailed && (
        <ErrorCard
          errorMessage={task.error_message}
          lastPhase={task.current_phase}
          onRetry={onBack}
        />
      )}

      {/* Pipeline Progress Tracker (Connected 7-Phase Execution Visualization) */}
      <PipelineTracker
        currentPhase={task.current_phase}
        status={task.status}
        retryCount={task.retry_count}
      />

      {/* Tabs Navigation Bar */}
      <div className="glass-panel-subtle p-1.5 rounded-xl flex items-center gap-1.5 overflow-x-auto border border-white/[0.08]">
        <button
          onClick={() => setActiveTab('tools')}
          className={`px-3.5 py-2 rounded-lg text-xs font-mono transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'tools'
              ? 'bg-white/[0.08] text-white shadow-sm border border-copper-400/40 font-semibold shadow-inner-copper'
              : 'text-mist-400 hover:text-slate-200 hover:bg-white/[0.03]'
          }`}
        >
          <Wrench className="w-3.5 h-3.5 text-copper-400" />
          <span>Tool Audit Trail ({task.tool_history?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('files')}
          className={`px-3.5 py-2 rounded-lg text-xs font-mono transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'files'
              ? 'bg-white/[0.08] text-white shadow-sm border border-copper-400/40 font-semibold shadow-inner-copper'
              : 'text-mist-400 hover:text-slate-200 hover:bg-white/[0.03]'
          }`}
        >
          <FileCode2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Files &amp; Diff ({task.modified_files?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('tests')}
          className={`px-3.5 py-2 rounded-lg text-xs font-mono transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'tests'
              ? 'bg-white/[0.08] text-white shadow-sm border border-copper-400/40 font-semibold shadow-inner-copper'
              : 'text-mist-400 hover:text-slate-200 hover:bg-white/[0.03]'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5 text-champagne-300" />
          <span>Test Runs ({task.test_results?.length || 0})</span>
        </button>

        {task.plan && (
          <button
            onClick={() => setActiveTab('plan')}
            className={`px-3.5 py-2 rounded-lg text-xs font-mono transition-all flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'plan'
                ? 'bg-white/[0.08] text-white shadow-sm border border-copper-400/40 font-semibold shadow-inner-copper'
                : 'text-mist-400 hover:text-slate-200 hover:bg-white/[0.03]'
            }`}
          >
            <ListTodo className="w-3.5 h-3.5 text-champagne-400" />
            <span>Architecture Plan ({task.plan.steps?.length || 0})</span>
          </button>
        )}

        <button
          onClick={() => setActiveTab('events')}
          className={`px-3.5 py-2 rounded-lg text-xs font-mono transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'events'
              ? 'bg-white/[0.08] text-white shadow-sm border border-copper-400/40 font-semibold shadow-inner-copper'
              : 'text-mist-400 hover:text-slate-200 hover:bg-white/[0.03]'
          }`}
        >
          <Radio className="w-3.5 h-3.5 text-copper-400" />
          <span>Live SSE Stream ({events.length})</span>
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === 'tools' && (
          <ToolHistoryList toolHistory={task.tool_history || []} />
        )}

        {activeTab === 'files' && (
          <ModifiedFilesView
            modifiedFiles={task.modified_files || []}
            diff={diff}
            diffLoading={diffLoading}
          />
        )}

        {activeTab === 'tests' && (
          <TestResultsView testResults={task.test_results || []} />
        )}

        {activeTab === 'plan' && task.plan && (
          <div className="glass-panel p-6 space-y-6 relative overflow-hidden">
            {/* Top subtle highlight */}
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-icy-400/25 to-transparent pointer-events-none" />

            <div>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-icy-400"></span>
                <span className="text-[10px] font-mono text-mist-400 uppercase tracking-widest">
                  Plan Strategy
                </span>
              </div>
              <h3 className="text-base font-bold text-white mt-1">
                Objective: {task.plan.objective}
              </h3>
              <p className="text-xs text-mist-400 mt-1 leading-relaxed">
                {task.plan.architecture_overview}
              </p>
            </div>

            <div className="space-y-3">
              {task.plan.steps.map((step, idx) => (
                <div
                  key={step.step_id || idx}
                  className="p-4 rounded-xl bg-[#070a11] border border-white/[0.06] flex items-start gap-3.5 hover:border-white/[0.12] transition-colors"
                >
                  <div className="w-6 h-6 rounded-md bg-graphite-800 border border-white/[0.08] flex items-center justify-center text-xs font-mono text-icy-300 flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-semibold text-slate-100">
                        {step.title}
                      </h4>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-graphite-900 text-mist-400 border border-white/[0.06]">
                        {step.status}
                      </span>
                    </div>
                    <p className="text-xs text-mist-400 mt-1 leading-relaxed font-sans">
                      {step.description}
                    </p>
                    {step.target_files && step.target_files.length > 0 && (
                      <div className="mt-2.5 flex flex-wrap gap-1.5">
                        {step.target_files.map((file, fIdx) => (
                          <span
                            key={fIdx}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-steel-900/60 text-icy-300 border border-white/[0.06]"
                          >
                            {file}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'events' && (
          <div className="glass-panel p-6 relative overflow-hidden">
            {/* Top subtle highlight */}
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-icy-400/25 to-transparent pointer-events-none" />

            <div className="mb-4 pb-3 border-b border-white/[0.06] flex items-center justify-between">
              <div>
                <h3 className="text-sm md:text-base font-bold text-white flex items-center gap-2">
                  <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
                  <span>Real-Time SSE Event Stream</span>
                </h3>
                <p className="text-xs text-mist-400 mt-0.5">
                  Live broadcast of state transitions, lifecycle events, and tool telemetry.
                </p>
              </div>

              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-950/40 text-cyan-300 border border-cyan-800/50 text-[11px] font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
                <span>Streaming</span>
              </div>
            </div>

            {events.length === 0 ? (
              <div className="p-12 text-center text-xs text-mist-500 italic font-mono">
                Listening on Server-Sent Events stream for incoming task transitions...
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {events.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-[#070a11] border border-white/[0.06] flex items-start justify-between gap-4 font-mono text-xs hover:border-white/[0.1] transition-colors"
                  >
                    <div className="flex items-start gap-2.5 min-w-0">
                      <span className="px-2 py-0.5 rounded bg-steel-900/80 text-icy-300 border border-white/[0.08] text-[10px] flex-shrink-0">
                        {ev.event_type}
                      </span>
                      <span className="text-slate-200 truncate leading-relaxed">
                        {ev.message}
                      </span>
                    </div>
                    <span className="text-mist-500 text-[10px] flex-shrink-0">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
