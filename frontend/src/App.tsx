import { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { TaskDetailPage } from './pages/TaskDetailPage';
import { TopographicBackground } from './components/common/TopographicBackground';

export function App() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('taskId') || window.location.hash.replace(/^#\/?/, '') || null;
  });

  // Sync taskId with URL query params for bookmarking and page refreshes
  useEffect(() => {
    const url = new URL(window.location.href);
    if (selectedTaskId) {
      url.searchParams.set('taskId', selectedTaskId);
    } else {
      url.searchParams.delete('taskId');
    }
    window.history.replaceState({}, '', url.toString());
  }, [selectedTaskId]);

  const handleSelectTask = (taskId: string) => {
    setSelectedTaskId(taskId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToDashboard = () => {
    setSelectedTaskId(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-midnight-950 text-slate-200 flex flex-col font-sans relative selection:bg-copper-500/30 selection:text-champagne-100">
      {/* Bespoke Topographic Intelligence Background */}
      <TopographicBackground />

      {/* Main Workspace Layer */}
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar
          showBack={!!selectedTaskId}
          onBackToDashboard={handleBackToDashboard}
        />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-12">
          {selectedTaskId ? (
            <TaskDetailPage
              taskId={selectedTaskId}
              onBack={handleBackToDashboard}
            />
          ) : (
            <DashboardPage onSelectTask={handleSelectTask} />
          )}
        </main>

        <footer className="border-t border-white/[0.06] py-5 mt-auto bg-midnight-950/70 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-mist-400 font-mono">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-copper-400/80 inline-block"></span>
              <span>Topographic Intelligence Workspace &bull; Autonomous LangGraph &amp; Docker Sandbox</span>
            </div>
            <div className="text-mist-500">
              React 18 &bull; Vite &bull; Tailwind CSS &bull; FastAPI SSE
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;

