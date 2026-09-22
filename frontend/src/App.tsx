import {  Routes, Route } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { LoginPage } from '@/components/LoginPage';
import { AbsentRequestPage } from '@/components/AbsentRequestPage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
          <Routes>
            <Route path='/login' element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path='/' element={<AbsentRequestPage />} />
            </Route>
          </Routes>
      </AuthProvider>
    </QueryClientProvider>
  );
}
