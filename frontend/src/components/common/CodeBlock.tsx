import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';

interface CodeBlockProps {
  code: string | object | null | undefined;
  language?: string;
  maxHeight?: string;
  title?: string;
  collapsed?: boolean;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'text',
  maxHeight = 'max-h-72',
  title,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  const formattedCode =
    typeof code === 'object' && code !== null
      ? JSON.stringify(code, null, 2)
      : String(code || '');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formattedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  if (!formattedCode) {
    return <div className="text-xs text-slate-500 italic">No content</div>;
  }

  return (
    <div className="rounded-lg border border-slate-800 bg-[#070b14] overflow-hidden">
      {title && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900/90 border-b border-slate-800/80 text-xs font-mono text-slate-400">
          <span className="truncate">{title}</span>
          <span className="text-[10px] text-slate-500 uppercase">{language}</span>
        </div>
      )}
      <div className="relative group">
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 p-1.5 rounded-md bg-slate-800/80 text-slate-400 opacity-0 group-hover:opacity-100 hover:text-white hover:bg-slate-700 transition-all text-xs flex items-center gap-1 backdrop-blur-sm z-10"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[10px] text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span className="text-[10px]">Copy</span>
            </>
          )}
        </button>
        <pre
          className={`p-3 font-mono text-xs text-slate-300 overflow-x-auto overflow-y-auto ${maxHeight} leading-relaxed select-text whitespace-pre`}
        >
          <code>{formattedCode}</code>
        </pre>
      </div>
    </div>
  );
};
