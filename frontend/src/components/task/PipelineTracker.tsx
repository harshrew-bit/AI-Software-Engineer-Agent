import React from 'react';
import {
  Search,
  ListTodo,
  Code2,
  ShieldCheck,
  Bug,
  FileCheck,
  GitPullRequest,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  PauseCircle,
  Activity,
} from 'lucide-react';

import type { TaskStatus, WorkflowPhase } from '../../types/task';

interface PipelineTrackerProps {
  currentPhase: WorkflowPhase;
  status: TaskStatus;
  retryCount?: number;
}

type StepState = 'completed' | 'active' | 'waiting_for_approval' | 'debugging' | 'failed' | 'pending';

interface PhaseDefinition {
  key: string;
  phaseId: WorkflowPhase;
  label: string;
  tag: string;
  description: string;
  icon: React.ElementType;
}

const WORKFLOW_SEVEN_PHASES: PhaseDefinition[] = [
  {
    key: 'repo_analysis',
    phaseId: 'repository_analysis',
    label: 'Repo Analysis',
    tag: '01',
    description: 'Structure, dependencies & tech stack inspection',
    icon: Search,
  },
  {
    key: 'planning',
    phaseId: 'planning',
    label: 'Planning',
    tag: '02',
    description: 'Architecture breakdown & file edit plan',
    icon: ListTodo,
  },
  {
    key: 'coding',
    phaseId: 'coding',
    label: 'Code Implementation',
    tag: '03',
    description: 'Multi-turn edits & AST code transformations',
    icon: Code2,
  },
  {
    key: 'testing',
    phaseId: 'testing',
    label: 'Sandbox Testing',
    tag: '04',
    description: 'Automated test suite execution in sandbox',
    icon: ShieldCheck,
  },
  {
    key: 'debugging',
    phaseId: 'debugging',
    label: 'Debugging',
    tag: '05',
    description: 'Test failure diagnostics & healing loops',
    icon: Bug,
  },
  {
    key: 'review',
    phaseId: 'review',
    label: 'Review & Commit',
    tag: '06',
    description: 'Unified diff audit & staged git commit',
    icon: FileCheck,
  },
  {
    key: 'pull_request',
    phaseId: 'pull_request',
    label: 'Pull Request',
    tag: '07',
    description: 'Remote branch push & PR delivery',
    icon: GitPullRequest,
  },
];

