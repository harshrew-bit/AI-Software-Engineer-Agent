import { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { TaskDetailPage } from './pages/TaskDetailPage';

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
    <div className="min-h-screen bg-background text-slate-100 flex flex-col font-sans">
      <Navbar
        showBack={!!selectedTaskId}
        onBackToDashboard={handleBackToDashboard}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {selectedTaskId ? (
          <TaskDetailPage
            taskId={selectedTaskId}
            onBack={handleBackToDashboard}
          />
        ) : (
          <DashboardPage onSelectTask={handleSelectTask} />
        )}
      </main>

      <footer className="border-t border-slate-800/80 py-6 mt-auto bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 font-mono">
          <div>AI Software Engineer Agent &bull; Autonomous LangGraph & Sandbox</div>
          <div>React 18 &bull; Vite &bull; Tailwind CSS &bull; FastAPI SSE</div>
        </div>
      </footer>
    </div>
  );
}

export default App;
