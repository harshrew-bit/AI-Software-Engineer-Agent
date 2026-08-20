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
      <div className="glass-card p-8 text-center">
        <ShieldCheck className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <h4 className="text-sm font-medium text-slate-300">No Test Runs Executed</h4>
        <p className="text-xs text-slate-500 mt-1">
          When the agent triggers test discovery or execution inside the sandbox, results and metrics will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <div className="mb-4 pb-3 border-b border-slate-800">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-primary-400" />
          Test Suite Verification ({testResults.length} {testResults.length === 1 ? 'run' : 'runs'})
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Sandboxed execution of unit and integration tests.
        </p>
      </div>

      <div className="space-y-4">
        {testResults.map((run, idx) => {
          const isSuccess = run.passed;

          return (
            <div
              key={idx}
              className={`rounded-xl border p-4 transition-all ${
                isSuccess
                  ? 'border-emerald-900/60 bg-emerald-950/20'
                  : 'border-rose-900/60 bg-rose-950/20'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-7 h-7 rounded-md flex items-center justify-center ${
                      isSuccess
                        ? 'bg-emerald-900/80 text-emerald-300'
                        : 'bg-rose-900/80 text-rose-300'
                    }`}
                  >
                    {isSuccess ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-100">
                        {run.command || 'Auto-detected Test Runner'}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-medium ${
                          isSuccess
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-rose-950 text-rose-400 border border-rose-800'
                        }`}
                      >
                        {isSuccess ? 'PASSED' : 'FAILED'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
                  <span>Total: <strong className="text-slate-200">{run.total_tests}</strong></span>
                  <span>Failures: <strong className={run.failures > 0 ? 'text-rose-400' : 'text-slate-200'}>{run.failures}</strong></span>
                  <span>Errors: <strong className={run.errors > 0 ? 'text-rose-400' : 'text-slate-200'}>{run.errors}</strong></span>
                  {run.duration_seconds > 0 && (
                    <span className="flex items-center gap-1 text-slate-500">
                      <Clock className="w-3 h-3" />
                      {run.duration_seconds.toFixed(2)}s
                    </span>
                  )}
                </div>
              </div>

              {/* STDOUT / Output */}
              {run.stdout && (
                <div className="mt-3">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 font-mono flex items-center gap-1">
                    <Terminal className="w-3 h-3 text-cyan-400" />
                    <span>Test Output (stdout)</span>
                  </div>
                  <CodeBlock
                    code={run.stdout}
                    language="text"
                    maxHeight="max-h-60"
                  />
                </div>
              )}

              {/* STDERR */}
              {run.stderr && (
                <div className="mt-3">
                  <div className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider mb-1 font-mono flex items-center gap-1">
                    <XCircle className="w-3 h-3 text-rose-400" />
                    <span>Test Errors (stderr)</span>
                  </div>
                  <CodeBlock
                    code={run.stderr}
                    language="text"
                    maxHeight="max-h-48"
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
