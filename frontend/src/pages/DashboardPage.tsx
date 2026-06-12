import { useEffect, useState } from 'react';
import { Button, Card } from '@/components/ui';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';
import type { StatsResponse } from '@/types';

export function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    api.get<StatsResponse>('/stats')
      .then((res) => setStats(res.data))
      .catch(() => addToast('加载数据失败，请刷新页面重试', 'error'))
      .finally(() => setLoading(false));
  }, [addToast]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <svg className="animate-spin h-8 w-8 mx-auto text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="mt-3 text-sm text-gray-500">加载数据中...</p>
        </div>
      </div>
    );
  }

  const handleExport = async (type: 'orders' | 'customers' | 'full') => {
    setExporting(true);
    try {
      const ext = type === 'full' ? 'xlsx' : 'csv';
      const resp = await api.get(`/export/${type}?format=${type === 'full' ? 'excel' : 'csv'}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}_${new Date().toISOString().slice(0, 10)}.${ext}`;
      a.click();
      window.URL.revokeObjectURL(url);
      addToast(`${type === 'orders' ? '订单' : type === 'customers' ? '客户' : '完整报表'}导出成功`, 'success');
    } catch {
      addToast('导出失败', 'error');
    } finally {
      setExporting(false);
    }
  };

  const summaryCards = [
    { label: '总订单数', value: stats?.summary?.total_orders ?? 0, color: 'text-blue-600', bg: 'bg-blue-50', icon: '📋' },
    { label: '客户数量', value: stats?.summary?.total_customers ?? 0, color: 'text-green-600', bg: 'bg-green-50', icon: '👥' },
    { label: '员工数量', value: stats?.summary?.total_staff ?? 0, color: 'text-purple-600', bg: 'bg-purple-50', icon: '🧹' },
    { label: '总收入', value: (stats?.summary?.total_revenue ?? 0).toLocaleString(), color: 'text-orange-600', bg: 'bg-orange-50', prefix: '¥', icon: '💰' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">控制台</h2>
        <p className="text-gray-500 mt-1">欢迎回来，这是您的业务概览</p>
      </div>

      {/* Export Buttons */}
      <div className="flex gap-2 flex-wrap">
        <Button variant="outline" size="sm" onClick={() => handleExport('orders')} loading={exporting}>
          📋 导出订单 CSV
        </Button>
        <Button variant="outline" size="sm" onClick={() => handleExport('customers')} loading={exporting}>
          👥 导出客户 CSV
        </Button>
        <Button variant="outline" size="sm" onClick={() => handleExport('full')} loading={exporting}>
          📊 导出完整报表 (.xlsx)
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((card) => (
          <Card key={card.label} padding="md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className={`text-2xl font-bold ${card.color} mt-1`}>
                  {card.prefix || ''}{card.value}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-xl ${card.bg} flex items-center justify-center text-2xl`}>
                {card.icon}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status distribution */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">订单状态分布</h3>
          <div className="space-y-4">
            {(['pending', 'confirmed', 'dispatched', 'in_progress', 'completed', 'cancelled'] as const).map((status) => {
              const item = stats?.status_distribution?.find((d) => d.status === status);
              const count = item?.count ?? 0;
              const total = stats?.status_distribution?.reduce((s, d) => s + d.count, 0) || 1;
              const pct = ((count / total) * 100).toFixed(1);
              const colors: Record<string, string> = {
                pending: 'bg-yellow-400', confirmed: 'bg-blue-400', dispatched: 'bg-indigo-400',
                in_progress: 'bg-cyan-400', completed: 'bg-green-400', cancelled: 'bg-red-400',
              };
              const labels: Record<string, string> = {
                pending: '待确认', confirmed: '已确认', dispatched: '已派单',
                in_progress: '服务中', completed: '已完成', cancelled: '已取消',
              };
              return (
                <div key={status} className="flex items-center gap-3">
                  <span className="text-sm text-gray-600 w-16 shrink-0">{labels[status]}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-500 ${colors[status]}`} style={{ width: `${count > 0 ? Math.max(Number(pct), 4) : 0}%` }} />
                  </div>
                  <span className="text-sm font-medium text-gray-900 w-16 text-right">{count} <span className="text-gray-400 text-xs">({pct}%)</span></span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Recent orders */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">最近订单</h3>
          {(stats?.recent_orders ?? []).length === 0 ? (
            <div className="text-center py-8">
              <p className="text-3xl mb-2">📭</p>
              <p className="text-gray-500 text-sm">暂无订单数据</p>
            </div>
          ) : (
            <div className="space-y-3">
              {(stats?.recent_orders ?? []).slice(0, 8).map((order) => {
                const statusLabels: Record<string, string> = {
                  pending: '待确认', confirmed: '已确认', dispatched: '已派单',
                  in_progress: '服务中', completed: '已完成', cancelled: '已取消',
                };
                return (
                  <div key={order.id} className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        order.status === 'completed' ? 'bg-green-400' :
                        order.status === 'cancelled' ? 'bg-red-400' :
                        order.status === 'in_progress' ? 'bg-cyan-400' :
                        order.status === 'pending' ? 'bg-yellow-400' : 'bg-blue-400'
                      }`} />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{order.customer_name || '未知客户'}</p>
                        <p className="text-xs text-gray-400">{order.address || '—'}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-900">¥{order.total_amount.toLocaleString()}</p>
                      <p className="text-xs text-gray-400">{statusLabels[order.status] || order.status}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      {/* 7-day trend */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">近7天订单趋势</h3>
        <div className="flex items-end gap-2 h-40 px-2">
          {stats?.last_7_days?.length ? (
            stats.last_7_days.map((day) => {
              const maxVal = Math.max(...stats.last_7_days.map((d) => d.orders), 1);
              const heightPct = (day.orders / maxVal) * 100;
              const revenueMax = Math.max(...stats.last_7_days.map((d) => d.revenue), 1);
              const revHeight = (day.revenue / revenueMax) * 100;
              return (
                <div key={day.date} className="flex-1 flex flex-col items-center gap-1.5 group cursor-default">
                  <div className="text-center opacity-0 group-hover:opacity-100 transition-opacity -mb-1">
                    <span className="text-xs bg-gray-800 text-white rounded px-2 py-0.5 whitespace-nowrap">
                      {day.orders}单 · ¥{day.revenue.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full flex flex-col gap-0.5">
                    <div className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600" style={{ height: `${Math.max(heightPct, 4)}%`, minHeight: 8 }} />
                    {day.revenue > 0 && (
                      <div className="w-full bg-orange-400/30 rounded-b transition-all" style={{ height: `${Math.max(revHeight * 0.3, 2)}%`, minHeight: 4 }} />
                    )}
                  </div>
                  <span className="text-xs text-gray-400">{day.date.slice(5)}</span>
                </div>
              );
            })
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">暂无数据</div>
          )}
        </div>
        <div className="flex justify-center gap-6 mt-4 text-xs text-gray-400">
          <span><span className="inline-block w-3 h-3 bg-blue-500 rounded-sm mr-1 align-middle" /> 订单数</span>
          <span><span className="inline-block w-3 h-3 bg-orange-400/30 rounded-sm mr-1 align-middle" /> 收入</span>
        </div>
      </Card>
    </div>
  );
}
