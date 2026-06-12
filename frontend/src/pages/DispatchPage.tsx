import { useEffect, useState } from 'react';
import { Button, Card, Badge } from '@/components/ui';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';
import type { Order, Staff } from '@/types';

const statusLabels: Record<string, string> = {
  pending: '待确认', confirmed: '已确认', dispatched: '已派单',
  in_progress: '服务中', completed: '已完成', cancelled: '已取消',
};
const statusVariants: Record<string, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
  pending: 'warning', confirmed: 'info', dispatched: 'info',
  in_progress: 'info', completed: 'success', cancelled: 'danger',
};

export function DispatchPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);
  const [dispatching, setDispatching] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    Promise.all([
      api.get<{ data: { items: Order[] } }>('/orders', { params: { status: 'confirmed' } }),
      api.get<{ data: { items: Staff[] } }>('/staff'),
    ]).then(([oRes, sRes]) => {
      setOrders(oRes.data.data.items);
      setStaffList(sRes.data.data.items.filter((s) => s.is_active));
    }).catch(() => addToast('加载调度数据失败，请稍后重试', 'error'))
      .finally(() => setLoading(false));
  }, [addToast]);

  const handleDispatch = async (orderId: string, staffId: string) => {
    setDispatching(orderId);
    try {
      await api.put(`/orders/${orderId}/status`, { status: 'dispatched', staff_id: staffId });
      setOrders((prev) => prev.filter((o) => o.id !== orderId));
      addToast('派单成功', 'success');
    } catch {
      addToast('派单失败，请重试', 'error');
    } finally {
      setDispatching(null);
    }
  };

  const handleAiDispatch = async (orderId: string) => {
    setAiLoading(true);
    setResult(null);
    try {
      const { data } = await api.post('/ai', {
        action: 'dispatch',
        messages: [{ role: 'user', content: `请为订单 ${orderId} 推荐最优派单方案，列出推荐员工ID` }],
      });
      setResult(data.reply);
    } catch {
      setResult('调度服务暂时不可用，请稍后重试。');
    } finally {
      setAiLoading(false);
    }
  };

  const bestMatch = (order: Order) => {
    return staffList
      .filter((s) => {
        if (!order.items || order.items.length === 0) return true;
        return order.items.some((item) => {
          const svcName = (item.service_name || '').toLowerCase();
          return s.skills?.some((sk) => svcName.includes(sk.toLowerCase()));
        }) || true;
      })
      .sort((a, b) => b.rating - a.rating || a.current_load - b.current_load)
      .slice(0, 3);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">智能调度</h2>
        <p className="text-gray-500 mt-1">AI根据员工技能、位置、负载推荐最优派单方案</p>
      </div>

      {/* AI Result */}
      {result && (
        <Card padding="md">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">AI 推荐结果</h3>
            <button onClick={() => setResult(null)} className="text-xs text-gray-400 hover:text-gray-600">关闭</button>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 text-sm text-gray-900 whitespace-pre-wrap leading-relaxed">{result}</div>
        </Card>
      )}

      {/* Dispatch List */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">待派单订单</h3>
        {loading ? (
          <div className="text-center py-8 text-sm text-gray-400">加载中...</div>
        ) : orders.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-3xl mb-2">📭</p>
            <p className="text-gray-500 text-sm">暂无待派单的已确认订单</p>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => {
              const candidates = bestMatch(order);
              return (
                <div key={order.id} className="border border-gray-200 rounded-xl p-4 hover:border-blue-200 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-semibold text-gray-900">{order.customer_name || '未知客户'}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        地址: {order.address || '—'} · 金额: ¥{order.total_amount} · 预约: {order.scheduled_at ? new Date(order.scheduled_at).toLocaleString('zh-CN') : '—'}
                      </p>
                      <div className="flex gap-1.5 mt-1.5">
                        {(order.items || []).map((item, idx) => (
                          <span key={idx} className="text-xs bg-gray-100 rounded px-2 py-0.5">{item.service_name}×{item.quantity}</span>
                        ))}
                      </div>
                    </div>
                    <Badge variant={statusVariants[order.status] || 'default'}>{statusLabels[order.status]}</Badge>
                  </div>

                  {/* Staff candidates */}
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-500">推荐员工:</p>
                    {candidates.map((s) => (
                      <div key={s.id} className="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-50 hover:bg-blue-50">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-gray-900">{s.name}</span>
                          <span className="text-xs text-yellow-500">{'★'.repeat(Math.round(s.rating))}{s.rating.toFixed(1)}</span>
                          <span className="text-xs text-gray-400">负载: {s.current_load}单</span>
                          <span className="text-xs text-gray-400">技能: {(s.skills || []).slice(0, 3).join('、')}</span>
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => handleAiDispatch(order.id)} loading={aiLoading}>
                            AI分析
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleDispatch(order.id, s.id)}
                            loading={dispatching === order.id}
                          >
                            派单
                          </Button>
                        </div>
                      </div>
                    ))}
                    {candidates.length === 0 && (
                      <p className="text-xs text-gray-400 py-2">暂无匹配的在岗员工</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
