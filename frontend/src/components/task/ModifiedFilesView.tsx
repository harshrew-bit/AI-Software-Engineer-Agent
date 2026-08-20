import React, { useState } from 'react';
import { FileCode2, GitCompare, FilePlus, Loader2 } from 'lucide-react';
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

  const hasFiles = modifiedFiles && modifiedFiles.length > 0;
  const hasDiff = !!diff && diff.trim().length > 0;

  if (!hasFiles && !hasDiff) {
    return (
      <div className="glass-card p-8 text-center">
        <FileCode2 className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <h4 className="text-sm font-medium text-slate-300">No Modified Files</h4>
        <p className="text-xs text-slate-500 mt-1">
          Files created or modified by the agent will be catalogued here.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-emerald-400" />
            Repository Changes ({modifiedFiles.length} files)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time track of all created, edited, or deleted files.
          </p>
        </div>

        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('diff')}
            className={`px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === 'diff'
                ? 'bg-primary-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Unified Diff</span>
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === 'files'
                ? 'bg-primary-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FilePlus className="w-3.5 h-3.5" />
            <span>File List ({modifiedFiles.length})</span>
          </button>
        </div>
      </div>

      {activeTab === 'diff' ? (
        <div>
          {diffLoading ? (
            <div className="p-8 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary-400" />
              <span>Fetching unified git diff...</span>
            </div>
          ) : hasDiff ? (
            <CodeBlock
              code={diff}
              language="diff"
              maxHeight="max-h-96"
              title="git diff"
            />
          ) : (
            <div className="p-6 text-center text-slate-500 text-xs italic">
              No active diff currently pending.
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {modifiedFiles.map((file, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-[#070b14] border border-slate-800 flex items-center gap-2.5 font-mono text-xs text-slate-200"
            >
              <FilePlus className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span className="truncate">{file}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
