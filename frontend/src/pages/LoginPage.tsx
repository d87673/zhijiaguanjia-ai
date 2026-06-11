import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Input, Card } from '@/components/ui';
import { useAuthStore } from '@/stores/authStore';
import api from '@/lib/api';
import type { TokenResponse } from '@/types';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data } = await api.post<TokenResponse>('/auth/login', { email, password });
      setAuth(data.user, data.access_token, data.refresh_token);
      navigate('/dashboard');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
      <Card className="w-full max-w-md" padding="lg">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-blue-600">智家管家AI</h1>
          <p className="text-gray-500 mt-1">家政智能管理系统</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="邮箱"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@example.com"
            required
          />
          <Input
            label="密码"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="请输入密码"
            required
          />
          {error && (
            <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2.5">
              {error}
            </div>
          )}
          <Button type="submit" loading={loading} className="w-full">
            登录
          </Button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          还没有账号？{' '}
          <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">
            立即注册
          </Link>
        </p>
      </Card>
    </div>
  );
}
