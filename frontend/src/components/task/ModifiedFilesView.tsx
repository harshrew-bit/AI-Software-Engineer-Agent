import React, { useState } from 'react';
import { FileCode2, GitCompare, FilePlus, Loader2, Copy, Check } from 'lucide-react';
import { CodeBlock } from '../common/CodeBlock';

interface ModifiedFilesViewProps {
  modifiedFiles: string[];
  diff: string | null;
  diffLoading?: boolean;
}

export const ModifiedFilesView: React.FC<ModifiedFilesViewProps> = ({
  modifiedFiles,
  diff,
  diffLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState<'files' | 'diff'>('diff');
  const [copiedFile, setCopiedFile] = useState<string | null>(null);

  const hasFiles = modifiedFiles && modifiedFiles.length > 0;
  const hasDiff = !!diff && diff.trim().length > 0;

  const handleCopyPath = async (filePath: string) => {
    try {
      await navigator.clipboard.writeText(filePath);
      setCopiedFile(filePath);
      setTimeout(() => setCopiedFile(null), 2000);
    } catch (err) {
      console.error('Failed to copy file path:', err);
    }
  };

  if (!hasFiles && !hasDiff) {
    return (
      <div className="glass-panel p-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-graphite-900 border border-white/[0.06] flex items-center justify-center mx-auto mb-3 text-mist-500">
          <FileCode2 className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-200">No Modified Files Registered</h4>
        <p className="text-xs text-mist-400 mt-1 max-w-sm mx-auto">
          Files edited or created by the agent during implementation will be displayed here with unified git diffs.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      {/* Top subtle warm champagne highlight */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-champagne-300/30 to-transparent pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5 pb-4 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span className="text-[10px] font-mono text-mist-400 uppercase tracking-widest">
              Workspace Diffs
            </span>
          </div>
          <h3 className="text-sm md:text-base font-bold text-white flex items-center gap-2 mt-0.5">
            <FileCode2 className="w-4 h-4 text-emerald-400" />
            <span>Repository Modifications</span>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-champagne-200">
              {modifiedFiles.length} {modifiedFiles.length === 1 ? 'file' : 'files'}
            </span>
          </h3>
        </div>

        {/* View Toggle Tabs */}
        <div className="flex items-center gap-1 bg-midnight-950/80 p-1 rounded-xl border border-white/[0.08] text-xs font-mono">
          <button
            onClick={() => setActiveTab('diff')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'diff'
                ? 'bg-white/[0.08] text-white shadow-sm border border-copper-400/40 font-semibold shadow-inner-copper'
                : 'text-mist-400 hover:text-slate-200'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5 text-copper-400" />
            <span>Unified Diff</span>
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'files'
                ? 'bg-white/[0.08] text-white shadow-sm border border-copper-400/40 font-semibold shadow-inner-copper'
                : 'text-mist-400 hover:text-slate-200'
            }`}
          >
            <FilePlus className="w-3.5 h-3.5 text-emerald-400" />
            <span>File List ({modifiedFiles.length})</span>
          </button>
        </div>
      </div>

      {activeTab === 'diff' ? (
        <div>
          {diffLoading ? (
            <div className="p-12 text-center text-mist-400 text-xs flex items-center justify-center gap-2 font-mono">
              <Loader2 className="w-4 h-4 animate-spin text-copper-400" />
              <span>Fetching unified git diff stream...</span>
            </div>
          ) : hasDiff ? (
            <CodeBlock
              code={diff}
              language="diff"
              maxHeight="max-h-[32rem]"
              title="git diff --staged"
            />
          ) : (
            <div className="p-8 text-center text-mist-500 text-xs italic font-mono">
              No active diff currently staged in the workspace.
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {modifiedFiles.map((file, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-[#070a11] border border-white/[0.06] flex items-center justify-between gap-3 font-mono text-xs text-slate-200 group hover:border-white/[0.12] transition-colors"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <FilePlus className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="truncate">{file}</span>
              </div>

              <button
                onClick={() => handleCopyPath(file)}
                className="p-1 text-mist-500 hover:text-white transition-colors flex-shrink-0"
                title="Copy relative file path"
              >
                {copiedFile === file ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
