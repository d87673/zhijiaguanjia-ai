import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import staffApi, { getStaffAuth, clearStaffAuth } from '@/lib/staffApi';

interface StaffProfile {
  id: string;
  name: string;
  phone: string;
  email: string;
  skills: string[];
  rating: number;
  current_load: number;
  is_active: boolean;
}

export function StaffProfilePage() {
  const { staffId } = useParams<{ staffId: string }>();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<StaffProfile | null>(null);

  useEffect(() => {
    const auth = getStaffAuth();
    if (!auth || auth.staffId !== staffId) {
      navigate('/staff-app/login', { replace: true });
      return;
    }
    staffApi.get(`/${staffId}/me`).then((res) => setProfile(res.data)).catch(() => {
      clearStaffAuth();
      navigate('/staff-app/login', { replace: true });
    });
  }, [staffId, navigate]);

  const handleLogout = () => {
    clearStaffAuth();
    navigate('/staff-app/login', { replace: true });
  };

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-4 pt-10 pb-8 rounded-b-3xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-lg font-bold">我的</h1>
          <button onClick={handleLogout} className="text-white/80 text-sm hover:text-white">
            退出登录
          </button>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-3xl backdrop-blur">
            {profile.name?.charAt(0) || '👤'}
          </div>
          <div>
            <p className="font-bold text-xl">{profile.name}</p>
            <p className="text-white/80 text-sm mt-0.5">{profile.phone || '无电话'}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 -mt-4 space-y-3 pb-24">
        {/* Rating Card */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">服务评分</span>
            <span className="text-2xl font-bold text-yellow-500">
              {'★'.repeat(Math.round(profile.rating))}
              {'☆'.repeat(5 - Math.round(profile.rating))}
              <span className="text-gray-900 ml-1">{profile.rating.toFixed(1)}</span>
            </span>
          </div>
        </div>

        {/* Load Card */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">当前负载</span>
            <span className={`text-lg font-bold ${profile.current_load >= 5 ? 'text-red-600' : profile.current_load >= 3 ? 'text-yellow-600' : 'text-green-600'}`}>
              {profile.current_load} 单
            </span>
          </div>
        </div>

        {/* Skills Card */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <span className="text-gray-500 block mb-3">技能标签</span>
          <div className="flex flex-wrap gap-2">
            {profile.skills?.length ? profile.skills.map((sk) => (
              <span key={sk} className="bg-blue-50 text-blue-700 text-sm rounded-full px-3 py-1.5">{sk}</span>
            )) : (
              <span className="text-gray-400 text-sm">暂无技能标签</span>
            )}
          </div>
        </div>

        {/* Contact Card */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-500">手机号</span>
            <a href={`tel:${profile.phone}`} className="text-blue-600 font-medium">{profile.phone || '未设置'}</a>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-gray-50">
            <span className="text-gray-500">邮箱</span>
            <span className="text-gray-900">{profile.email || '未设置'}</span>
          </div>
        </div>
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2 px-6 flex justify-around">
        <Link to={`/staff-app/${staffId}`} className="flex flex-col items-center text-gray-400">
          <span className="text-xl">📋</span>
          <span className="text-xs font-medium mt-0.5">订单</span>
        </Link>
        <Link to={`/staff-app/${staffId}/profile`} className="flex flex-col items-center text-blue-600">
          <span className="text-xl">👤</span>
          <span className="text-xs font-medium mt-0.5">我的</span>
        </Link>
      </nav>
    </div>
  );
}
