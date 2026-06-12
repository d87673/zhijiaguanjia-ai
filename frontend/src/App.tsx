import { useEffect } from 'react';
import { AppRouter } from '@/components/AppRouter';
import { useAuthStore } from '@/stores/authStore';
import api from '@/lib/api';
import type { User } from '@/types';

export default function App() {
  const { initialize, setUser, setAuth, logout } = useAuthStore();

  useEffect(() => {
    // Try to fetch current user on mount
    const token = localStorage.getItem('access_token');
    if (token) {
      api.get<User>('/auth/me')
        .then((res) => {
          setAuth(res.data, token, localStorage.getItem('refresh_token') || '');
        })
        .catch(() => {
          initialize();
        });
    } else {
      initialize();
    }
  }, []);

  useEffect(() => {
    // Listen for auth:logout event from api interceptor (soft navigation)
    const handleAuthLogout = () => {
      logout();
    };
    window.addEventListener('auth:logout', handleAuthLogout);
    return () => window.removeEventListener('auth:logout', handleAuthLogout);
  }, [logout]);

  return <AppRouter />;
}
