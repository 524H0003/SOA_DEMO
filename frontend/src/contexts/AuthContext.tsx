import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router';
import { useQueryClient } from '@tanstack/react-query';

interface AuthContextType {
  user: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const checkAuth = async () => {
    try {
      const response = await fetch(`/api/absent-requests`, {
        method: 'GET',
        credentials: 'include',
      });
      
      if (response.ok) {
        // If we can access protected resource, we're authenticated
        // Try to get username from a user info endpoint or use stored username
        const storedUser = localStorage.getItem('absent.username');
        if (storedUser) {
          setUser(storedUser);
        }
      } else {
        setUser(null);
        localStorage.removeItem('absent.username');
      }
    } catch (error) {
      setUser(null);
      localStorage.removeItem('absent.username');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await fetch(`/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Login failed');
      }
      
      // Backend sets HttpOnly cookie automatically
      // Store username in localStorage for display purposes
      localStorage.setItem('absent.username', username);
      setUser(username);
      queryClient.clear();
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await fetch(`/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      localStorage.removeItem('absent.username');
      setUser(null);
      queryClient.clear();
      navigate('/login');
    }
  };

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    isLoading,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}