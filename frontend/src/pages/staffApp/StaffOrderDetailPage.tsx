import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import staffApi, { getStaffAuth } from '@/lib/staffApi';

interface OrderDetail {
  id: string;
  customer_name: string;
  customer_phone: string;
  status: string;
  total_amount: number;
  scheduled_at: string | null;
  completed_at: string | null;
  address: string;
  notes: string;
  items: { service_name: string; quantity: number; price: number }[];
  payment: { status: string; method: string; amount: number } | null;
  created_at: string;
}

const STEP_LABELS: Record<string, string> = {
  pending: '待确认', confirmed: '已确认', dispatched: '已派单',
  in_progress: '服务中', completed: '已完成', cancelled: '已取消',
};

const STEP_ORDER = ['pending', 'confirmed', 'dispatched', 'in_progress', 'completed'];

export function StaffOrderDetailPage() {
  const { staffId, orderId } = useParams<{ staffId: string; orderId: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');
  const [liveStatus, setLiveStatus] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const fetchOrder = useCallback(async () => {
    try {
      const res = await staffApi.get(`/${staffId}/orders/${orderId}`);
      setOrder(res.data);
    } catch {
      setError('加载订单详情失败');
    } finally {
      setLoading(false);
    }
  }, [staffId, orderId]);

  useEffect(() => {
    const auth = getStaffAuth();
    if (!auth || auth.staffId !== staffId) {
      navigate('/staff-app/login', { replace: true });
      return;
    }
    fetchOrder();
  }, [staffId, orderId, navigate, fetchOrder]);

  // SSE 实时状态监听
  useEffect(() => {
    if (!staffId || !orderId) return;

    const auth = getStaffAuth();
    if (!auth) return;

    const es = new EventSource(
      `/api/v1/staff-app/${staffId}/orders/${orderId}/stream`
    );

    es.addEventListener('status', (e) => {
      setLiveStatus(e.data);
      // Refresh order data when status changes
      fetchOrder();
    });
    es.addEventListener('error', () => {});
    es.addEventListener('done', () => es.close());

    eventSourceRef.current = es;
    return () => { es.close(); };
  }, [staffId, orderId, fetchOrder]);

  const handleStatusUpdate = async (newStatus: string) => {
    setUpdating(true);
    setError('');
    try {
      await staffApi.put(`/${staffId}/orders/${orderId}/status`, null, {
        params: { status: newStatus },
      });
      await fetchOrder();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '操作失败';
      setError(msg);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="text-center">
          <p className="text-4xl mb-3">😕</p>
          <p className="text-gray-900 font-medium">订单不存在</p>
          <Link to={`/staff-app/${staffId}`} className="text-blue-600 text-sm mt-2 inline-block">返回订单列表</Link>
        </div>
      </div>
    );
  }

  const currentStatus = liveStatus || order.status;
  const currentStep = STEP_ORDER.indexOf(currentStatus);
  const canStart = currentStatus === 'dispatched';
  const canComplete = currentStatus === 'in_progress';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 sticky top-0 z-30">
        <button onClick={() => navigate(-1)} className="text-blue-600 text-xl">←</button>
        <h1 className="font-bold text-gray-900">订单详情</h1>
      </div>

      <div className="px-4 py-4 space-y-4 pb-24">
        {/* Customer info */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h3 className="text-sm text-gray-500 mb-2">客户信息</h3>
          <p className="font-semibold text-gray-900 text-lg">{order.customer_name}</p>
          <p className="text-gray-600 mt-1">
            <a href={`tel:${order.customer_phone}`} className="text-blue-600">{order.customer_phone || '无电话'}</a>
          </p>
          <p className="text-gray-600 mt-1">{order.address}</p>
        </div>

        {/* Progress Steps */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h3 className="text-sm text-gray-500 mb-3">服务进度</h3>
          <div className="flex items-center">
            {STEP_ORDER.filter(s => s !== 'cancelled').map((step, idx) => {
              const stepIdx = STEP_ORDER.indexOf(step);
              let statusClass = 'bg-gray-200 text-gray-400';
              if (stepIdx < currentStep) statusClass = 'bg-green-500 text-white';
              else if (stepIdx === currentStep) statusClass = 'bg-blue-500 text-white';

              return (
                <div key={step} className="flex-1 flex flex-col items-center">
                  {idx > 0 && (
                    <div className={`absolute h-0.5 w-[calc(100%/4-2rem)] -ml-[calc(50%-1rem)] mt-3.5 ${
                      stepIdx <= currentStep ? 'bg-green-500' : 'bg-gray-200'
                    }`} style={{ position: 'relative', top: '-0.25rem' }} />
                  )}
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold relative z-10 ${statusClass}`}>
                    {stepIdx < currentStep ? '✓' : idx + 1}
                  </div>
                  <span className={`text-xs mt-1 ${stepIdx <= currentStep ? 'text-gray-900 font-medium' : 'text-gray-400'}`}>
                    {STEP_LABELS[step]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Service Items */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h3 className="text-sm text-gray-500 mb-2">服务项目</h3>
          {order.items.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <span className="text-gray-900">{item.service_name}</span>
              <div className="text-right">
                <span className="text-gray-500 text-sm">×{item.quantity}</span>
                <span className="text-gray-900 font-medium ml-3">¥{(item.price * item.quantity).toFixed(2)}</span>
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between pt-3 mt-1 border-t border-gray-100">
            <span className="font-semibold text-gray-900">合计</span>
            <span className="font-bold text-lg text-gray-900">¥{order.total_amount}</span>
          </div>
        </div>

        {/* Schedule */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h3 className="text-sm text-gray-500 mb-2">时间信息</h3>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">预约时间</span>
            <span className="text-gray-900 font-medium">
              {order.scheduled_at ? new Date(order.scheduled_at).toLocaleString('zh-CN') : '待定'}
            </span>
          </div>
          {order.completed_at && (
            <div className="flex justify-between text-sm mt-2">
              <span className="text-gray-500">完成时间</span>
              <span className="text-gray-900 font-medium">
                {new Date(order.completed_at).toLocaleString('zh-CN')}
              </span>
            </div>
          )}
        </div>

        {/* Payment */}
        {order.payment && (
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h3 className="text-sm text-gray-500 mb-2">支付信息</h3>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">支付状态</span>
              <span className={`font-medium ${order.payment.status === 'paid' ? 'text-green-600' : 'text-yellow-600'}`}>
                {order.payment.status === 'paid' ? '已支付' : order.payment.status === 'pending' ? '待支付' : order.payment.status}
              </span>
            </div>
          </div>
        )}

        {/* Notes */}
        {order.notes && (
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h3 className="text-sm text-gray-500 mb-2">备注</h3>
            <p className="text-gray-900 text-sm">{order.notes}</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 text-red-600 rounded-xl p-3 text-sm">{error}</div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          {canStart && (
            <button
              onClick={() => handleStatusUpdate('in_progress')}
              disabled={updating}
              className="flex-1 bg-blue-600 text-white py-3.5 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {updating ? '处理中...' : '🚀 开始服务'}
            </button>
          )}
          {canComplete && (
            <button
              onClick={() => handleStatusUpdate('completed')}
              disabled={updating}
              className="flex-1 bg-green-600 text-white py-3.5 rounded-xl font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {updating ? '处理中...' : '✅ 完成服务'}
            </button>
          )}
        </div>
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2 px-6 flex justify-around">
        <Link to={`/staff-app/${staffId}`} className="flex flex-col items-center text-gray-400">
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
