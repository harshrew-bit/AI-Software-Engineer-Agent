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
        <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-slate-200">Loading Task Details...</h3>
        <p className="text-xs text-slate-500 font-mono mt-1">{taskId}</p>
      </div>
    );
  }

  if (error && !task) {
    return (
      <div className="py-12 max-w-xl mx-auto">
        <div className="glass-card p-6 border-rose-900 bg-rose-950/20 text-center">
          <h3 className="text-base font-semibold text-rose-300">Failed to Load Task</h3>
          <p className="text-xs text-slate-400 mt-2">{error}</p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <button onClick={onBack} className="btn-secondary text-xs">
              Back to Dashboard
            </button>
            <button onClick={refresh} className="btn-primary text-xs">
              Retry
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
      {/* Task Header */}
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

      {/* Pipeline Progress Tracker */}
      <PipelineTracker
        currentPhase={task.current_phase}
        status={task.status}
        retryCount={task.retry_count}
      />

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('tools')}
          className={`px-3.5 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
            activeTab === 'tools'
              ? 'bg-primary-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <Wrench className="w-3.5 h-3.5" />
          <span>Tool History ({task.tool_history?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('files')}
          className={`px-3.5 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
            activeTab === 'files'
              ? 'bg-primary-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <FileCode2 className="w-3.5 h-3.5" />
          <span>Files & Diff ({task.modified_files?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('tests')}
          className={`px-3.5 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
            activeTab === 'tests'
              ? 'bg-primary-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Test Runs ({task.test_results?.length || 0})</span>
        </button>

        {task.plan && (
          <button
            onClick={() => setActiveTab('plan')}
            className={`px-3.5 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
              activeTab === 'plan'
                ? 'bg-primary-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <ListTodo className="w-3.5 h-3.5" />
            <span>Implementation Plan ({task.plan.steps?.length || 0})</span>
          </button>
        )}

        <button
          onClick={() => setActiveTab('events')}
          className={`px-3.5 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
            activeTab === 'events'
              ? 'bg-primary-600 text-white shadow'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          }`}
        >
          <Radio className="w-3.5 h-3.5 text-cyan-400" />
          <span>Live Event Feed ({events.length})</span>
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
          <div className="glass-card p-6 space-y-6">
            <div>
              <h3 className="text-base font-semibold text-white">
                Objective: {task.plan.objective}
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                {task.plan.architecture_overview}
              </p>
            </div>

            <div className="space-y-3">
              {task.plan.steps.map((step, idx) => (
                <div
                  key={step.step_id || idx}
                  className="p-4 rounded-lg bg-[#070b14] border border-slate-800 flex items-start gap-3"
                >
                  <div className="w-6 h-6 rounded-md bg-slate-800 flex items-center justify-center text-xs font-mono text-primary-400 flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold text-slate-200">
                        {step.title}
                      </h4>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        {step.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      {step.description}
                    </p>
                    {step.target_files && step.target_files.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {step.target_files.map((file, fIdx) => (
                          <span
                            key={fIdx}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-cyan-400 border border-slate-800"
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
          <div className="glass-card p-6">
            <div className="mb-4 pb-3 border-b border-slate-800">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Radio className="w-4 h-4 text-cyan-400" />
                Real-Time SSE Event Stream
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Live stream of state transitions and lifecycle broadcasts.
              </p>
            </div>

            {events.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 italic">
                Listening for live task events...
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {events.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-[#070b14] border border-slate-800 flex items-start justify-between gap-4 font-mono text-xs"
                  >
                    <div className="flex items-start gap-2 min-w-0">
                      <span className="px-1.5 py-0.5 rounded bg-primary-950 text-primary-400 border border-primary-800/60 text-[10px]">
                        {ev.event_type}
                      </span>
                      <span className="text-slate-300 truncate">{ev.message}</span>
                    </div>
                    <span className="text-slate-500 text-[10px] flex-shrink-0">
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
