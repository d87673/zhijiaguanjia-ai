import { useEffect, useState, useCallback } from 'react';
import { Button, Card, Input, Modal, Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';
import type { Service, ServiceCreate, ServiceUpdate } from '@/types';

const emptyForm: ServiceCreate = { name: '', price: 0, duration: 60, category: '', description: '', image_url: '' };

export function ServicesPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Service | null>(null);
  const [form, setForm] = useState<ServiceCreate>(emptyForm);
  const [saving, setSaving] = useState(false);
  const addToast = useToastStore((s) => s.addToast);

  const fetchServices = useCallback(() => {
    setLoading(true);
    api.get<{ data: { items: Service[] } }>('/services')
      .then((res) => setServices(res.data.data.items))
      .catch(() => addToast('加载服务列表失败', 'error'))
      .finally(() => setLoading(false));
  }, [addToast]);

  useEffect(() => { fetchServices(); }, [fetchServices]);

  const openCreate = () => { setEditing(null); setForm(emptyForm); setModalOpen(true); };
  const openEdit = (s: Service) => {
    setEditing(s);
    setForm({ name: s.name, price: s.price, duration: s.duration, category: s.category || '', description: s.description || '', image_url: s.image_url || '' });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) { addToast('请输入服务名称', 'warning'); return; }
    setSaving(true);
    try {
      if (editing) {
        const body: ServiceUpdate = { ...form };
        await api.put(`/services/${editing.id}`, body);
        addToast('服务已更新', 'success');
      } else {
        await api.post('/services', form);
        addToast('服务已创建', 'success');
      }
      setModalOpen(false);
      fetchServices();
    } catch { addToast('保存失败，请重试', 'error'); }
    finally { setSaving(false); }
  };

  const handleDelete = async (s: Service) => {
    if (!confirm(`确定删除服务「${s.name}」？`)) return;
    try { await api.delete(`/services/${s.id}`); addToast('已删除', 'success'); fetchServices(); }
    catch { addToast('删除失败', 'error'); }
  };

  const handleToggleActive = async (s: Service) => {
    try { await api.put(`/services/${s.id}`, { is_active: !s.is_active }); addToast(s.is_active ? '已下架' : '已上架', 'success'); fetchServices(); }
    catch { addToast('操作失败', 'error'); }
  };

  const updateForm = (k: keyof ServiceCreate) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.type === 'number' ? Number(e.target.value) : e.target.value }));

  const columns: TableColumn<Service>[] = [
    { key: 'name', header: '服务名称', render: (s) => <span className="font-medium">{s.name}</span> },
    { key: 'category', header: '分类', render: (s) => s.category || '未分类' },
    { key: 'price', header: '价格', render: (s) => <span className="font-semibold">¥{s.price}</span> },
    { key: 'duration', header: '时长', render: (s) => `${s.duration}分钟` },
    { key: 'is_active', header: '状态', render: (s) => (
      <button onClick={(ev) => { ev.stopPropagation(); handleToggleActive(s); }} className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium cursor-pointer transition-colors ${s.is_active ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
        {s.is_active ? '上架' : '下架'}
      </button>
    )},
    { key: 'actions', header: '操作', className: 'w-28', render: (s) => (
      <div className="flex gap-2">
        <button onClick={(ev) => { ev.stopPropagation(); openEdit(s); }} className="text-blue-600 hover:text-blue-800 text-sm">编辑</button>
        <button onClick={(ev) => { ev.stopPropagation(); handleDelete(s); }} className="text-red-500 hover:text-red-700 text-sm">删除</button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">服务管理</h2>
          <p className="text-gray-500 mt-1">管理您的家政服务项目</p>
        </div>
        <Button onClick={openCreate}>+ 添加服务</Button>
      </div>

      <Card>
        <Table columns={columns} data={services} keyExtractor={(s) => s.id} loading={loading} onRowClick={openEdit} />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? '编辑服务' : '添加服务'}
        footer={
          <>
            <Button variant="outline" onClick={() => setModalOpen(false)}>取消</Button>
            <Button onClick={handleSave} loading={saving}>保存</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input label="服务名称" value={form.name} onChange={updateForm('name')} placeholder="例如：日常保洁" required />
          <div className="grid grid-cols-2 gap-4">
            <Input label="价格 (元)" type="number" value={form.price} onChange={updateForm('price')} />
            <Input label="时长 (分钟)" type="number" value={form.duration} onChange={updateForm('duration')} />
          </div>
          <Input label="分类" value={form.category || ''} onChange={updateForm('category')} placeholder="保洁/维修/搬家/月嫂" />
          <Input label="描述" value={form.description || ''} onChange={updateForm('description')} placeholder="服务详细介绍" />
          <Input label="图片URL" value={form.image_url || ''} onChange={updateForm('image_url')} placeholder="可选" />
        </div>
      </Modal>
    </div>
  );
}
