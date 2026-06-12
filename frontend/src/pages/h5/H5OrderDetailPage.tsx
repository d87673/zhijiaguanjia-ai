import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import h5Api, { getH5Token } from '@/lib/h5Api';
import type { H5Order } from '@/types';

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

const STATUS_STEPS = ['pending', 'confirmed', 'dispatched', 'in_progress', 'completed'];

/**
 * H5 订单详情 + 实时状态追踪
 * URL: /h5/:customerId/orders/:orderId
 */
export function H5OrderDetailPage() {
  const { customerId, orderId } = useParams<{ customerId: string; orderId: string }>();
  const [order, setOrder] = useState<H5Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [liveStatus, setLiveStatus] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // 初次加载
  useEffect(() => {
    const token = getH5Token();
    if (!token || !customerId) {
      setError('未登录');
      setLoading(false);
      return;
    }
    h5Api.get<{ success: boolean; data: H5Order }>(`/${customerId}/orders/${orderId}`)
      .then(({ data }) => {
        setOrder(data.data);
        setLiveStatus(data.data.status);
      })
      .catch(() => setError('加载订单详情失败'))
      .finally(() => setLoading(false));
  }, [customerId, orderId]);

  // SSE 实时状态
  useEffect(() => {
    if (!customerId || !orderId || !order) return;
    if (order.status === 'completed' || order.status === 'cancelled') return;

    const token = getH5Token();
    const url = `/api/v1/h5/${customerId}/orders/${orderId}/stream`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        setLiveStatus(d.status);
        if (d.done) es.close();
      } catch { /* ignore */ }
    };
    es.onerror = () => es.close();

    return () => es.close();
  }, [customerId, orderId, order?.id]);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  const currentStatus = liveStatus || order?.status || 'pending';
  const stepIndex = STATUS_STEPS.indexOf(currentStatus);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center animate-pulse text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="text-center">
          <p className="text-gray-600">{error || '订单不存在'}</p>
          <Link to={`/h5/${customerId}/orders`} className="text-blue-600 text-sm mt-2 inline-block">返回</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-5 flex items-center gap-3">
        <Link to={`/h5/${customerId}/orders`} className="text-white/80 hover:text-white text-xl">←</Link>
        <div>
          <h1 className="text-lg font-bold">订单详情</h1>
          <p className="text-blue-100 text-xs">#{order.id.slice(0, 8)}</p>
        </div>
      </div>

      {/* Status */}
      <div className="bg-white mx-4 mt-4 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-600">订单状态</span>
          <span className={`text-sm px-2.5 py-0.5 rounded-full font-medium ${STATUS_COLORS[currentStatus] || 'bg-gray-100'}`}>
            {STATUS_LABELS[currentStatus] || currentStatus}
          </span>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mt-4">
          {STATUS_STEPS.map((s, i) => {
            const done = currentStatus === 'cancelled' ? false : stepIndex >= i;
            const current = currentStatus === s && currentStatus !== 'cancelled';
            return (
              <div key={s} className="flex flex-col items-center flex-1 relative">
                {i > 0 && (
                  <div className="absolute right-1/2 top-3 w-full h-0.5 -translate-y-1/2">
                    <div className={`h-full ${done ? 'bg-blue-500' : 'bg-gray-200'}`} />
                  </div>
                )}
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium z-10 ${
                    done ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'
                  } ${current ? 'ring-2 ring-blue-300 ring-offset-2' : ''}`}
                >
                  {done ? '✓' : i + 1}
                </div>
                <span className="text-[10px] text-gray-400 mt-1">{STATUS_LABELS[s]}</span>
              </div>
            );
          })}
        </div>
        {currentStatus === 'cancelled' && (
          <div className="text-center mt-3">
            <span className="text-xs bg-red-50 text-red-500 px-3 py-1 rounded-full">已取消</span>
          </div>
        )}
      </div>

      {/* Service Items */}
      <div className="bg-white mx-4 mt-3 rounded-xl p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">服务项目</h3>
        <div className="space-y-2">
          {order.items?.map((item, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="text-gray-700">{item.service_name || `服务 #${i + 1}`} ×{item.quantity}</span>
              <span className="font-medium text-gray-900">¥{item.price}</span>
            </div>
          ))}
        </div>
        <div className="border-t border-gray-100 mt-3 pt-3 flex justify-between">
          <span className="text-sm font-semibold text-gray-900">合计</span>
          <span className="text-lg font-bold text-blue-600">¥{order.total_amount}</span>
        </div>
      </div>

      {/* Info */}
      <div className="bg-white mx-4 mt-3 rounded-xl p-4 shadow-sm space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">服务地址</span>
          <span className="text-gray-900 text-right max-w-[60%]">{order.address || '—'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">预约时间</span>
          <span className="text-gray-900">
            {order.scheduled_at ? new Date(order.scheduled_at).toLocaleString('zh-CN') : '待确认'}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">服务人员</span>
          <span className="text-gray-900">
            {order.staff_name ? (
              <>
                {order.staff_name}
                {order.staff_phone && (
                  <a href={`tel:${order.staff_phone}`} className="ml-1 text-blue-600">📞</a>
                )}
              </>
            ) : (
              '待分配'
            )}
          </span>
        </div>
        {order.payment && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">支付状态</span>
            <span className={order.payment.status === 'paid' ? 'text-green-600 font-medium' : 'text-yellow-600'}>
              {order.payment.status === 'paid' ? `已支付 ¥${order.payment.amount}` : '待支付'}
            </span>
          </div>
        )}
      </div>

      {/* Review CTA */}
      {currentStatus === 'completed' && (
        <div className="mx-4 mt-4">
          <Link
            to={`/h5/${customerId}/orders/${orderId}/review`}
            className="block w-full text-center bg-orange-500 text-white py-3 rounded-xl font-medium hover:bg-orange-600 transition-colors"
          >
            ⭐ 评价本次服务
          </Link>
        </div>
      )}
    </div>
  );
}
