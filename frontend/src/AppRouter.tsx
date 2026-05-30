import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, Outlet } from 'react-router-dom';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useAuthStore } from '@/stores/authStore';
import { Toaster } from '@/components/ui/toaster';

// Lazy load pages
const LandingPage = lazy(() => import('@/components/LandingPage'));
const SearchPage = lazy(() => import('@/pages/SearchPage').then(m => ({ default: m.SearchPage })));
const SavedPapersPage = lazy(() => import('@/pages/SavedPapersPage').then(m => ({ default: m.SavedPapersPage })));
const AlertsPage = lazy(() => import('@/pages/AlertsPage').then(m => ({ default: m.AlertsPage })));
const LoginPage = lazy(() => import('@/pages/LoginPage').then(m => ({ default: m.LoginPage })));

// Loading fallback
function PageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );
}

/**
 * App layout — no sidebar.
 * Tiap halaman bertanggung jawab atas top nav-nya sendiri (LandingPage punya
 * TopNav internal; halaman lain bisa pakai pattern serupa nanti).
 */
function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Outlet />
      <Toaster />
    </div>
  );
}

// Landing page wrapper
function LandingPageWrapper() {
  const navigate = useNavigate();
  return (
    <LandingPage
      onSearch={(query: string) => {
        navigate('/search?q=' + encodeURIComponent(query));
      }}
    />
  );
}

export function AppRouter() {
  const { initializeAuth } = useAuthStore();

  // Initialize auth on app load
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Login page (standalone, full screen) */}
            <Route path="/login" element={<LoginPage />} />

            {/* All other pages share the bare layout */}
            <Route element={<AppLayout />}>
              <Route path="/" element={<LandingPageWrapper />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/saved" element={<SavedPapersPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
