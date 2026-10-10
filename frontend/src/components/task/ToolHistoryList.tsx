import React, { useState } from 'react';
import {
  Wrench,
  CheckCircle2,
  XCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Terminal,
  FileCode,
  ShieldAlert,
} from 'lucide-react';
import { CodeBlock } from '../common/CodeBlock';
import type { ToolExecutionRecord } from '../../types/task';

interface ToolHistoryListProps {
  toolHistory: ToolExecutionRecord[];
}

export const ToolHistoryList: React.FC<ToolHistoryListProps> = ({ toolHistory }) => {
  const [expandedCalls, setExpandedCalls] = useState<Record<string, boolean>>({});

  const toggleExpand = (callId: string) => {
    setExpandedCalls((prev) => ({
      ...prev,
      [callId]: !prev[callId],
    }));
  };

  const expandAll = () => {
    const all: Record<string, boolean> = {};
    toolHistory.forEach((t) => {
      all[t.call_id] = true;
    });
    setExpandedCalls(all);
  };

  const collapseAll = () => {
    setExpandedCalls({});
  };

  if (!toolHistory || toolHistory.length === 0) {
    return (
      <div className="glass-panel p-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-graphite-900 border border-white/[0.06] flex items-center justify-center mx-auto mb-3 text-mist-500">
          <Wrench className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-200">No Tool Invocations Logged</h4>
        <p className="text-xs text-mist-400 mt-1 max-w-sm mx-auto">
          When the autonomous agent interacts with files, git commands, or sandbox runners, execution traces will stream here.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      {/* Top subtle highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-icy-400/25 to-transparent pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-icy-400"></span>
            <span className="text-[10px] font-mono text-mist-400 uppercase tracking-widest">
              Execution Observability
            </span>
          </div>
          <h3 className="text-sm md:text-base font-bold text-white flex items-center gap-2 mt-0.5">
            <Terminal className="w-4 h-4 text-icy-400" />
            <span>Sandbox Tool Invocations</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-graphite-900 border border-white/[0.08] text-mist-300">
              {toolHistory.length} actions
            </span>
          </h3>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <button
            onClick={expandAll}
            className="px-2.5 py-1 rounded bg-steel-900/60 border border-white/[0.06] text-mist-300 hover:text-white hover:bg-steel-800 transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-2.5 py-1 rounded bg-steel-900/60 border border-white/[0.06] text-mist-300 hover:text-white hover:bg-steel-800 transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {toolHistory.map((item, index) => {
          const isExpanded = !!expandedCalls[item.call_id];
          const hasError =
            !!item.error ||
            (item.exit_code !== null && item.exit_code !== undefined && item.exit_code !== 0);

          return (
            <div
              key={item.call_id || index}
              className={`rounded-xl border transition-all overflow-hidden ${
                hasError
                  ? 'border-rose-900/60 bg-rose-950/20'
                  : 'border-white/[0.07] bg-[#070a11]/90 shadow-sm'
              }`}
            >
              <div
                onClick={() => toggleExpand(item.call_id)}
                className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      hasError
                        ? 'bg-rose-900/40 text-rose-300 border border-rose-800/60'
                        : 'bg-emerald-950/40 text-emerald-300 border border-emerald-800/50'
                    }`}
                  >
                    {hasError ? (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    )}
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-semibold text-slate-100">
                        {item.tool_name}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-graphite-900 text-mist-400 border border-white/[0.06]">
                        {item.call_id}
                      </span>
                      {item.requires_approval && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-300 border border-amber-800/80 flex items-center gap-1">
                          <ShieldAlert className="w-2.5 h-2.5" />
                          <span>Approval Gate</span>
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-mist-500 font-mono mt-0.5">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-mist-600" />
                        <span>{item.execution_time_ms.toFixed(1)} ms</span>
                      </span>
                      {item.exit_code !== null && item.exit_code !== undefined && (
                        <span className={item.exit_code === 0 ? 'text-mist-400' : 'text-rose-400'}>
                          Exit Code: {item.exit_code}
                        </span>
                      )}
                      <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0 text-mist-400 ml-2">
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-icy-300" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-mist-500" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <div className="p-4 border-t border-white/[0.06] space-y-4 bg-[#05070c]">
                  {/* Input Arguments */}
                  <div>
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-mist-300 mb-1.5 font-mono">
                      <FileCode className="w-3.5 h-3.5 text-icy-400" />
                      <span>Input Arguments</span>
                    </div>
                    <CodeBlock
                      code={item.input_args}
                      language="json"
                      maxHeight="max-h-48"
                      title="args.json"
                    />
                  </div>

                  {/* Output */}
                  {item.output && (
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-mist-300 mb-1.5 font-mono">
                        <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Tool Output</span>
                      </div>
                      <CodeBlock
                        code={item.output}
                        language="text"
                        maxHeight="max-h-64"
                        title="stdout"
                      />
                    </div>
                  )}

                  {/* Error if present */}
                  {item.error && (
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-300 mb-1.5 font-mono">
                        <XCircle className="w-3.5 h-3.5 text-rose-400" />
                        <span>Execution Error</span>
                      </div>
                      <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-900/60 text-xs font-mono text-rose-200 whitespace-pre-wrap leading-relaxed shadow-inner-glow">
                        {item.error}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
