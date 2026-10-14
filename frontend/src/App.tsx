import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { ApiKeyProvider } from './context/ApiKeyContext';
import { Navbar } from './components/Navbar';
import { ProjectsListPage } from './pages/ProjectsListPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { DiffDetailPage } from './pages/DiffDetailPage';
import { EvaluationPage } from './pages/EvaluationPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ApiKeyProvider>
          <BrowserRouter>
          <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
            <Navbar />
            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <Routes>
                <Route path="/" element={<ProjectsListPage />} />
                <Route path="/projects" element={<ProjectsListPage />} />
                <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
                <Route path="/projects/:projectId/diff/:diffId" element={<DiffDetailPage />} />
                <Route path="/diffs/:diffId" element={<DiffDetailPage />} />
                <Route path="/evaluation" element={<EvaluationPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-400">
              Semantic Diffing for Evolving Knowledge Graphs • Temporal Ontology & Provenance Architecture
            </footer>
          </div>
        </BrowserRouter>
        </ApiKeyProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
