import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { setStaffAuth } from '@/lib/staffApi';
import staffApi from '@/lib/staffApi';

/**
 * 员工端登录页 — 输入员工 ID + Token 登录
 * 实际使用中，管理员在后台为员工生成带 token 的链接
 */
export function StaffLoginPage() {
  const navigate = useNavigate();
  const [staffId, setStaffId] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!staffId.trim() || !token.trim()) {
      setError('请输入员工 ID 和访问令牌');
      return;
    }
    setLoading(true);
    setError('');
    try {
      setStaffAuth(staffId.trim(), token.trim());
      // 验证 token 是否有效
      await staffApi.get(`/${staffId}/me`);
      navigate(`/staff-app/${staffId}`, { replace: true });
    } catch {
      setError('登录失败，请检查员工 ID 和令牌是否正确');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-500 to-blue-700 flex flex-col items-center justify-center p-6">
      <div className="text-center mb-8">
        <div className="w-20 h-20 bg-white/20 rounded-3xl flex items-center justify-center mx-auto mb-4 backdrop-blur">
          <span className="text-4xl">🧹</span>
        </div>
        <h1 className="text-2xl font-bold text-white">智家管家 · 员工端</h1>
        <p className="text-blue-100 mt-2 text-sm">登录接收派单和更新服务进度</p>
      </div>

      <form onSubmit={handleLogin} className="w-full max-w-sm bg-white rounded-2xl p-6 shadow-xl space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">员工 ID</label>
          <input
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={staffId}
            onChange={(e) => setStaffId(e.target.value)}
            placeholder="管理员提供的员工编号"
            autoComplete="off"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">访问令牌</label>
          <input
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="管理员提供的访问令牌"
            autoComplete="off"
          />
        </div>
        {error && (
          <div className="bg-red-50 text-red-600 text-sm rounded-lg p-3">{error}</div>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? '登录中...' : '登录'}
        </button>
        <p className="text-xs text-gray-400 text-center">
          请向管理员索取员工 ID 和访问令牌
        </p>
      </form>

      <Link to="/login" className="mt-6 text-blue-100 text-sm hover:text-white transition-colors">
        管理端登录 →
      </Link>
    </div>
  );
}
