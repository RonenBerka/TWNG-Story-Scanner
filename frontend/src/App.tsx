import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./lib/auth";
import AppLayout from "./components/layout/AppLayout";
import Login from "./pages/Login";
import Scanner from "./pages/Scanner";
import Extraction from "./pages/Extraction";
import Approval from "./pages/Approval";
import Claims from "./pages/Claims";
import Viewer from "./pages/Viewer";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/extraction" element={<Extraction />} />
              <Route path="/approval" element={<Approval />} />
              <Route path="/claims" element={<Claims />} />
            </Route>
            {/* Compat redirects */}
            <Route path="/inbox" element={<Navigate to="/scanner" replace />} />
            <Route path="/viewer" element={<ProtectedRoute><Viewer /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/scanner" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
