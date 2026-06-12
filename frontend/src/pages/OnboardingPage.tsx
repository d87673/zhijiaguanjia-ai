import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card } from '@/components/ui';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';

const STEPS = [
  {
    title: '欢迎加入智家管家AI',
    subtitle: '让我们花 2 分钟完成基础设置，快速上手',
    icon: '🎉',
    fields: [],
  },
  {
    title: '设置服务项目',
    subtitle: '添加您公司提供的家政服务，客户将通过H5自助端浏览下单',
    icon: '🧹',
    fields: [
      { key: 'svg_name1', label: '第一个服务名称', placeholder: '例如：日常保洁', type: 'text' },
      { key: 'svg_price1', label: '价格（元）', placeholder: '例如：99', type: 'number' },
    ],
  },
  {
    title: '添加员工',
    subtitle: '添加您的家政服务人员，后续可以为他们生成手机端PWA登录链接',
    icon: '👷',
    fields: [
      { key: 'staff_name1', label: '员工姓名', placeholder: '例如：张阿姨', type: 'text' },
      { key: 'staff_phone1', label: '手机号', placeholder: '例如：13800138000', type: 'text' },
    ],
  },
  {
    title: '设置完成！',
    subtitle: '一切就绪，开始使用智家管家AI管理您的家政业务吧',
    icon: '🚀',
    fields: [],
  },
];

export function OnboardingPage() {
  const navigate = useNavigate();
  const addToast = useToastStore((s) => s.addToast);
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});

  const currentStep = STEPS[step];

  const updateForm = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [key]: e.target.value }));
  };

  const handleNext = async () => {
    if (step === 1 && form.svg_name1) {
      // Create service
      setSaving(true);
      try {
        await api.post('/services', {
          name: form.svg_name1,
          price: parseFloat(form.svg_price1 || '99'),
          category: '保洁',
          duration: 120,
          is_active: true,
        });
      } catch { /* ok if fails */ }
      setSaving(false);
    }

    if (step === 2 && form.staff_name1) {
      setSaving(true);
      try {
        await api.post('/staff', {
          name: form.staff_name1,
          phone: form.staff_phone1 || '',
          skills: ['保洁'],
        });
      } catch { /* ok if fails */ }
      setSaving(false);
    }

    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      // Mark onboarding complete
      try {
        await api.put('/company/keys', { onboarding_completed: true });
      } catch { /* ok */ }
      addToast('设置完成，欢迎使用智家管家AI！', 'success');
      navigate('/dashboard', { replace: true });
    }
  };

  const handleSkip = () => {
    navigate('/dashboard', { replace: true });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {STEPS.map((_, idx) => (
            <div
              key={idx}
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                idx <= step ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>

        <Card padding="lg">
          <div className="text-center mb-6">
            <span className="text-5xl inline-block mb-4">{currentStep.icon}</span>
            <h2 className="text-xl font-bold text-gray-900">{currentStep.title}</h2>
            <p className="text-gray-500 mt-2 text-sm">{currentStep.subtitle}</p>
          </div>

          {/* Form fields */}
          {currentStep.fields.length > 0 && (
            <div className="space-y-4 mb-6">
              {currentStep.fields.map((field) => (
                <div key={field.key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                  <input
                    className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    type={field.type}
                    value={form[field.key] || ''}
                    onChange={updateForm(field.key)}
                    placeholder={field.placeholder}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Step 3: summary */}
          {step === 3 && (
            <div className="space-y-2 mb-6 text-sm text-gray-600">
              <div className="flex items-center gap-2">✅ 公司已设置</div>
              {form.svg_name1 && <div className="flex items-center gap-2">🧹 已添加服务：{form.svg_name1}</div>}
              {form.staff_name1 && <div className="flex items-center gap-2">👷 已添加员工：{form.staff_name1}</div>}
            </div>
          )}

          <div className="flex gap-3">
            {step < STEPS.length - 1 && (
              <Button variant="outline" onClick={handleSkip} className="flex-1">
                跳过
              </Button>
            )}
            <Button onClick={handleNext} loading={saving} className="flex-1">
              {step < STEPS.length - 1 ? '下一步 →' : '开始使用 🚀'}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