export const PipelineTracker: React.FC<PipelineTrackerProps> = ({
  currentPhase,
  status,
  retryCount = 0,
}) => {
  // Phase mapping order to accurately track progression
  const resolvePhaseIndex = (phase: WorkflowPhase): number => {
    switch (phase) {
      case 'initialized':
        return -1;
      case 'repository_analysis':
        return 0;
      case 'planning':
        return 1;
      case 'coding':
        return 2;
      case 'testing':
        return 3;
      case 'debugging':
        return 4;
      case 'review':
      case 'commit':
        return 5;
      case 'pull_request':
      case 'finished':
        return 6;
      default:
        return 0;
    }
  };

  const currentIdx = resolvePhaseIndex(currentPhase);

  const getPhaseState = (phaseIndex: number): StepState => {
    if (status === 'completed') {
      return 'completed';
    }

    if (status === 'paused_for_approval') {
      if (phaseIndex === currentIdx) return 'waiting_for_approval';
      return phaseIndex < currentIdx ? 'completed' : 'pending';
    }

    if (status === 'failed') {
      if (phaseIndex === currentIdx) return 'failed';
      // If marked finished with failure, last step failed
      if (currentPhase === 'finished' && phaseIndex === 6) return 'failed';
      return phaseIndex < currentIdx ? 'completed' : 'pending';
    }

    if (phaseIndex < currentIdx) {
      return 'completed';
    }

    if (phaseIndex === currentIdx) {
      if (currentPhase === 'debugging') return 'debugging';
      return 'active';
    }

    return 'pending';
  };

  return (
    <div className="glass-panel p-5 md:p-6 relative overflow-hidden">
      {/* Header section with telemetry */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-icy-400 animate-pulse"></span>
            <h3 className="text-sm font-semibold text-slate-100 tracking-tight font-sans">
              Seven-Phase Execution Topology
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-steel-900/80 text-mist-300 border border-white/[0.06]">
              Autonomous Cycle
            </span>
          </div>
          <p className="text-xs text-mist-400 mt-1 font-sans">
            Deterministic LangGraph state machine orchestrating repository operations.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
          {retryCount > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-950/40 text-amber-300 border border-amber-700/50">
              <Bug className="w-3.5 h-3.5" />
              <span>Healing Loops: {retryCount}</span>
            </div>
          )}

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-graphite-900/80 text-mist-400 border border-white/[0.06]">
            <Activity className="w-3 h-3 text-icy-400" />
            <span className="capitalize">{status.replace(/_/g, ' ')}</span>
          </div>
        </div>
      </div>

      {/* Desktop Horizontal Connected Conduit Layout */}
      <div className="hidden lg:block relative">
        {/* Connected Terrain Flow Line */}
        <div className="absolute top-[32px] left-[4%] right-[4%] h-[2px] bg-graphite-800 pointer-events-none z-0">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 via-sky-400 to-icy-400 transition-all duration-500 shadow-glow-cyan"
            style={{
              width:
                status === 'completed'
                  ? '100%'
                  : `${Math.max(0, Math.min(100, (currentIdx / 6) * 100))}%`,
            }}
          />
        </div>

        <div className="grid grid-cols-7 gap-3 relative z-10">
          {WORKFLOW_SEVEN_PHASES.map((phase, idx) => {
            const state = getPhaseState(idx);
            const PhaseIcon = phase.icon;

            // Visual treatment based on state
            let containerClasses =
              'bg-graphite-900/50 border-white/[0.05] text-mist-400 hover:border-white/[0.1]';
            let iconWrapper =
              'bg-graphite-800 text-mist-500 border border-white/[0.05]';
            let badgeText = 'Pending';
            let badgeClass = 'text-mist-500 bg-graphite-950/60 border-white/[0.04]';
            let indicator = <Clock className="w-3 h-3 text-mist-500" />;

            if (state === 'completed') {
              containerClasses =
                'bg-emerald-950/20 border-emerald-800/40 text-mist-200';
              iconWrapper =
                'bg-emerald-900/40 text-emerald-400 border border-emerald-700/50';
              badgeText = 'Complete';
              badgeClass = 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
              indicator = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
            } else if (state === 'active') {
              containerClasses =
                'bg-sky-950/30 border-sky-500/60 text-white shadow-glow-cyan/20 ring-1 ring-sky-500/40';
              iconWrapper =
                'bg-sky-600/30 text-icy-300 border border-sky-400/60 animate-pulse';
              badgeText = 'Active';
              badgeClass = 'text-icy-300 bg-sky-950/80 border-sky-700/70';
              indicator = <Loader2 className="w-3.5 h-3.5 text-icy-300 animate-spin" />;
            } else if (state === 'waiting_for_approval') {
              containerClasses =
                'bg-amber-950/30 border-amber-500/70 text-amber-200 shadow-glow-amber/30 ring-1 ring-amber-500/50';
              iconWrapper =
                'bg-amber-600/30 text-amber-300 border border-amber-500/60 animate-pulse';
              badgeText = 'Approval';
              badgeClass = 'text-amber-300 bg-amber-950/80 border-amber-700/70';
              indicator = <PauseCircle className="w-3.5 h-3.5 text-amber-400" />;
            } else if (state === 'debugging') {
              containerClasses =
                'bg-amber-950/25 border-amber-600/50 text-amber-200 shadow-glow-amber/20';
              iconWrapper =
                'bg-amber-900/40 text-amber-400 border border-amber-600/50 animate-bounce';
              badgeText = 'Healing';
              badgeClass = 'text-amber-400 bg-amber-950/60 border-amber-800/60';
              indicator = <Bug className="w-3.5 h-3.5 text-amber-400" />;
            } else if (state === 'failed') {
              containerClasses =
                'bg-rose-950/30 border-rose-600/60 text-rose-200 ring-1 ring-rose-500/50';
              iconWrapper =
                'bg-rose-900/40 text-rose-400 border border-rose-600/60';
              badgeText = 'Failed';
              badgeClass = 'text-rose-400 bg-rose-950/80 border-rose-800/70';
              indicator = <XCircle className="w-3.5 h-3.5 text-rose-400" />;
            }

            return (
              <div
                key={phase.key}
                className={`p-3 rounded-xl border flex flex-col justify-between transition-all duration-200 relative overflow-hidden backdrop-blur-sm ${containerClasses}`}
              >
                <div>
                  {/* Top node & status icon */}
                  <div className="flex items-center justify-between mb-3">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${iconWrapper}`}
                    >
                      <PhaseIcon className="w-4 h-4" />
                    </div>
                    <div>{indicator}</div>
                  </div>

                  {/* Title and metadata */}
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-[10px] text-mist-500 font-mono">
                      {phase.tag}
                    </span>
                    <h4 className="font-semibold text-xs text-slate-100 tracking-tight leading-snug">
                      {phase.label}
                    </h4>
                  </div>

                  <p className="text-[10.5px] text-mist-400 mt-1 line-clamp-2 leading-relaxed">
                    {phase.description}
                  </p>
                </div>

                {/* Bottom status chip */}
                <div className="mt-3 pt-2 border-t border-white/[0.04] flex items-center justify-between text-[10px] font-mono">
                  <span className="text-mist-500">Status</span>
                  <span
                    className={`px-1.5 py-0.5 rounded border text-[10px] uppercase font-medium ${badgeClass}`}
                  >
                    {badgeText}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Responsive Vertical Connected Timeline for Laptop & Mobile */}
      <div className="block lg:hidden">
        <div className="relative pl-6 space-y-3 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-graphite-800">
          {WORKFLOW_SEVEN_PHASES.map((phase, idx) => {
            const state = getPhaseState(idx);
            const PhaseIcon = phase.icon;

            let dotClass = 'bg-graphite-700 border-graphite-600';
            let cardBg = 'bg-graphite-900/60 border-white/[0.05] text-mist-300';
            let badgeText = 'Pending';
            let badgeColor = 'text-mist-500 border-white/[0.04] bg-graphite-950/60';

            if (state === 'completed') {
              dotClass = 'bg-emerald-500 border-emerald-400 shadow-glow-emerald';
              cardBg = 'bg-emerald-950/20 border-emerald-800/40 text-mist-200';
              badgeText = 'Complete';
              badgeColor = 'text-emerald-400 border-emerald-800/60 bg-emerald-950/60';
            } else if (state === 'active') {
              dotClass = 'bg-sky-400 border-sky-300 shadow-glow-cyan animate-pulse';
              cardBg = 'bg-sky-950/30 border-sky-500/60 text-white ring-1 ring-sky-500/40';
              badgeText = 'Active';
              badgeColor = 'text-icy-300 border-sky-700/70 bg-sky-950/80';
            } else if (state === 'waiting_for_approval') {
              dotClass = 'bg-amber-400 border-amber-300 shadow-glow-amber animate-pulse';
              cardBg = 'bg-amber-950/30 border-amber-500/70 text-amber-200 ring-1 ring-amber-500/50';
              badgeText = 'Approval Gate';
              badgeColor = 'text-amber-300 border-amber-700/70 bg-amber-950/80';
            } else if (state === 'debugging') {
              dotClass = 'bg-amber-500 border-amber-400';
              cardBg = 'bg-amber-950/25 border-amber-600/50 text-amber-200';
              badgeText = 'Healing Loop';
              badgeColor = 'text-amber-400 border-amber-800/60 bg-amber-950/60';
            } else if (state === 'failed') {
              dotClass = 'bg-rose-500 border-rose-400';
              cardBg = 'bg-rose-950/30 border-rose-600/60 text-rose-200';
              badgeText = 'Failed';
              badgeColor = 'text-rose-400 border-rose-800/70 bg-rose-950/80';
            }

            return (
              <div key={phase.key} className="relative">
                {/* Timeline node marker */}
                <div
                  className={`absolute -left-[29px] top-3.5 w-3.5 h-3.5 rounded-full border-2 transition-all ${dotClass}`}
                />

                <div
                  className={`p-3 rounded-lg border backdrop-blur-sm flex items-center justify-between gap-3 ${cardBg}`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-md bg-graphite-800/80 border border-white/[0.06] flex items-center justify-center flex-shrink-0 text-mist-400">
                      <PhaseIcon className="w-3.5 h-3.5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-mono text-mist-500">
                          {phase.tag}
                        </span>
                        <h4 className="font-semibold text-xs text-slate-100 truncate">
                          {phase.label}
                        </h4>
                      </div>
                      <p className="text-[11px] text-mist-400 truncate mt-0.5">
                        {phase.description}
                      </p>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border whitespace-nowrap flex-shrink-0 font-medium ${badgeColor}`}
                  >
                    {badgeText}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
