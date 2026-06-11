import { useState } from 'react';
import { Button, Card } from '@/components/ui';
import api from '@/lib/api';

const COPYWRITER_TEMPLATES = [
  { label: '日常保洁', prompt: '写一篇日常保洁服务的推广文案，强调专业、省心、价格实惠' },
  { label: '深度清洁', prompt: '写一篇深度清洁服务的营销文案，突出彻底清洁、专业设备、健康生活' },
  { label: '月嫂服务', prompt: '写一篇月嫂服务的宣传文案，突出专业护理、丰富经验、贴心照顾' },
  { label: '家电维修', prompt: '写一篇家电维修服务的推广文案，强调技术专业、快速上门、质量保障' },
];

export function MarketingPage() {
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const generate = async (prompt: string) => {
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post('/ai', {
        action: 'copywriter',
        messages: [{ role: 'user', content: prompt }],
      });
      setResult(data.reply);
    } catch {
      setResult('文案生成服务暂时不可用，请稍后重试。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">营销文案</h2>
        <p className="text-gray-500 mt-1">AI智能生成家政服务推广文案</p>
      </div>

      {/* Template buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {COPYWRITER_TEMPLATES.map((t) => (
          <Card key={t.label} padding="md" hover onClick={() => generate(t.prompt)}>
            <h3 className="font-semibold text-gray-900">{t.label}</h3>
            <p className="text-sm text-gray-500 mt-1">{t.prompt.slice(0, 50)}...</p>
          </Card>
        ))}
      </div>

      {/* Result */}
      {loading && (
        <Card>
          <div className="flex items-center gap-3 text-gray-500">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>正在生成文案...</span>
          </div>
        </Card>
      )}

      {result && (
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">生成结果</h3>
            <Button variant="outline" size="sm" onClick={() => navigator.clipboard?.writeText(result)}>
              复制
            </Button>
          </div>
          <div className="text-sm text-gray-900 whitespace-pre-wrap leading-relaxed bg-gray-50 rounded-lg p-4">
            {result}
          </div>
        </Card>
      )}
    </div>
  );
}
