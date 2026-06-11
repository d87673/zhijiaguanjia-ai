import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Input, Card } from '@/components/ui';
import { useAuthStore } from '@/stores/authStore';
import api from '@/lib/api';
import type { TokenResponse } from '@/types';

export function RegisterPage() {
  const [form, setForm] = useState({ name: '', email: '', password: '', company_name: '', phone: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const update = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data } = await api.post<TokenResponse>('/auth/register', form);
      setAuth(data.user, data.access_token, data.refresh_token);
      navigate('/dashboard');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || '注册失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
      <Card className="w-full max-w-md" padding="lg">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-blue-600">创建账号</h1>
          <p className="text-gray-500 mt-1">注册您的家政公司</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="您的姓名" value={form.name} onChange={update('name')} placeholder="张经理" required />
          <Input label="公司名称" value={form.company_name} onChange={update('company_name')} placeholder="XX家政服务有限公司" required />
          <Input label="邮箱" type="email" value={form.email} onChange={update('email')} placeholder="admin@example.com" required />
          <Input label="手机号" type="tel" value={form.phone} onChange={update('phone')} placeholder="选填" />
          <Input label="密码" type="password" value={form.password} onChange={update('password')} placeholder="至少8位字符" required minLength={8} />
          {error && (
            <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2.5">{error}</div>
          )}
          <Button type="submit" loading={loading} className="w-full">
            注册
          </Button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          已有账号？{' '}
          <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
            去登录
          </Link>
        </p>
      </Card>
    </div>
  );
}
