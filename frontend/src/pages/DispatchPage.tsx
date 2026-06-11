import { useState } from 'react';
import { Button, Card } from '@/components/ui';
import api from '@/lib/api';

export function DispatchPage() {
  const [orderId, setOrderId] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const runDispatch = async () => {
    if (!orderId.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post('/ai', {
        action: 'dispatch',
        messages: [{ role: 'user', content: `请为订单 ${orderId.trim()} 推荐最优派单方案` }],
      });
      setResult(data.reply);
    } catch {
      setResult('调度服务暂时不可用，请稍后重试。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">智能调度</h2>
        <p className="text-gray-500 mt-1">AI根据员工技能、位置、负载推荐最优派单方案</p>
      </div>

      <Card>
        <div className="flex gap-3 mb-4">
          <input
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="输入订单ID..."
          />
          <Button onClick={runDispatch} loading={loading}>
            开始调度
          </Button>
        </div>

        {result && (
          <div className="bg-blue-50 rounded-lg p-4 text-sm text-gray-900 whitespace-pre-wrap leading-relaxed">
            {result}
          </div>
        )}
      </Card>
    </div>
  );
}
