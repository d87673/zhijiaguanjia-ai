import { useEffect, useState, useCallback } from 'react';
import { Button, Card, Input, Modal, Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';
import type { Customer, CustomerCreate } from '@/types';

const emptyForm: CustomerCreate = { name: '', phone: '', email: '', address: '', notes: '', tags: [] };

export function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState<CustomerCreate>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [search, setSearch] = useState('');
  const addToast = useToastStore((s) => s.addToast);

  const fetchCustomers = useCallback(() => {
    setLoading(true);
    api.get<{ data: { items: Customer[]; total: number } }>('/customers', { params: search ? { search } : {} })
      .then((res) => setCustomers(res.data.data.items))
      .catch(() => addToast('加载客户列表失败', 'error'))
      .finally(() => setLoading(false));
  }, [addToast, search]);

  useEffect(() => { fetchCustomers(); }, [fetchCustomers]);

  const openCreate = () => { setEditing(null); setForm(emptyForm); setTagInput(''); setModalOpen(true); };
  const openEdit = (c: Customer) => {
    setEditing(c);
    setForm({ name: c.name, phone: c.phone || '', email: c.email || '', address: c.address || '', notes: c.notes || '', tags: c.tags || [] });
    setTagInput('');
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) { addToast('请输入客户姓名', 'warning'); return; }
    setSaving(true);
    try {
      if (editing) {
        await api.put(`/customers/${editing.id}`, form);
        addToast('客户信息已更新', 'success');
      } else {
        await api.post('/customers', form);
        addToast('客户已添加', 'success');
      }
      setModalOpen(false);
      fetchCustomers();
    } catch { addToast('保存失败', 'error'); }
    finally { setSaving(false); }
  };

  const handleDelete = async (c: Customer) => {
    if (!confirm(`确定删除客户「${c.name}」？此操作不可撤销。`)) return;
    try { await api.delete(`/customers/${c.id}`); addToast('已删除', 'success'); fetchCustomers(); }
    catch { addToast('删除失败', 'error'); }
  };

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !form.tags?.includes(tag)) {
      setForm((f) => ({ ...f, tags: [...(f.tags || []), tag] }));
    }
    setTagInput('');
  };

  const removeTag = (tag: string) => {
    setForm((f) => ({ ...f, tags: (f.tags || []).filter((t) => t !== tag) }));
  };

  const updateForm = (k: keyof CustomerCreate) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const columns: TableColumn<Customer>[] = [
    { key: 'name', header: '姓名', render: (c) => <span className="font-medium">{c.name}</span> },
    { key: 'phone', header: '电话', render: (c) => c.phone || '—' },
    { key: 'address', header: '地址', render: (c) => c.address || '—' },
    { key: 'order_count', header: '订单数', render: (c) => c.order_count },
    { key: 'tags', header: '标签', render: (c) => (c.tags || []).map((t) => (
      <span key={t} className="inline-block bg-blue-50 text-blue-600 text-xs rounded px-2 py-0.5 mr-1 mb-1">{t}</span>
    ))},
    { key: 'actions', header: '操作', className: 'w-24', render: (c) => (
      <div className="flex gap-2">
        <button onClick={(ev) => { ev.stopPropagation(); openEdit(c); }} className="text-blue-600 hover:text-blue-800 text-sm">编辑</button>
        <button onClick={(ev) => { ev.stopPropagation(); handleDelete(c); }} className="text-red-500 hover:text-red-700 text-sm">删除</button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">客户管理</h2>
          <p className="text-gray-500 mt-1">管理您的客户信息和历史记录</p>
        </div>
        <Button onClick={openCreate}>+ 添加客户</Button>
      </div>

      {/* Search */}
      <div className="flex gap-3">
        <input
          className="flex-1 max-w-sm border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索客户姓名、电话..."
        />
      </div>

      <Card>
        <Table columns={columns} data={customers} keyExtractor={(c) => c.id} loading={loading} onRowClick={openEdit} />
      </Card>

      {/* Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? '编辑客户' : '添加客户'}
        footer={
          <>
            <Button variant="outline" onClick={() => setModalOpen(false)}>取消</Button>
            <Button onClick={handleSave} loading={saving}>保存</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input label="姓名" value={form.name} onChange={updateForm('name')} placeholder="客户姓名" required />
          <div className="grid grid-cols-2 gap-4">
            <Input label="电话" value={form.phone || ''} onChange={updateForm('phone')} placeholder="手机号" />
            <Input label="邮箱" value={form.email || ''} onChange={updateForm('email')} placeholder="电子邮箱" />
          </div>
          <Input label="地址" value={form.address || ''} onChange={updateForm('address')} placeholder="服务地址" />
          <Input label="备注" value={form.notes || ''} onChange={updateForm('notes')} placeholder="备注信息" />
          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">标签</label>
            <div className="flex gap-2">
              <input
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTag(); } }}
                placeholder="输入标签后回车添加"
              />
              <Button variant="outline" size="sm" onClick={addTag}>添加</Button>
            </div>
            {(form.tags || []).length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {(form.tags || []).map((t) => (
                  <span key={t} className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs rounded-full px-2.5 py-1">
                    {t}
                    <button onClick={() => removeTag(t)} className="text-blue-400 hover:text-red-500">&times;</button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
}
