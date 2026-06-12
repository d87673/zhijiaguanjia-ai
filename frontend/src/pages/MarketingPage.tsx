import { useState } from 'react';
import { Button, Card } from '@/components/ui';
import api from '@/lib/api';

const CATEGORIES = [
  { key: 'service', label: '服务推广' },
  { key: 'seasonal', label: '节日促销' },
  { key: 'social', label: '朋友圈' },
  { key: 'sms', label: '短信营销' },
  { key: 'poster', label: '海报文案' },
];

const COPYWRITER_TEMPLATES = [
  // ── 服务推广 ──
  { label: '日常保洁', category: 'service', prompt: '写一篇日常保洁服务的推广文案，强调专业、省心、价格实惠，适合微信推文' },
  { label: '深度清洁', category: 'service', prompt: '写一篇深度清洁服务的营销文案，突出彻底清洁、专业设备、健康生活' },
  { label: '月嫂服务', category: 'service', prompt: '写一篇月嫂服务的宣传文案，突出专业护理、丰富经验、贴心照顾、持证上岗' },
  { label: '家电维修', category: 'service', prompt: '写一篇家电维修服务的推广文案，强调技术专业、快速上门、质量保障' },
  { label: '搬家服务', category: 'service', prompt: '写一篇搬家服务的营销文案，突出细心打包、高效搬运、物品保障' },
  { label: '收纳整理', category: 'service', prompt: '写一篇收纳整理服务的推广文案，强调空间优化、专业收纳师、焕然一新' },
  { label: '除甲醛', category: 'service', prompt: '写一篇除甲醛服务的营销文案，突出专业检测、高效治理、母婴级安全' },
  { label: '陪护服务', category: 'service', prompt: '写一篇陪护服务的宣传文案，突出贴心陪伴、专业护理、子女放心' },

  // ── 节日促销 ──
  { label: '春节大扫除', category: 'seasonal', prompt: '写一篇春节前大扫除的促销文案，结合春节习俗，强调"辞旧迎新"，附带限时优惠' },
  { label: '618年中大促', category: 'seasonal', prompt: '写一篇618家政服务大促的营销文案，突出全年最低价、限量抢购、多种服务套餐' },
  { label: '双11特惠', category: 'seasonal', prompt: '写一篇双11家政服务特惠文案，强调年度最大优惠、囤货式购买、全家套餐' },
  { label: '春季焕新', category: 'seasonal', prompt: '写一篇春季家居焕新的推广文案，结合春季换季清洁需求，适合3-4月促销' },
  { label: '端午安康', category: 'seasonal', prompt: '写一篇端午节家政促销文案，结合端午安康主题，突出送健康送清洁的理念' },
  { label: '中秋团圆', category: 'seasonal', prompt: '写一篇中秋节家政宣传文案，强调"让家有更多团聚时光"，保洁+月嫂套餐促销' },

  // ── 朋友圈 ──
  { label: '朋友圈·开业', category: 'social', prompt: '写一段适合发微信朋友圈的家政服务开业/推广文案，亲切自然，150字以内，带emoji' },
  { label: '朋友圈·案例', category: 'social', prompt: '写一段朋友圈客户服务案例分享，展示清洁前后对比效果，生活化口吻，带emoji' },
  { label: '朋友圈·日常', category: 'social', prompt: '写一段朋友圈日常文案，分享家政小妙招顺便推广服务，轻松幽默风格，带emoji' },
  { label: '朋友圈·活动', category: 'social', prompt: '写一段朋友圈限时活动文案，制造紧迫感，鼓励转发和下单，120字以内' },

  // ── 短信营销 ──
  { label: '短信·新客', category: 'sms', prompt: '写一条70字以内的短信营销文案，针对新客户首次下单优惠，包含优惠码和联系方式' },
  { label: '短信·唤醒', category: 'sms', prompt: '写一条70字以内的短信文案，唤醒老客户，温馨问候+专属优惠，适合长时间未下单客户' },
  { label: '短信·节日', category: 'sms', prompt: '写一条70字以内的节日祝福短信，自然嵌入家政服务推广，温馨不突兀' },

  // ── 海报文案 ──
  { label: '海报·开业', category: 'poster', prompt: '写一段适合家政公司开业海报的文案，包含主标题、副标题、核心卖点、联系方式' },
  { label: '海报·套餐', category: 'poster', prompt: '写一段家政服务套餐海报文案，突出超值套餐组合，主标题吸引眼球，附带价格锚点' },
];

export function MarketingPage() {
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('service');

  const filteredTemplates = COPYWRITER_TEMPLATES.filter((t) => t.category === activeCategory);

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

      {/* Category tabs */}
      <div className="flex gap-2 flex-wrap">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeCategory === cat.key
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Template buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {filteredTemplates.map((t) => (
          <Card key={t.label} padding="md" hover onClick={() => generate(t.prompt)}>
            <h3 className="font-semibold text-gray-900">{t.label}</h3>
            <p className="text-sm text-gray-500 mt-1">{t.prompt.slice(0, 60)}...</p>
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
