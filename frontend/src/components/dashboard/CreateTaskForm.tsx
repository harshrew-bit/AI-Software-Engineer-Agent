import React, { useState } from 'react';
import {
  Play,
  GitFork,
  Sparkles,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  GitBranch,
  RotateCcw,
  Terminal,
} from 'lucide-react';
import { createTask } from '../../api/tasks';
import type { CreateTaskRequest, TaskResponse } from '../../types/task';

interface CreateTaskFormProps {
  onTaskCreated: (task: TaskResponse) => void;
}

export const CreateTaskForm: React.FC<CreateTaskFormProps> = ({ onTaskCreated }) => {
  const [repositoryUrl, setRepositoryUrl] = useState<string>('https://github.com/harshrew-bit/my-agent-test');
  const [userInstruction, setUserInstruction] = useState<string>(
    'Add a simple /hello endpoint that returns {"message": "Hello World"}. Add a unit test for it.'
  );
  const [baseBranch, setBaseBranch] = useState<string>('main');
  const [workingBranch, setWorkingBranch] = useState<string>('');
  const [maxRetries, setMaxRetries] = useState<number>(5);

  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const presets = [
    {
      name: 'Hello World Endpoint',
      instruction: 'Add a simple /hello endpoint that returns {"message": "Hello World"}. Add a unit test for it.',
    },
    {
      name: 'Add Health Check',
      instruction: 'Implement a /health endpoint returning {"status": "ok", "uptime": float} with thorough unit tests.',
    },
    {
      name: 'Input Validation Fix',
      instruction: 'Add Pydantic validation to user input models and write test cases for edge cases.',
    },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Form Validation
    const cleanRepo = repositoryUrl.trim();
    const cleanInstruction = userInstruction.trim();

    if (!cleanRepo) {
      setError('GitHub Repository URL is required.');
      return;
    }

    if (!cleanRepo.startsWith('http://') && !cleanRepo.startsWith('https://') && !cleanRepo.startsWith('git@')) {
      setError('Please provide a valid repository URL (e.g. https://github.com/owner/repo).');
      return;
    }

    if (!cleanInstruction || cleanInstruction.length < 5) {
      setError('User instruction must be at least 5 characters long.');
      return;
    }

    setSubmitting(true);

    try {
      const payload: CreateTaskRequest = {
        repository_url: cleanRepo,
        user_instruction: cleanInstruction,
        base_branch: baseBranch.trim() || 'main',
        working_branch: workingBranch.trim() || undefined,
        max_retries: Number(maxRetries) || 5,
      };

      const task = await createTask(payload);
      onTaskCreated(task);
    } catch (err: any) {
      console.error('Failed to create task:', err);
      setError(err.message || 'Failed to start task. Please check server logs.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="glass-panel p-6 md:p-8 relative overflow-hidden">
      {/* Subtle top edge warm champagne specular highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-champagne-300/30 to-transparent pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-white/[0.06] gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-copper-400"></span>
            <span className="text-[11px] font-mono text-mist-400 uppercase tracking-widest">
              Task Initiation
            </span>
          </div>
          <h2 className="text-lg md:text-xl font-bold text-white tracking-tight flex items-center gap-2 mt-1">
            <Terminal className="w-5 h-5 text-copper-400" />
            <span>Launch Engineering Task</span>
          </h2>
          <p className="text-xs text-mist-300 mt-1">
            Agent clones repository, inspects architecture, writes code, verifies in Docker, and pushes pull request.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-mist-300">
          <span className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[11px]">
            Branch Isolation
          </span>
          <span className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[11px]">
            Docker Sandbox
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs flex items-start gap-2.5 backdrop-blur-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-rose-400" />
            <span className="leading-relaxed">{error}</span>
          </div>
        )}

        {/* GitHub Repository URL */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs font-semibold text-mist-200 tracking-wide font-sans">
              Repository Location <span className="text-rose-400">*</span>
            </label>
            <span className="text-[11px] font-mono text-mist-400">Public or Private (with git credentials)</span>
          </div>

          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-mist-400 group-focus-within:text-copper-400 transition-colors">
              <GitFork className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={repositoryUrl}
              onChange={(e) => setRepositoryUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              disabled={submitting}
              className="w-full pl-10 pr-4 py-2.5 bg-midnight-950/80 border border-white/[0.08] rounded-xl text-xs md:text-sm text-slate-100 placeholder-mist-600 focus:outline-none focus:border-copper-400/70 focus:ring-1 focus:ring-copper-400/30 transition-all font-mono shadow-inner-copper disabled:opacity-50"
            />
          </div>
        </div>

        {/* Instruction Templates & Textarea */}
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
            <label className="block text-xs font-semibold text-mist-200 tracking-wide font-sans">
              Engineering Prompt &amp; Specification <span className="text-rose-400">*</span>
            </label>
            <span className="text-[11px] text-mist-400">Select template:</span>
          </div>

          {/* Quick Preset Buttons (Styled as Image 2 Reference Chips) */}
          <div className="flex flex-wrap gap-2 mb-3">
            {presets.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setUserInstruction(preset.instruction)}
                disabled={submitting}
                className="text-xs font-sans px-3 py-1.5 rounded-full bg-white/[0.04] text-mist-200 hover:bg-white/[0.08] hover:text-white border border-white/[0.08] hover:border-copper-400/40 transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5 text-copper-400" />
                <span>{preset.name}</span>
              </button>
            ))}
          </div>

          <textarea
            rows={4}
            value={userInstruction}
            onChange={(e) => setUserInstruction(e.target.value)}
            placeholder="Describe what the agent should implement, fix, or test in natural language..."
            disabled={submitting}
            className="w-full p-3.5 bg-midnight-950/80 border border-white/[0.08] rounded-xl text-xs md:text-sm text-slate-100 placeholder-mist-600 focus:outline-none focus:border-copper-400/70 focus:ring-1 focus:ring-copper-400/30 transition-all resize-y leading-relaxed font-sans shadow-inner-copper disabled:opacity-50"
          />
        </div>

        {/* Advanced Options Toggle */}
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-mist-400 hover:text-champagne-300 flex items-center gap-1.5 transition-colors font-mono"
          >
            <span>Advanced Configuration</span>
            {showAdvanced ? (
              <ChevronUp className="w-3.5 h-3.5 text-copper-400" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-mist-500" />
            )}
          </button>

          {showAdvanced && (
            <div className="mt-3 p-4 rounded-xl bg-midnight-950/70 border border-white/[0.08] grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-[11px] font-medium text-mist-400 uppercase tracking-wider mb-1.5 font-mono flex items-center gap-1">
                  <GitBranch className="w-3 h-3 text-mist-400" />
                  <span>Base Branch</span>
                </label>
                <input
                  type="text"
                  value={baseBranch}
                  onChange={(e) => setBaseBranch(e.target.value)}
                  placeholder="main"
                  disabled={submitting}
                  className="w-full px-3 py-1.5 bg-midnight-950/90 border border-white/[0.08] rounded-lg text-xs text-slate-200 font-mono focus:outline-none focus:border-copper-400/70"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-mist-400 uppercase tracking-wider mb-1.5 font-mono flex items-center gap-1">
                  <GitFork className="w-3 h-3 text-mist-400" />
                  <span>Custom Working Branch</span>
                </label>
                <input
                  type="text"
                  value={workingBranch}
                  onChange={(e) => setWorkingBranch(e.target.value)}
                  placeholder="auto-generated"
                  disabled={submitting}
                  className="w-full px-3 py-1.5 bg-midnight-950/90 border border-white/[0.08] rounded-lg text-xs text-slate-200 font-mono focus:outline-none focus:border-copper-400/70"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-mist-400 uppercase tracking-wider mb-1.5 font-mono flex items-center gap-1">
                  <RotateCcw className="w-3 h-3 text-mist-400" />
                  <span>Max Debug Retries</span>
                </label>
                <input
                  type="number"
                  min={1}
                  max={15}
                  value={maxRetries}
                  onChange={(e) => setMaxRetries(Number(e.target.value))}
                  disabled={submitting}
                  className="w-full px-3 py-1.5 bg-midnight-950/90 border border-white/[0.08] rounded-lg text-xs text-slate-200 font-mono focus:outline-none focus:border-copper-400/70"
                />
              </div>
            </div>
          )}
        </div>

        {/* Primary Action Button (Matching Image 2 Start Agent button) */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3.5 bg-gradient-to-r from-[#d9825b] via-[#c86f49] to-[#b05c38] hover:from-[#e28e67] hover:via-[#d1764f] hover:to-[#bc623e] text-white font-medium rounded-xl transition-all duration-200 shadow-lg shadow-copper-900/40 hover:shadow-copper-900/60 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm border border-copper-300/30 group active:scale-[0.99]"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Initializing Agent Session...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current group-hover:translate-x-0.5 transition-transform text-champagne-100" />
                <span>Start Autonomous Workflow</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
