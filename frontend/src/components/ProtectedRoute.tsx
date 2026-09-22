import { Navigate, Outlet } from 'react-router';
import { useAuth } from '@/hooks/useAuth';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to='/login' replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}