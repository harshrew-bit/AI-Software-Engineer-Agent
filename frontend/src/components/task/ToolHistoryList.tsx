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
      <div className="glass-card p-8 text-center">
        <Wrench className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <h4 className="text-sm font-medium text-slate-300">No Tool Invocations Yet</h4>
        <p className="text-xs text-slate-500 mt-1">
          When the agent performs file operations, test runs, or shell commands, they will be logged here in real time.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            Tool Execution Audit Trail ({toolHistory.length})
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Granular logs of every agent action executed inside the isolated sandbox.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={expandAll}
            className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {toolHistory.map((item, index) => {
          const isExpanded = !!expandedCalls[item.call_id];
          const hasError = !!item.error || (item.exit_code !== null && item.exit_code !== undefined && item.exit_code !== 0);

          return (
            <div
              key={item.call_id || index}
              className={`rounded-lg border transition-all overflow-hidden ${
                hasError
                  ? 'border-rose-900/60 bg-rose-950/20'
                  : 'border-slate-800 bg-[#070b14]/90'
              }`}
            >
              <div
                onClick={() => toggleExpand(item.call_id)}
                className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 ${
                      hasError
                        ? 'bg-rose-900/80 text-rose-300'
                        : 'bg-slate-800 text-slate-300'
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
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {item.call_id}
                      </span>
                      {item.requires_approval && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1">
                          <ShieldAlert className="w-2.5 h-2.5" />
                          Approval Gate
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono mt-0.5">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {item.execution_time_ms.toFixed(1)} ms
                      </span>
                      {item.exit_code !== null && item.exit_code !== undefined && (
                        <span>Exit Code: {item.exit_code}</span>
                      )}
                      <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0 text-slate-400">
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </div>

              {isExpanded && (
                <div className="p-4 border-t border-slate-800/80 space-y-4 bg-black/40">
                  {/* Input Arguments */}
                  <div>
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 mb-1.5 font-mono">
                      <FileCode className="w-3.5 h-3.5 text-primary-400" />
                      <span>Input Arguments</span>
                    </div>
                    <CodeBlock
                      code={item.input_args}
                      language="json"
                      maxHeight="max-h-48"
                    />
                  </div>

                  {/* Output */}
                  {item.output && (
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 mb-1.5 font-mono">
                        <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Tool Output</span>
                      </div>
                      <CodeBlock
                        code={item.output}
                        language="text"
                        maxHeight="max-h-64"
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
                      <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-900/60 text-xs font-mono text-rose-200 whitespace-pre-wrap">
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
