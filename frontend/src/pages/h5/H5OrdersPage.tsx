import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import h5Api, { setH5Auth, getH5CustomerId, getH5Token } from '@/lib/h5Api';
import type { H5Order, H5CompanyInfo } from '@/types';

const STATUS_LABELS: Record<string, string> = {
  pending: '待确认',
  confirmed: '已确认',
  dispatched: '已派单',
  in_progress: '服务中',
  completed: '已完成',
  cancelled: '已取消',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-blue-100 text-blue-700',
  dispatched: 'bg-indigo-100 text-indigo-700',
  in_progress: 'bg-cyan-100 text-cyan-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-500',
};

/**
 * H5 订单列表页
 * URL: /h5/:customerId/orders
 */
export function H5OrdersPage() {
  const { customerId } = useParams<{ customerId: string }>();

  const [orders, setOrders] = useState<H5Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = getH5Token();
    if (!token || !customerId) {
      setError('未登录，请通过链接访问');
      setLoading(false);
      return;
    }
    h5Api.get<{ success: boolean; data: { items: H5Order[] } }>(`/${customerId}/orders`)
      .then(({ data }) => setOrders(data.data.items))
      .catch(() => setError('加载订单失败'))
      .finally(() => setLoading(false));
  }, [customerId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center animate-pulse text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="text-5xl mb-4">🔗</div>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-5 flex items-center gap-3">
        <Link to={`/h5/${customerId}`} className="text-white/80 hover:text-white text-xl">←</Link>
        <div>
          <h1 className="text-lg font-bold">我的订单</h1>
          <p className="text-blue-100 text-sm">共 {orders.length} 笔</p>
        </div>
      </div>

      {/* Order List */}
      <div className="p-4 space-y-3">
        {orders.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-4xl mb-3">📭</p>
            <p className="text-gray-500">暂无订单</p>
            <Link
              to={`/h5/${customerId}`}
              className="inline-block mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg text-sm"
            >
              去下单
            </Link>
          </div>
        ) : (
          orders.map((order) => (
            <Link
              key={order.id}
              to={`/h5/${customerId}/orders/${order.id}`}
              className="block bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:border-blue-200 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-gray-900 text-sm">
                    {order.items?.map((i) => i.service_name || '服务').join('、') || '家政服务'}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {order.created_at ? new Date(order.created_at).toLocaleDateString('zh-CN') : ''}
                  </p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[order.status] || 'bg-gray-100'}`}>
                  {STATUS_LABELS[order.status] || order.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {order.staff_name ? `🧹 ${order.staff_name}` : '待分配'}
                </span>
                <span className="text-sm font-bold text-gray-900">¥{order.total_amount}</span>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex">
        <Link
          to={`/h5/${customerId}`}
          className="flex-1 text-center py-3 text-sm text-gray-500 hover:text-blue-600"
        >
          🏠 首页
        </Link>
        <Link
          to={`/h5/${customerId}/orders`}
          className="flex-1 text-center py-3 text-sm text-blue-600 font-medium border-t-2 border-blue-600"
        >
          📋 订单
        </Link>
      </nav>
    </div>
  );
}
