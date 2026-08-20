import React from 'react';
import { Bot, Terminal, Shield, ArrowLeft } from 'lucide-react';

interface NavbarProps {
  onBackToDashboard?: () => void;
  showBack?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  onBackToDashboard,
  showBack = false,
}) => {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-slate-800 bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {showBack && onBackToDashboard && (
            <button
              onClick={onBackToDashboard}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Back to Dashboard"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}

          <div
            onClick={onBackToDashboard}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-500 p-0.5 shadow-lg shadow-primary-500/20 group-hover:scale-105 transition-transform">
              <div className="w-full h-full bg-background rounded-[10px] flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-100 text-base tracking-tight">
                  AI Software Engineer Agent
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-primary-950/80 text-primary-400 border border-primary-800/60 font-medium">
                  v0.1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Autonomous LangGraph Engineer with Docker Sandbox
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-4 text-xs text-slate-400 border-r border-slate-800 pr-4">
            <div className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Sandbox Isolated</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-cyan-400" />
              <span>LangGraph Multi-Turn</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-mono text-slate-300">Backend Ready</span>
          </div>
        </div>
      </div>
    </header>
  );
};
