import React from 'react';
import { Terminal, Shield, ArrowLeft, Compass } from 'lucide-react';


interface NavbarProps {
  onBackToDashboard?: () => void;
  showBack?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  onBackToDashboard,
  showBack = false,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-midnight-950/60 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {showBack && onBackToDashboard && (
            <button
              onClick={onBackToDashboard}
              className="px-2.5 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-mist-300 hover:text-white hover:bg-white/[0.08] transition-all flex items-center gap-1.5 text-xs font-medium shadow-sm group"
              title="Return to Workspace Overview"
            >
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
              <span className="hidden sm:inline">Workspace</span>
            </button>
          )}

          <div
            onClick={onBackToDashboard}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-copper-500/30 via-midnight-800 to-midnight-900 p-px border border-copper-400/30 shadow-inner-copper group-hover:border-champagne-300/50 transition-colors flex items-center justify-center relative overflow-hidden">
              {/* Subtle contour line graphic in icon */}
              <svg className="absolute inset-0 w-full h-full opacity-35 text-champagne-300" viewBox="0 0 36 36">
                <path d="M0,18 Q9,10 18,18 T36,18" fill="none" stroke="currentColor" strokeWidth="1" />
                <path d="M0,26 Q9,18 18,26 T36,26" fill="none" stroke="currentColor" strokeWidth="1" />
              </svg>
              <Compass className="w-4 h-4 text-champagne-200 relative z-10 group-hover:rotate-45 transition-transform duration-300" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-white text-sm tracking-tight font-sans">
                  AI Software Engineer Agent
                </span>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-copper-950/40 text-copper-300 border border-copper-600/30 font-medium tracking-wide">
                  Topographic v1.0
                </span>
              </div>
              <p className="text-[11px] text-mist-400 hidden sm:block tracking-normal font-sans">
                Autonomous LangGraph Engineer with Isolated Sandbox
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-3 text-xs text-mist-300 border-r border-white/[0.08] pr-4 font-mono">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06]">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[11px]">Sandbox Isolated</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06]">
              <Terminal className="w-3.5 h-3.5 text-champagne-300" />
              <span className="text-[11px]">Multi-Turn Engine</span>
            </div>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-700/50 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-[11px] font-mono text-emerald-300 font-medium">System Online</span>
          </div>
        </div>
      </div>
    </header>
  );
};

