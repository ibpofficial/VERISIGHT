import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, UserRole } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (allowedRoles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('verisight_access_token');
      const cachedUser = localStorage.getItem('verisight_user');
      if (token && cachedUser) {
        try {
          setUser(JSON.parse(cachedUser));
          // Verify with backend
          const freshUser = await authApi.getMe();
          setUser(freshUser);
          localStorage.setItem('verisight_user', JSON.stringify(freshUser));
        } catch (err) {
          localStorage.removeItem('verisight_access_token');
          localStorage.removeItem('verisight_refresh_token');
          localStorage.removeItem('verisight_user');
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    localStorage.setItem('verisight_access_token', res.access_token);
    localStorage.setItem('verisight_refresh_token', res.refresh_token);
    const userInfo: User = {
      id: res.user_id,
      email: res.email,
      full_name: res.full_name,
      role: res.role,
      is_active: true,
      created_at: new Date().toISOString(),
    };
    setUser(userInfo);
    localStorage.setItem('verisight_user', JSON.stringify(userInfo));
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
  };

  const hasRole = (allowedRoles: UserRole[]) => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
