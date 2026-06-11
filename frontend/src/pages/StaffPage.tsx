import { useEffect, useState, useCallback } from 'react';
import { Button, Card, Input, Modal, Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';
import type { Staff, StaffCreate } from '@/types';

const SKILL_OPTIONS = ['保洁', '深度清洁', '家电维修', '搬家', '月嫂', '育儿嫂', '陪护', '收纳整理', '除甲醛'];

const emptyForm: StaffCreate = { name: '', phone: '', email: '', skills: [] };

export function StaffPage() {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<StaffCreate>(emptyForm);
  const [saving, setSaving] = useState(false);
  const addToast = useToastStore((s) => s.addToast);

  const fetchStaff = useCallback(() => {
    setLoading(true);
    api.get<{ data: { items: Staff[] } }>('/staff')
      .then((res) => setStaff(res.data.data.items))
      .catch(() => addToast('加载员工列表失败', 'error'))
      .finally(() => setLoading(false));
  }, [addToast]);

  useEffect(() => { fetchStaff(); }, [fetchStaff]);

  const openCreate = () => { setForm(emptyForm); setModalOpen(true); };

  const toggleSkill = (skill: string) => {
    setForm((f) => ({
      ...f,
      skills: (f.skills || []).includes(skill)
        ? (f.skills || []).filter((s) => s !== skill)
        : [...(f.skills || []), skill],
    }));
  };

  const handleSave = async () => {
    if (!form.name.trim()) { addToast('请输入员工姓名', 'warning'); return; }
    setSaving(true);
    try {
      await api.post('/staff', form);
      addToast('员工已添加', 'success');
      setModalOpen(false);
      fetchStaff();
    } catch { addToast('保存失败', 'error'); }
    finally { setSaving(false); }
  };

  const handleDelete = async (s: Staff) => {
    if (!confirm(`确定删除员工「${s.name}」？`)) return;
    try { await api.delete(`/staff/${s.id}`); addToast('已删除', 'success'); fetchStaff(); }
    catch { addToast('删除失败', 'error'); }
  };

  const updateForm = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const columns: TableColumn<Staff>[] = [
    { key: 'name', header: '姓名', render: (s) => <span className="font-medium">{s.name}</span> },
    { key: 'phone', header: '电话', render: (s) => s.phone || '—' },
    { key: 'skills', header: '技能', render: (s) => (s.skills || []).map((sk) => (
      <span key={sk} className="inline-block bg-green-50 text-green-700 text-xs rounded px-2 py-0.5 mr-1 mb-1">{sk}</span>
    ))},
    { key: 'rating', header: '评分', render: (s) => (
      <span className="text-yellow-500 font-medium">{'★'.repeat(Math.round(s.rating))}{'☆'.repeat(5 - Math.round(s.rating))} {s.rating.toFixed(1)}</span>
    )},
    { key: 'current_load', header: '当前负载', render: (s) => (
      <span className={`font-medium ${s.current_load >= 5 ? 'text-red-600' : s.current_load >= 3 ? 'text-yellow-600' : 'text-green-600'}`}>
        {s.current_load} 单
      </span>
    )},
    { key: 'order_count', header: '总服务', render: (s) => s.order_count },
    { key: 'is_active', header: '状态', render: (s) => (
      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
        {s.is_active ? '在岗' : '休息'}
      </span>
    )},
    { key: 'actions', header: '操作', className: 'w-20', render: (s) => (
      <button onClick={(ev) => { ev.stopPropagation(); handleDelete(s); }} className="text-red-500 hover:text-red-700 text-sm">删除</button>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">员工管理</h2>
          <p className="text-gray-500 mt-1">管理您的家政服务员工</p>
        </div>
        <Button onClick={openCreate}>+ 添加员工</Button>
      </div>

      <Card>
        <Table columns={columns} data={staff} keyExtractor={(s) => s.id} loading={loading} />
      </Card>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="添加员工"
        footer={
          <>
            <Button variant="outline" onClick={() => setModalOpen(false)}>取消</Button>
            <Button onClick={handleSave} loading={saving}>保存</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input label="姓名" value={form.name} onChange={updateForm('name')} placeholder="员工姓名" required />
          <div className="grid grid-cols-2 gap-4">
            <Input label="电话" value={form.phone || ''} onChange={updateForm('phone')} placeholder="手机号" />
            <Input label="邮箱" value={form.email || ''} onChange={updateForm('email')} placeholder="电子邮箱" />
          </div>
          {/* Skills */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">技能标签（可多选）</label>
            <div className="flex flex-wrap gap-2">
              {SKILL_OPTIONS.map((sk) => (
                <button
                  key={sk}
                  type="button"
                  onClick={() => toggleSkill(sk)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    (form.skills || []).includes(sk)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {sk}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
