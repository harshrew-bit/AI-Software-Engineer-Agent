import React from 'react';
import { CheckCircle2, XCircle, Terminal, Clock, ShieldCheck } from 'lucide-react';
import { CodeBlock } from '../common/CodeBlock';
import type { TestExecutionSummary } from '../../types/task';

interface TestResultsViewProps {
  testResults: TestExecutionSummary[];
}

export const TestResultsView: React.FC<TestResultsViewProps> = ({ testResults }) => {
  if (!testResults || testResults.length === 0) {
    return (
      <div className="glass-panel p-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-graphite-900 border border-white/[0.06] flex items-center justify-center mx-auto mb-3 text-mist-500">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-200">No Test Runs Executed</h4>
        <p className="text-xs text-mist-400 mt-1 max-w-sm mx-auto">
          When the agent triggers test discovery or executes verification commands inside the sandbox, telemetry will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      {/* Top subtle warm champagne highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-champagne-300/30 to-transparent pointer-events-none" />

      <div className="mb-5 pb-4 border-b border-white/[0.06] flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-copper-400"></span>
            <span className="text-[10px] font-mono text-mist-400 uppercase tracking-widest">
              Verification Suite
            </span>
          </div>
          <h3 className="text-sm md:text-base font-bold text-white flex items-center gap-2 mt-0.5">
            <ShieldCheck className="w-4 h-4 text-copper-400" />
            <span>Sandbox Test Verification</span>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-champagne-200">
              {testResults.length} {testResults.length === 1 ? 'execution' : 'executions'}
            </span>
          </h3>
        </div>
      </div>

      <div className="space-y-4">
        {testResults.map((run, idx) => {
          const isSuccess = run.passed;

          return (
            <div
              key={idx}
              className={`rounded-xl border p-4 md:p-5 transition-all shadow-sm ${
                isSuccess
                  ? 'border-emerald-800/40 bg-emerald-950/15'
                  : 'border-rose-800/50 bg-rose-950/20'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3.5 border-b border-white/[0.06]">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isSuccess
                        ? 'bg-emerald-950/50 text-emerald-300 border border-emerald-700/60'
                        : 'bg-rose-950/50 text-rose-300 border border-rose-700/60'
                    }`}
                  >
                    {isSuccess ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold text-slate-100">
                        {run.command || 'Auto-detected Test Runner'}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold border ${
                          isSuccess
                            ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700/70'
                            : 'bg-rose-950/80 text-rose-300 border-rose-700/70'
                        }`}
                      >
                        {isSuccess ? 'PASSED' : 'FAILED'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono text-mist-400 flex-wrap">
                  <span className="bg-[#070a11] px-2 py-1 rounded border border-white/[0.06]">
                    Total: <strong className="text-slate-100">{run.total_tests}</strong>
                  </span>
                  <span className="bg-[#070a11] px-2 py-1 rounded border border-white/[0.06]">
                    Failures:{' '}
                    <strong className={run.failures > 0 ? 'text-rose-400' : 'text-slate-100'}>
                      {run.failures}
                    </strong>
                  </span>
                  <span className="bg-[#070a11] px-2 py-1 rounded border border-white/[0.06]">
                    Errors:{' '}
                    <strong className={run.errors > 0 ? 'text-rose-400' : 'text-slate-100'}>
                      {run.errors}
                    </strong>
                  </span>
                  {run.duration_seconds > 0 && (
                    <span className="flex items-center gap-1 text-mist-500">
                      <Clock className="w-3 h-3" />
                      <span>{run.duration_seconds.toFixed(2)}s</span>
                    </span>
                  )}
                </div>
              </div>

              {/* STDOUT Stream */}
              {run.stdout && (
                <div className="mt-3.5">
                  <div className="text-[10px] font-mono font-medium text-mist-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                    <Terminal className="w-3 h-3 text-icy-400" />
                    <span>Standard Output (stdout)</span>
                  </div>
                  <CodeBlock
                    code={run.stdout}
                    language="text"
                    maxHeight="max-h-60"
                    title="test.stdout"
                  />
                </div>
              )}

              {/* STDERR Stream */}
              {run.stderr && (
                <div className="mt-3.5">
                  <div className="text-[10px] font-mono font-medium text-rose-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                    <XCircle className="w-3 h-3 text-rose-400" />
                    <span>Error Output (stderr)</span>
                  </div>
                  <CodeBlock
                    code={run.stderr}
                    language="text"
                    maxHeight="max-h-48"
                    title="test.stderr"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
