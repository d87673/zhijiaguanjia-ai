import { useEffect, useState } from 'react';
import { Button, Card, Input } from '@/components/ui';
import { useAuthStore } from '@/stores/authStore';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';

export function SettingsPage() {
  const { user } = useAuthStore();
  const addToast = useToastStore((s) => s.addToast);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingKeys, setSavingKeys] = useState(false);

  const [companyForm, setCompanyForm] = useState({
    name: '',
    phone: user?.phone || '',
    address: '',
  });

  const [keysForm, setKeysForm] = useState({
    deepseek_key: '',
    doubao_key: '',
    wechat_mch_id: '',
    wechat_appid: '',
    wechat_api_v3_key: '',
    wechat_cert_serial: '',
    wechat_private_key: '',
    alipay_app_id: '',
    alipay_private_key: '',
    alipay_public_key: '',
    payment_notify_host: '',
  });

  // Fetch current company settings on mount
  useEffect(() => {
    api.get<{ name: string; settings: Record<string, unknown> }>('/company')
      .then(({ data }) => {
        setCompanyForm({
          name: data.name || '',
          phone: (data.settings as Record<string, string>)?.phone || user?.phone || '',
          address: (data.settings as Record<string, string>)?.address || '',
        });
        const keys = (data.settings as Record<string, Record<string, string>>)?.api_keys || {};
        setKeysForm({
          deepseek_key: keys.deepseek_key || '',
          doubao_key: keys.doubao_key || '',
          wechat_mch_id: keys.wechat_mch_id || '',
          wechat_appid: keys.wechat_appid || '',
          wechat_api_v3_key: keys.wechat_api_v3_key || '',
          wechat_cert_serial: keys.wechat_cert_serial || '',
          wechat_private_key: keys.wechat_private_key || '',
          alipay_app_id: keys.alipay_app_id || '',
          alipay_private_key: keys.alipay_private_key || '',
          alipay_public_key: keys.alipay_public_key || '',
          payment_notify_host: keys.payment_notify_host || '',
        });
      })
      .catch(() => addToast('加载公司信息失败', 'error'))
      .finally(() => setLoading(false));
  }, [addToast, user?.phone]);

  const handleSaveCompany = async () => {
    setSaving(true);
    try {
      await api.put('/company', companyForm);
      addToast('公司信息已保存', 'success');
    } catch {
      addToast('保存公司信息失败', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveKeys = async () => {
    setSavingKeys(true);
    try {
      await api.put('/company/keys', keysForm);
      addToast('密钥已保存', 'success');
    } catch {
      addToast('保存密钥失败', 'error');
    } finally {
      setSavingKeys(false);
    }
  };

  const updateCompany = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setCompanyForm((f) => ({ ...f, [k]: e.target.value }));

  const updateKeys = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setKeysForm((f) => ({ ...f, [k]: e.target.value }));

  if (loading) {
    return (
      <div className="space-y-6 max-w-2xl">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">设置</h2>
          <p className="text-gray-500 mt-1">公司和账户设置</p>
        </div>
        <div className="text-center py-16 text-sm text-gray-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">设置</h2>
        <p className="text-gray-500 mt-1">公司和账户设置</p>
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">公司信息</h3>
        <div className="space-y-4">
          <Input label="公司名称" value={companyForm.name} onChange={updateCompany('name')} placeholder="XX家政服务有限公司" />
          <Input label="联系人" value={user?.name || ''} readOnly />
          <Input label="邮箱" value={user?.email || ''} readOnly />
          <Input label="手机号" value={companyForm.phone} onChange={updateCompany('phone')} placeholder="未设置" />
          <Input label="地址" value={companyForm.address} onChange={updateCompany('address')} placeholder="请输入公司地址" />
          <Button onClick={handleSaveCompany} loading={saving}>保存设置</Button>
        </div>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">API 配置</h3>
        <p className="text-sm text-gray-500 mb-4">AI接口和支付接口的密钥配置</p>
        <div className="space-y-4">
          <Input label="DeepSeek API Key" type="password" value={keysForm.deepseek_key} onChange={updateKeys('deepseek_key')} placeholder="••••••••" />
          <Input label="豆包 API Key" type="password" value={keysForm.doubao_key} onChange={updateKeys('doubao_key')} placeholder="••••••••" />
          <hr className="my-4 border-gray-100" />
          <h4 className="text-sm font-semibold text-gray-700 -mb-2">微信支付 (APIv3)</h4>
          <Input label="商户号 (Mch ID)" value={keysForm.wechat_mch_id} onChange={updateKeys('wechat_mch_id')} placeholder="未配置" />
          <Input label="AppID" value={keysForm.wechat_appid} onChange={updateKeys('wechat_appid')} placeholder="公众号/小程序 AppID" />
          <Input label="APIv3 密钥" type="password" value={keysForm.wechat_api_v3_key} onChange={updateKeys('wechat_api_v3_key')} placeholder="32位密钥" />
          <Input label="证书序列号" value={keysForm.wechat_cert_serial} onChange={updateKeys('wechat_cert_serial')} placeholder="商户API证书序列号" />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">API 私钥 (PEM)</label>
            <textarea
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              rows={3}
              value={keysForm.wechat_private_key}
              onChange={(e) => setKeysForm((f) => ({ ...f, wechat_private_key: e.target.value }))}
              placeholder="-----BEGIN PRIVATE KEY----- ..."
            />
          </div>
          <hr className="my-4 border-gray-100" />
          <h4 className="text-sm font-semibold text-gray-700 -mb-2">支付宝</h4>
          <Input label="App ID" value={keysForm.alipay_app_id} onChange={updateKeys('alipay_app_id')} placeholder="未配置" />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">应用私钥 (PEM)</label>
            <textarea
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              rows={3}
              value={keysForm.alipay_private_key}
              onChange={(e) => setKeysForm((f) => ({ ...f, alipay_private_key: e.target.value }))}
              placeholder="-----BEGIN RSA PRIVATE KEY----- ..."
            />
          </div>
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-700">支付宝公钥 (PEM)</label>
            <textarea
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              rows={3}
              value={keysForm.alipay_public_key}
              onChange={(e) => setKeysForm((f) => ({ ...f, alipay_public_key: e.target.value }))}
              placeholder="-----BEGIN PUBLIC KEY----- ..."
            />
          </div>
          <hr className="my-4 border-gray-100" />
          <h4 className="text-sm font-semibold text-gray-700 -mb-2">通用</h4>
          <Input label="回调通知域名" value={keysForm.payment_notify_host} onChange={updateKeys('payment_notify_host')} placeholder="https://api.xxx.com" />
          <Button variant="outline" onClick={handleSaveKeys} loading={savingKeys}>保存密钥</Button>
        </div>
      </Card>
    </div>
  );
}
