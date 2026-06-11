import { useState } from 'react';
import { Button, Card, Input } from '@/components/ui';
import { useAuthStore } from '@/stores/authStore';

export function SettingsPage() {
  const { user } = useAuthStore();
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">设置</h2>
        <p className="text-gray-500 mt-1">公司和账户设置</p>
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">公司信息</h3>
        <div className="space-y-4">
          <Input label="公司名称" defaultValue="XX家政服务有限公司" />
          <Input label="联系人" value={user?.name || ''} readOnly />
          <Input label="邮箱" value={user?.email || ''} readOnly />
          <Input label="手机号" value={user?.phone || ''} placeholder="未设置" />
          <Input label="地址" placeholder="请输入公司地址" />
          <Button onClick={handleSave}>{saved ? '已保存 ✓' : '保存设置'}</Button>
        </div>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">API 配置</h3>
        <p className="text-sm text-gray-500 mb-4">AI接口和支付接口的密钥配置</p>
        <div className="space-y-4">
          <Input label="DeepSeek API Key" type="password" placeholder="••••••••" />
          <Input label="豆包 API Key" type="password" placeholder="••••••••" />
          <Input label="微信支付商户号" placeholder="未配置" />
          <Input label="支付宝App ID" placeholder="未配置" />
          <Button variant="outline">保存密钥</Button>
        </div>
      </Card>
    </div>
  );
}
