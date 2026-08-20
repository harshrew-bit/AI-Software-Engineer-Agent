import React, { useState } from 'react';
import { Play, GitFork, Sparkles, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
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
    <div className="glass-card p-6 md:p-8">
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-primary-400" />
            Launch Autonomous Agent Task
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Specify a target repository and prompt. The agent will clone, analyze, implement, test, and submit a PR.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        {error && (
          <div className="p-3.5 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-sm flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* GitHub Repository URL */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            GitHub Repository URL <span className="text-rose-400">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
              <GitFork className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={repositoryUrl}
              onChange={(e) => setRepositoryUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              disabled={submitting}
              className="w-full pl-10 pr-4 py-2.5 bg-[#070b14] border border-slate-700/80 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors font-mono"
            />
          </div>
        </div>

        {/* Instruction Templates */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Engineering Instruction <span className="text-rose-400">*</span>
            </label>
            <span className="text-[11px] text-slate-500">Try a template:</span>
          </div>

          <div className="flex flex-wrap gap-1.5 mb-2.5">
            {presets.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setUserInstruction(preset.instruction)}
                disabled={submitting}
                className="text-[11px] px-2.5 py-1 rounded-md bg-slate-800/90 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700/60 transition-colors"
              >
                {preset.name}
              </button>
            ))}
          </div>

          <textarea
            rows={4}
            value={userInstruction}
            onChange={(e) => setUserInstruction(e.target.value)}
            placeholder="Describe what the agent should implement, fix, or test in natural language..."
            disabled={submitting}
            className="w-full p-3.5 bg-[#070b14] border border-slate-700/80 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors resize-y leading-relaxed font-sans"
          />
        </div>

        {/* Advanced Options Toggle */}
        <div className="pt-2">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
          >
            <span>Advanced Configuration</span>
            {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showAdvanced && (
            <div className="mt-3 p-4 rounded-lg bg-slate-900/90 border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                  Base Branch
                </label>
                <input
                  type="text"
                  value={baseBranch}
                  onChange={(e) => setBaseBranch(e.target.value)}
                  placeholder="main"
                  disabled={submitting}
                  className="w-full px-3 py-1.5 bg-[#070b14] border border-slate-700/80 rounded-md text-xs text-slate-200 font-mono focus:outline-none focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                  Custom Working Branch
                </label>
                <input
                  type="text"
                  value={workingBranch}
                  onChange={(e) => setWorkingBranch(e.target.value)}
                  placeholder="auto-generated"
                  disabled={submitting}
                  className="w-full px-3 py-1.5 bg-[#070b14] border border-slate-700/80 rounded-md text-xs text-slate-200 font-mono focus:outline-none focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                  Max Debug Retries
                </label>
                <input
                  type="number"
                  min={1}
                  max={15}
                  value={maxRetries}
                  onChange={(e) => setMaxRetries(Number(e.target.value))}
                  disabled={submitting}
                  className="w-full px-3 py-1.5 bg-[#070b14] border border-slate-700/80 rounded-md text-xs text-slate-200 font-mono focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="pt-3">
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white font-medium rounded-lg transition-all shadow-lg shadow-primary-600/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Initializing Agent Task...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Start Agent Workflow</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
