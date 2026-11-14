import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { PreferencesProvider } from './context/PreferencesContext';
import { AppShell } from './components/layout/AppShell';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { NewScreeningPage } from './pages/NewScreeningPage';
import { QualityAssessmentPage } from './pages/QualityAssessmentPage';
import { ExtractionPage } from './pages/ExtractionPage';
import { MRZStudioPage } from './pages/MRZStudioPage';
import { ForensicLabPage } from './pages/ForensicLabPage';
import { FaceVerificationPage } from './pages/FaceVerificationPage';
import { RiskResultsPage } from './pages/RiskResultsPage';
import { QuickCheckPage } from './pages/QuickCheckPage';
import { HelpCenterPage } from './pages/HelpCenterPage';
import { CaseQueuePage } from './pages/CaseQueuePage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { AuditPage } from './pages/AuditPage';
import { EngineStatusPage } from './pages/EngineStatusPage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { AdminConfigPage } from './pages/AdminConfigPage';
import { AdminSelfTestPage } from './pages/AdminSelfTestPage';
import { NotFoundPage } from './pages/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          <span className="text-xs font-mono text-slate-500">Initializing Security Context...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <PreferencesProvider>
          <BrowserRouter>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Application Workspace */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="quick-check" element={<QuickCheckPage />} />
              <Route path="help" element={<HelpCenterPage />} />
              
              {/* Screening & Processing Pipeline */}
              <Route path="screenings" element={<Navigate to="/cases" replace />} />
              <Route path="screenings/new" element={<NewScreeningPage />} />
              <Route path="screenings/:id/quality" element={<QualityAssessmentPage />} />
              <Route path="screenings/:id/extraction" element={<ExtractionPage />} />
              <Route path="screenings/:id/mrz" element={<MRZStudioPage />} />
              <Route path="screenings/:id/forensics" element={<ForensicLabPage />} />
              <Route path="screenings/:id/face" element={<FaceVerificationPage />} />
              <Route path="screenings/:id/risk" element={<RiskResultsPage />} />
              
              {/* Investigation Cases */}
              <Route path="cases" element={<CaseQueuePage />} />
              <Route path="cases/:id" element={<CaseDetailPage />} />

              {/* Cryptographic Audit Ledger */}
              <Route path="audit" element={<AuditPage />} />

              {/* Admin & System Health */}
              <Route path="admin/engine-status" element={<EngineStatusPage />} />
              <Route path="admin/self-test" element={<AdminSelfTestPage />} />
              <Route path="admin/users" element={<AdminUsersPage />} />
              <Route path="admin/config" element={<AdminConfigPage />} />
            </Route>

            {/* 404 Route */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
        </PreferencesProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
