import { Link } from 'react-router-dom';
import { Button } from '@/components/ui';

const services = [
  { icon: '🧹', name: '日常保洁', desc: '专业清洁，省时省心，让您的家焕然一新', price: '¥60起' },
  { icon: '🔧', name: '家电维修', desc: '持证技师，快速上门，修不好不收费', price: '¥100起' },
  { icon: '🏠', name: '深度清洁', desc: '全屋无死角，德国设备，除螨杀菌消毒', price: '¥200起' },
  { icon: '📦', name: '搬家服务', desc: '专业打包，小心搬运，零破损承诺', price: '¥300起' },
  { icon: '👶', name: '月嫂服务', desc: '持证月嫂，科学育儿，产后康复指导', price: '¥8000起/月' },
  { icon: '👴', name: '老年陪护', desc: '专业陪护，健康监测，陪伴聊天散步', price: '¥200起/天' },
];

const features = [
  { icon: '🤖', title: 'AI智能调度', desc: '根据员工技能、位置、负载自动派单，效率提升300%' },
  { icon: '💬', title: '7×24 AI客服', desc: '智能客服小智全年无休，秒级响应客户咨询和下单' },
  { icon: '📊', title: '数据驱动', desc: '实时经营数据大屏，订单趋势、营收一目了然' },
  { icon: '🔒', title: '安全可靠', desc: '数据加密传输，银行级支付安全，员工背景审查' },
];

export function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── Nav ── */}
      <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🏠</span>
            <span className="text-xl font-bold text-blue-600">智家管家AI</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-gray-600">
            <a href="#services" className="hover:text-blue-600 transition-colors">服务项目</a>
            <a href="#features" className="hover:text-blue-600 transition-colors">核心优势</a>
            <a href="#pricing" className="hover:text-blue-600 transition-colors">价格</a>
            <Link to="/login" className="text-blue-600 font-medium hover:text-blue-700">登录</Link>
            <Link to="/register">
              <Button size="sm">免费试用</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="max-w-6xl mx-auto px-6 py-20 md:py-28 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-sm font-medium rounded-full px-4 py-1.5 mb-6">
          🤖 AI驱动的家政服务管理平台
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 leading-tight tracking-tight">
          家政服务，<br className="md:hidden" />
          <span className="text-blue-600">AI</span>重新定义
        </h1>
        <p className="mt-6 text-lg md:text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
          智能调度、AI客服、数据驱动决策 —— 让您的家政公司运营效率提升300%，客户满意度飙升
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
          <Link to="/register">
            <Button size="lg" className="px-8 py-3.5 text-base">立即免费试用 →</Button>
          </Link>
          <Link to="/login">
            <Button size="lg" variant="outline" className="px-8 py-3.5 text-base">已有账号？登录</Button>
          </Link>
        </div>
        <p className="mt-4 text-xs text-gray-400">无需信用卡 · 14天免费试用 · 随时取消</p>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-8 mt-20 max-w-lg mx-auto border-t border-gray-100 pt-12">
          {[
            { v: '99.9%', l: '系统可用率' },
            { v: '10万+', l: '服务订单' },
            { v: '5000+', l: '入驻公司' },
          ].map((s) => (
            <div key={s.l}>
              <p className="text-2xl font-bold text-gray-900">{s.v}</p>
              <p className="text-sm text-gray-400 mt-1">{s.l}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Services ── */}
      <section id="services" className="bg-gray-50 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900">全方位家政服务</h2>
            <p className="mt-3 text-gray-500">覆盖6大品类，满足家庭和企业的所有需求</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((s) => (
              <div key={s.name} className="bg-white rounded-2xl p-6 border border-gray-100 hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
                <div className="text-3xl mb-3">{s.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900">{s.name}</h3>
                <p className="text-sm text-gray-500 mt-1 leading-relaxed">{s.desc}</p>
                <p className="text-blue-600 font-bold mt-3">{s.price}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900">为什么选择智家管家AI</h2>
            <p className="mt-3 text-gray-500">用技术赋能家政行业，让管理更简单</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((f) => (
              <div key={f.title} className="flex gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-2xl shrink-0">
                  {f.icon}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{f.title}</h3>
                  <p className="text-sm text-gray-500 mt-1 leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ── */}
      <section id="pricing" className="bg-gray-50 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900">简单透明的定价</h2>
            <p className="mt-3 text-gray-500">选择适合您公司的方案</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              { name: '免费版', price: '¥0', period: '永久', desc: '适合小型家政公司入门', features: ['10个订单/月', '5名员工', '基础AI客服', '手动派单'] },
              { name: '专业版', price: '¥299', period: '/月', desc: '适合成长中的家政公司', features: ['无限订单', '50名员工', 'AI客服+智能调度', '数据统计分析', '营销文案生成'], highlight: true },
              { name: '企业版', price: '¥999', period: '/月', desc: '适合大型连锁家政品牌', features: ['所有专业版功能', '无限员工', '多门店管理', 'API开放接入', '专属客服经理', '定制开发'] },
            ].map((plan) => (
              <div key={plan.name} className={`rounded-2xl p-8 border-2 ${plan.highlight ? 'border-blue-600 bg-white shadow-xl relative' : 'border-gray-200 bg-white'}`}>
                {plan.highlight && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-bold rounded-full px-4 py-1">🔥 最受欢迎</span>
                )}
                <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{plan.desc}</p>
                <div className="mt-4 mb-6">
                  <span className="text-4xl font-extrabold text-gray-900">{plan.price}</span>
                  <span className="text-gray-400 ml-1">{plan.period}</span>
                </div>
                <ul className="space-y-3">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                      <span className="text-green-500">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link to="/register">
                  <Button className="w-full mt-8" variant={plan.highlight ? 'primary' : 'outline'}>
                    {plan.price === '¥0' ? '免费开始' : '开始试用'}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 bg-blue-600">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white">准备好升级您的家政业务了吗？</h2>
          <p className="mt-4 text-blue-100 text-lg">加入5000+家政公司，用AI驱动增长</p>
          <Link to="/register">
            <Button size="lg" className="mt-8 px-10 py-3.5 bg-white text-blue-600 hover:bg-blue-50 text-base font-bold shadow-lg">
              立即免费试用 →
            </Button>
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-sm">
          <div>
            <h4 className="text-white font-semibold mb-3">智家管家AI</h4>
            <p className="leading-relaxed text-gray-500">AI驱动的家政服务智能管理平台</p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3">服务</h4>
            <ul className="space-y-1.5">
              {['日常保洁', '家电维修', '深度清洁', '搬家服务', '月嫂育儿', '老年陪护'].map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3">公司</h4>
            <ul className="space-y-1.5">
              {['关于我们', '加入我们', '合作伙伴', '联系我们'].map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3">联系</h4>
            <ul className="space-y-1.5">
              <li>📧 hello@zhijiaguanjia.ai</li>
              <li>📞 400-888-0000</li>
              <li>📍 中国·北京</li>
            </ul>
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-6 mt-10 pt-6 border-t border-gray-800 text-center text-xs text-gray-600">
          © 2026 智家管家AI · 保留所有权利
        </div>
      </footer>
    </div>
  );
}
