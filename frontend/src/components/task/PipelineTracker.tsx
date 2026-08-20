import React from 'react';
import {
  Search,
  ListTodo,
  Code2,
  CheckCircle,
  Bug,
  FileCheck,
  GitCommit,
  GitPullRequest,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
} from 'lucide-react';
import type { TaskStatus, WorkflowPhase } from '../../types/task';

interface PipelineTrackerProps {
  currentPhase: WorkflowPhase;
  status: TaskStatus;
  retryCount?: number;
}

interface StepConfig {
  id: WorkflowPhase;
  label: string;
  description: string;
  icon: React.ElementType;
}

const PIPELINE_STEPS: StepConfig[] = [
  {
    id: 'repository_analysis',
    label: 'Repo Analysis',
    description: 'Inspect structure & tech stack',
    icon: Search,
  },
  {
    id: 'planning',
    label: 'Planning',
    description: 'Formulate architecture & steps',
    icon: ListTodo,
  },
  {
    id: 'coding',
    label: 'Coding & Tools',
    description: 'Execute multi-turn file edits',
    icon: Code2,
  },
  {
    id: 'testing',
    label: 'Sandbox Testing',
    description: 'Run test suite in sandbox',
    icon: CheckCircle,
  },
  {
    id: 'review',
    label: 'Review',
    description: 'Audit diff & create commit msg',
    icon: FileCheck,
  },
  {
    id: 'commit',
    label: 'Git Commit',
    description: 'Stage & commit branch changes',
    icon: GitCommit,
  },
  {
    id: 'pull_request',
    label: 'Pull Request',
    description: 'Push to origin & open PR',
    icon: GitPullRequest,
  },
];

export const PipelineTracker: React.FC<PipelineTrackerProps> = ({
  currentPhase,
  status,
  retryCount = 0,
}) => {
  const phaseOrder: WorkflowPhase[] = [
    'initialized',
    'repository_analysis',
    'planning',
    'coding',
    'testing',
    'debugging',
    'review',
    'commit',
    'pull_request',
    'finished',
  ];

  const currentPhaseIndex = phaseOrder.indexOf(currentPhase);

  const getStepState = (stepId: WorkflowPhase) => {
    const stepIndex = phaseOrder.indexOf(stepId);

    if (status === 'completed') {
      return 'completed';
    }

    if (status === 'failed') {
      if (currentPhase === stepId) return 'failed';
      if (currentPhase === 'finished' && stepId === 'pull_request') return 'failed';
      return stepIndex < currentPhaseIndex ? 'completed' : 'pending';
    }

    if (currentPhase === 'debugging' && stepId === 'testing') {
      return 'retry';
    }

    if (currentPhase === stepId) {
      return 'active';
    }

    if (stepIndex < currentPhaseIndex) {
      return 'completed';
    }

    return 'pending';
  };

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <span>Agent Workflow Pipeline</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic LangGraph state machine orchestrating repository operations.
          </p>
        </div>

        {retryCount > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-950/60 px-3 py-1 rounded-full border border-amber-800/80 font-mono">
            <Bug className="w-3.5 h-3.5" />
            <span>Test-Debug Healing Loops: {retryCount}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {PIPELINE_STEPS.map((step, index) => {
          const stepState = getStepState(step.id);
          const StepIcon = step.icon;

          let cardStyle = 'bg-slate-900/60 border-slate-800/80 text-slate-400';
          let iconStyle = 'bg-slate-800 text-slate-500';
          let indicatorIcon = <Clock className="w-3 h-3 text-slate-500" />;

          if (stepState === 'completed') {
            cardStyle = 'bg-emerald-950/30 border-emerald-800/60 text-slate-200';
            iconStyle = 'bg-emerald-900/80 text-emerald-300';
            indicatorIcon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
          } else if (stepState === 'active') {
            cardStyle = 'bg-primary-950/50 border-primary-500 text-white shadow-lg shadow-primary-950/50 ring-1 ring-primary-500';
            iconStyle = 'bg-primary-600 text-white';
            indicatorIcon = <Loader2 className="w-3.5 h-3.5 text-primary-400 animate-spin" />;
          } else if (stepState === 'retry') {
            cardStyle = 'bg-amber-950/40 border-amber-600 text-amber-200 ring-1 ring-amber-500/50';
            iconStyle = 'bg-amber-600 text-white';
            indicatorIcon = <Bug className="w-3.5 h-3.5 text-amber-400 animate-bounce" />;
          } else if (stepState === 'failed') {
            cardStyle = 'bg-rose-950/40 border-rose-600 text-rose-200 ring-1 ring-rose-500/50';
            iconStyle = 'bg-rose-600 text-white';
            indicatorIcon = <XCircle className="w-3.5 h-3.5 text-rose-400" />;
          }

          return (
            <div
              key={step.id}
              className={`p-3.5 rounded-xl border flex flex-col justify-between transition-all relative overflow-hidden ${cardStyle}`}
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${iconStyle}`}>
                    <StepIcon className="w-4 h-4" />
                  </div>
                  <div>{indicatorIcon}</div>
                </div>

                <div className="font-semibold text-xs text-slate-100 flex items-center gap-1.5">
                  <span className="text-[10px] text-slate-500 font-mono">0{index + 1}</span>
                  <span>{step.label}</span>
                </div>
                <div className="text-[10.5px] text-slate-400 mt-1 line-clamp-2 leading-tight">
                  {step.description}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] uppercase font-mono font-medium">
                <span className="text-slate-500">Status</span>
                <span
                  className={
                    stepState === 'completed'
                      ? 'text-emerald-400'
                      : stepState === 'active'
                      ? 'text-primary-300'
                      : stepState === 'failed'
                      ? 'text-rose-400'
                      : stepState === 'retry'
                      ? 'text-amber-400'
                      : 'text-slate-600'
                  }
                >
                  {stepState}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
