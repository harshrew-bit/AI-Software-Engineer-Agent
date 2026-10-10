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
    return <div className="text-xs text-mist-500 italic p-3">No content available</div>;
  }

  const isDiff = language.toLowerCase() === 'diff';

  return (
    <div className="rounded-lg border border-white/[0.08] bg-[#070a11] overflow-hidden shadow-inner-glow">
      {title && (
        <div className="flex items-center justify-between px-3.5 py-2 bg-graphite-900/90 border-b border-white/[0.06] text-xs font-mono text-mist-300">
          <span className="truncate font-medium">{title}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-mist-400 uppercase tracking-wider">
            {language}
          </span>
        </div>
      )}
      <div className="relative group">
        <button
          onClick={handleCopy}
          className="absolute top-2.5 right-2.5 p-1.5 rounded-md bg-steel-900/90 border border-white/[0.08] text-mist-400 opacity-0 group-hover:opacity-100 hover:text-white hover:bg-steel-800 transition-all text-xs flex items-center gap-1.5 backdrop-blur-sm z-10 shadow-sm"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[10px] text-emerald-400 font-mono">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span className="text-[10px] font-mono">Copy</span>
            </>
          )}
        </button>

        <pre
          className={`p-3.5 font-mono text-xs text-slate-200 overflow-x-auto overflow-y-auto ${maxHeight} leading-relaxed select-text whitespace-pre`}
        >
          {isDiff ? (
            <code>
              {formattedCode.split('\n').map((line, idx) => {
                let lineClass = 'text-slate-300';
                if (line.startsWith('+') && !line.startsWith('+++')) {
                  lineClass = 'text-emerald-300 bg-emerald-950/40 -mx-3.5 px-3.5 block border-l-2 border-emerald-500';
                } else if (line.startsWith('-') && !line.startsWith('---')) {
                  lineClass = 'text-rose-300 bg-rose-950/40 -mx-3.5 px-3.5 block border-l-2 border-rose-500';
                } else if (line.startsWith('@@')) {
                  lineClass = 'text-icy-300 bg-sky-950/30 -mx-3.5 px-3.5 block font-semibold';
                }
                return (
                  <span key={idx} className={lineClass}>
                    {line}
                    {'\n'}
                  </span>
                );
              })}
            </code>
          ) : (
            <code>{formattedCode}</code>
          )}
        </pre>
      </div>
    </div>
  );
};

