import { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import h5Api, { setH5Auth, getH5CustomerId, getH5Token } from '@/lib/h5Api';
import type { H5ServiceItem, H5CompanyInfo, H5OrderCreate } from '@/types';

/**
 * H5 首页：展示服务列表 + 下单入口
 * URL: /h5/:customerId?token=xxx
 */
export function H5HomePage() {
  const { customerId } = useParams<{ customerId: string }>();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [company, setCompany] = useState<H5CompanyInfo | null>(null);
  const [services, setServices] = useState<H5ServiceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; orderId?: string; error?: string } | null>(null);

  // 下单表单
  const [selected, setSelected] = useState<Map<string, number>>(new Map());
  const [address, setAddress] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!customerId || !token) return;
    setH5Auth(customerId, token);
    Promise.all([
      h5Api.get<{ success: boolean; data: H5CompanyInfo }>(`/${customerId}/company`),
      h5Api.get<{ success: boolean; data: { items: H5ServiceItem[] } }>(`/${customerId}/services`),
    ])
      .then(([compRes, svcRes]) => {
        setCompany(compRes.data.data);
        setServices(svcRes.data.data.items);
      })
      .catch(() => setResult({ success: false, error: '加载失败，请检查链接是否有效' }))
      .finally(() => setLoading(false));
  }, [customerId, token]);

  const toggleService = (id: string, price: number) => {
    setSelected((prev) => {
      const next = new Map(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.set(id, price);
      }
      return next;
    });
  };

  const totalAmount = Array.from(selected.values()).reduce((s, p) => s + p, 0);

  const handleSubmit = async () => {
    if (selected.size === 0) return;
    if (!address.trim()) {
      setResult({ success: false, error: '请填写服务地址' });
      return;
    }
    setSubmitting(true);
    setResult(null);
    try {
      const items: H5OrderCreate['items'] = Array.from(selected.entries()).map(([id, price]) => ({
        service_id: id,
        quantity: 1,
        price,
      }));
      const { data } = await h5Api.post<{ success: boolean; data: { order_id: string } }>(
        `/${customerId}/orders`,
        {
          address: address.trim(),
          scheduled_at: scheduledAt || undefined,
          notes: notes.trim() || undefined,
          items,
        },
      );
      setResult({ success: true, orderId: data.data.order_id });
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '下单失败，请重试';
      setResult({ success: false, error: msg });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center animate-pulse">
          <div className="text-4xl mb-4">🧹</div>
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 p-6">
        <div className="text-center max-w-sm">
          <div className="text-5xl mb-4">🔗</div>
          <p className="text-gray-600 font-medium">链接已失效或无效</p>
          <p className="text-gray-400 text-sm mt-2">请联系管理员获取新的访问链接</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-32">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-6">
        <h1 className="text-xl font-bold">{company.name}</h1>
        <p className="text-blue-100 text-sm mt-1">您好，{company.customer_name}</p>
        {company.phone && (
          <a href={`tel:${company.phone}`} className="inline-block mt-2 text-sm bg-white/20 rounded-full px-3 py-1 hover:bg-white/30">
            📞 {company.phone}
          </a>
        )}
      </div>

      {/* Service Grid */}
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">选择服务</h2>
        <div className="grid grid-cols-2 gap-3">
          {services.map((s) => {
            const active = selected.has(s.id);
            return (
              <button
                key={s.id}
                onClick={() => toggleService(s.id, s.price)}
                className={`text-left p-3 rounded-xl border-2 transition-all ${
                  active
                    ? 'border-blue-500 bg-blue-50 shadow-sm'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="text-sm font-medium text-gray-900">{s.name}</div>
                <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">{s.description || s.category || ''}</div>
                <div className="text-blue-600 font-bold text-sm mt-2">¥{s.price}</div>
                {s.duration > 0 && (
                  <div className="text-xs text-gray-400">{s.duration}分钟</div>
                )}
              </button>
            );
          })}
        </div>
        {services.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <p className="text-3xl mb-2">📋</p>
            <p>暂无可用服务</p>
          </div>
        )}
      </div>

      {/* Order Form */}
      {selected.size > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg px-4 py-4 max-h-[60vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">下单信息</h3>
            <span className="text-lg font-bold text-blue-600">¥{totalAmount}</span>
          </div>

          {result && (
            <div className={`rounded-lg p-3 mb-3 text-sm ${result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
              {result.success ? (
                <>
                  <p className="font-medium">下单成功！✅</p>
                  <p className="mt-1">订单号：{result.orderId?.slice(0, 8)}...</p>
                  <Link
                    to={`/h5/${customerId}/orders`}
                    className="inline-block mt-2 text-green-700 underline font-medium"
                  >
                    查看我的订单 →
                  </Link>
                </>
              ) : (
                <p>{result.error}</p>
              )}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">服务地址 *</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="如：XX小区3栋501"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">预约时间</label>
              <input
                type="datetime-local"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">备注</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="有什么特殊要求？"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-4">
            <Link
              to={`/h5/${customerId}/orders`}
              className="flex-1 text-center py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
            >
              我的订单
            </Link>
            <button
              onClick={handleSubmit}
              disabled={submitting || !address.trim()}
              className="flex-[2] bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? '提交中...' : `立即预约 (¥${totalAmount})`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
