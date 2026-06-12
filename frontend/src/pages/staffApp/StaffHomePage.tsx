import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import staffApi, { getStaffAuth, clearStaffAuth } from '@/lib/staffApi';

interface StaffProfile {
  id: string;
  name: string;
  phone: string;
  skills: string[];
  rating: number;
  current_load: number;
  is_active: boolean;
}

interface StaffOrder {
  id: string;
  customer_name: string;
  customer_phone: string;
  status: string;
  total_amount: number;
  scheduled_at: string | null;
  address: string;
  notes: string;
  items: { service_name: string; quantity: number; price: number }[];
  payment_status: string;
  created_at: string;
}

const STATUS_TABS = [
  { key: '', label: '全部' },
  { key: 'pending', label: '待确认' },
  { key: 'confirmed', label: '已确认' },
  { key: 'dispatched', label: '已派单' },
  { key: 'in_progress', label: '服务中' },
  { key: 'completed', label: '已完成' },
];

const STATUS_LABELS: Record<string, string> = {
  pending: '待确认', confirmed: '已确认', dispatched: '已派单',
  in_progress: '服务中', completed: '已完成', cancelled: '已取消',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-blue-100 text-blue-700',
  dispatched: 'bg-indigo-100 text-indigo-700',
  in_progress: 'bg-cyan-100 text-cyan-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
};

export function StaffHomePage() {
  const { staffId } = useParams<{ staffId: string }>();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<StaffProfile | null>(null);
  const [orders, setOrders] = useState<StaffOrder[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const auth = getStaffAuth();
    if (!auth || auth.staffId !== staffId) {
      navigate(`/staff-app/login`, { replace: true });
      return;
    }
    try {
      const [profileRes, ordersRes] = await Promise.all([
        staffApi.get(`/${staffId}/me`),
        staffApi.get(`/${staffId}/orders`, statusFilter ? { params: { status: statusFilter } } : {}),
      ]);
      setProfile(profileRes.data);
      setOrders(ordersRes.data.orders);
    } catch {
      clearStaffAuth();
      navigate(`/staff-app/login`, { replace: true });
    } finally {
      setLoading(false);
    }
  }, [staffId, statusFilter, navigate]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleLogout = () => {
    clearStaffAuth();
    navigate('/staff-app/login', { replace: true });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-8 w-8 mx-auto text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="mt-3 text-sm text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header / Profile Card */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-4 pt-6 pb-8 rounded-b-3xl">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold">智家管家 · 员工端</h1>
          <button onClick={handleLogout} className="text-white/80 text-sm hover:text-white">
            退出
          </button>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center text-2xl backdrop-blur">
            {profile?.name?.charAt(0) || '👤'}
          </div>
          <div>
            <p className="font-bold text-lg">{profile?.name}</p>
            <div className="flex items-center gap-2 text-sm text-white/80 mt-0.5">
              <span>⭐ {profile?.rating?.toFixed(1)}</span>
              <span>·</span>
              <span>📋 {profile?.current_load} 单进行中</span>
            </div>
            {profile?.skills && profile.skills.length > 0 && (
              <div className="flex gap-1 mt-1.5 flex-wrap">
                {profile.skills.map((sk) => (
                  <span key={sk} className="bg-white/20 text-white text-xs px-2 py-0.5 rounded-full">{sk}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Tabs */}
      <div className="px-4 -mt-4 mb-4">
        <div className="flex gap-1.5 bg-white rounded-xl p-1.5 shadow-sm overflow-x-auto">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors flex-1 min-w-0 ${
                statusFilter === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Orders List */}
      <div className="px-4 pb-24 space-y-3">
        {orders.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-4xl mb-3">📭</p>
            <p className="text-gray-500 text-sm">暂无{statusFilter ? STATUS_LABELS[statusFilter] : ''}订单</p>
          </div>
        ) : (
          orders.map((order) => (
            <Link
              key={order.id}
              to={`/staff-app/${staffId}/orders/${order.id}`}
              className="block bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow active:scale-[0.98]"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-semibold text-gray-900">{order.customer_name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{order.address}</p>
                </div>
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_COLORS[order.status] || 'bg-gray-100'}`}>
                  {STATUS_LABELS[order.status] || order.status}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                {order.items.slice(0, 3).map((item, i) => (
                  <span key={i} className="bg-gray-100 rounded px-2 py-0.5">{item.service_name}×{item.quantity}</span>
                ))}
                {(order.items.length || 0) > 3 && <span className="text-gray-400">+{order.items.length - 3}</span>}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">
                  {order.scheduled_at ? new Date(order.scheduled_at).toLocaleString('zh-CN') : '时间待定'}
                </span>
                <span className="font-semibold text-gray-900">¥{order.total_amount}</span>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2 px-6 flex justify-around">
        <Link to={`/staff-app/${staffId}`} className="flex flex-col items-center text-blue-600">
          <span className="text-xl">📋</span>
          <span className="text-xs font-medium mt-0.5">订单</span>
        </Link>
        <Link to={`/staff-app/${staffId}/profile`} className="flex flex-col items-center text-gray-400">
          <span className="text-xl">👤</span>
          <span className="text-xs font-medium mt-0.5">我的</span>
        </Link>
      </nav>
    </div>
  );
}
