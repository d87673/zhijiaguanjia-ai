import { useEffect, useState, useCallback } from 'react';
import { Button, Card, Input, Modal, Badge, OrderStatusBadge, Table } from '@/components/ui';
import type { TableColumn } from '@/components/ui';
import { useToastStore } from '@/stores/toastStore';
import api from '@/lib/api';
import type { Order, OrderStatus, Customer, Service, Staff } from '@/types';

const statusTabs: { key: string; label: string }[] = [
  { key: '', label: '全部' },
  { key: 'pending', label: '待确认' },
  { key: 'confirmed', label: '已确认' },
  { key: 'dispatched', label: '已派单' },
  { key: 'in_progress', label: '服务中' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
];

const statusFlow: { from: OrderStatus; to: OrderStatus; label: string; variant: 'primary' | 'secondary' | 'danger' }[] = [
  { from: 'pending', to: 'confirmed', label: '确认订单', variant: 'primary' },
  { from: 'confirmed', to: 'dispatched', label: '派单', variant: 'primary' },
  { from: 'dispatched', to: 'in_progress', label: '开始服务', variant: 'primary' },
  { from: 'in_progress', to: 'completed', label: '完成', variant: 'primary' },
  { from: 'pending', to: 'cancelled', label: '取消', variant: 'danger' },
  { from: 'confirmed', to: 'cancelled', label: '取消', variant: 'danger' },
];

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [dispatchOpen, setDispatchOpen] = useState(false);
  const [dispatchOrderId, setDispatchOrderId] = useState('');
  const [saving, setSaving] = useState(false);
  const addToast = useToastStore((s) => s.addToast);

  // Order form state
  const [form, setForm] = useState({
    customer_id: '', address: '', scheduled_at: '', notes: '',
    items: [] as { service_id: string; quantity: number; price: number; service_name?: string }[],
  });

  const fetchOrders = useCallback(() => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (statusFilter) params.status = statusFilter;
    api.get<{ data: { items: Order[] } }>('/orders', { params })
      .then((res) => setOrders(res.data.data.items))
      .catch(() => addToast('加载订单失败', 'error'))
      .finally(() => setLoading(false));
  }, [addToast, statusFilter]);

  useEffect(() => { fetchOrders(); }, [fetchOrders]);
  useEffect(() => {
    Promise.all([
      api.get<{ data: { items: Customer[] } }>('/customers'),
      api.get<{ data: { items: Service[] } }>('/services'),
    ]).then(([cRes, sRes]) => {
      setCustomers(cRes.data.data.items);
      setServices(sRes.data.data.items);
    }).catch(() => {});
  }, []);

  const openCreate = () => { setForm({ customer_id: '', address: '', scheduled_at: '', notes: '', items: [] }); setCreateOpen(true); };

  const addServiceItem = (serviceId: string) => {
    const svc = services.find((s) => s.id === serviceId);
    if (!svc) return;
    const exists = form.items.find((i) => i.service_id === serviceId);
    if (exists) {
      setForm((f) => ({ ...f, items: f.items.map((i) => i.service_id === serviceId ? { ...i, quantity: i.quantity + 1 } : i) }));
    } else {
      setForm((f) => ({ ...f, items: [...f.items, { service_id: serviceId, quantity: 1, price: svc.price, service_name: svc.name }] }));
    }
  };

  const removeServiceItem = (serviceId: string) => {
    setForm((f) => ({ ...f, items: f.items.filter((i) => i.service_id !== serviceId) }));
  };

  const totalAmount = form.items.reduce((sum, i) => sum + i.price * i.quantity, 0);

  const handleCreate = async () => {
    if (!form.customer_id) { addToast('请选择客户', 'warning'); return; }
    if (form.items.length === 0) { addToast('请至少添加一个服务', 'warning'); return; }
    setSaving(true);
    try {
      await api.post('/orders', { ...form, total_amount: totalAmount });
      addToast('订单已创建', 'success');
      setCreateOpen(false);
      fetchOrders();
    } catch { addToast('创建订单失败', 'error'); }
    finally { setSaving(false); }
  };

  const handleStatusChange = async (order: Order, to: OrderStatus) => {
    if (to === 'dispatched') {
      setDispatchOrderId(order.id);
      setDispatchOpen(true);
      return;
    }
    try {
      await api.put(`/orders/${order.id}/status`, { status: to });
      addToast(`订单状态已更新为「${OrderStatusBadge[to]?.label || to}」`, 'success');
      fetchOrders();
    } catch { addToast('状态更新失败', 'error'); }
  };

  const handleDispatch = async (staffId: string) => {
    try {
      await api.put(`/orders/${dispatchOrderId}/status`, { status: 'dispatched', staff_id: staffId });
      addToast('派单成功', 'success');
      setDispatchOpen(false);
      fetchOrders();
    } catch { addToast('派单失败', 'error'); }
  };

  const columns: TableColumn<Order>[] = [
    { key: 'customer_name', header: '客户', render: (o) => <span className="font-medium">{o.customer_name || '—'}</span> },
    { key: 'address', header: '地址', render: (o) => <span className="text-sm">{o.address || '—'}</span> },
    { key: 'total_amount', header: '金额', render: (o) => <span className="font-semibold">¥{o.total_amount}</span> },
    { key: 'items', header: '服务', render: (o) => (o.items || []).map((i: any) => (
      <span key={i.service_id} className="inline-block text-xs bg-gray-100 rounded px-2 py-0.5 mr-1 mb-1">{i.service_name || i.service_id}×{i.quantity}</span>
    ))},
    { key: 'status', header: '状态', render: (o) => {
      const badge = OrderStatusBadge[o.status as OrderStatus] || OrderStatusBadge.pending;
      return <Badge variant={badge.variant}>{badge.label}</Badge>;
    }},
    { key: 'scheduled_at', header: '预约时间', render: (o) => o.scheduled_at ? new Date(o.scheduled_at).toLocaleString('zh-CN') : '—' },
    { key: 'actions', header: '操作', className: 'w-36', render: (o) => {
      const availableActions = statusFlow.filter((a) => a.from === o.status);
      return (
        <div className="flex gap-1.5 flex-wrap">
          {availableActions.map((a) => (
            <button
              key={a.to}
              onClick={(ev) => { ev.stopPropagation(); handleStatusChange(o, a.to); }}
              className={`text-xs px-2 py-1 rounded font-medium transition-colors ${
                a.variant === 'danger' ? 'text-red-600 hover:bg-red-50' : 'text-blue-600 hover:bg-blue-50'
              }`}
            >
              {a.label}
            </button>
          ))}
        </div>
      );
    }},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">订单管理</h2>
          <p className="text-gray-500 mt-1">管理和追踪所有服务订单</p>
        </div>
        <Button onClick={openCreate}>+ 新建订单</Button>
      </div>

      {/* Status tabs */}
      <div className="flex gap-2 flex-wrap">
        {statusTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setStatusFilter(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === tab.key
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <Card>
        <Table columns={columns} data={orders} keyExtractor={(o) => o.id} loading={loading} />
      </Card>

      {/* Create Order Modal */}
      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="新建订单"
        size="lg"
        footer={
          <>
            <span className="text-sm text-gray-500 mr-4">合计: <b className="text-lg text-gray-900">¥{totalAmount}</b></span>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>取消</Button>
            <Button onClick={handleCreate} loading={saving}>创建订单</Button>
          </>
        }
      >
        <div className="space-y-4">
          {/* Customer select */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">客户 *</label>
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.customer_id}
              onChange={(e) => setForm((f) => ({ ...f, customer_id: e.target.value }))}
            >
              <option value="">请选择客户</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>{c.name} — {c.phone || '无电话'}</option>
              ))}
            </select>
          </div>
          <Input label="服务地址" value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} placeholder="请输入服务地址" />
          <Input label="预约时间" type="datetime-local" value={form.scheduled_at} onChange={(e) => setForm((f) => ({ ...f, scheduled_at: e.target.value }))} />
          <Input label="备注" value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} placeholder="备注信息" />

          {/* Service items */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">服务项目 *</label>
            <div className="flex gap-2 mb-3">
              <select
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value=""
                onChange={(e) => { if (e.target.value) { addServiceItem(e.target.value); e.target.value = ''; } }}
              >
                <option value="">添加服务...</option>
                {services.filter((s) => s.is_active).map((s) => (
                  <option key={s.id} value={s.id}>{s.name} — ¥{s.price}</option>
                ))}
              </select>
            </div>
            {form.items.length > 0 ? (
              <div className="border border-gray-200 rounded-lg divide-y divide-gray-100">
                {form.items.map((item, idx) => (
                  <div key={item.service_id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                    <span className="font-medium text-gray-900">{item.service_name || item.service_id}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-gray-500">¥{item.price} × {item.quantity}</span>
                      <span className="font-semibold text-gray-900">¥{item.price * item.quantity}</span>
                      <button onClick={() => removeServiceItem(item.service_id)} className="text-red-400 hover:text-red-600">✕</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-4 border border-dashed border-gray-200 rounded-lg">点击上方下拉框添加服务项目</p>
            )}
          </div>
        </div>
      </Modal>

      {/* Dispatch Modal */}
      <DispatchModal open={dispatchOpen} onClose={() => setDispatchOpen(false)} onDispatch={handleDispatch} />
    </div>
  );
}

// ─── Dispatch sub-component ───
function DispatchModal({ open, onClose, onDispatch }: { open: boolean; onClose: () => void; onDispatch: (staffId: string) => void }) {
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      api.get<{ data: { items: Staff[] } }>('/staff').then((r) => setStaffList(r.data.data.items.filter((s) => s.is_active))).catch(() => {});
    }
  }, [open]);

  return (
    <Modal open={open} onClose={onClose} title="选择派单员工">
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {staffList.length === 0 && <p className="text-sm text-gray-400">暂无在岗员工</p>}
        {staffList.map((s) => (
          <div key={s.id} className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-gray-50 border border-gray-100">
            <div>
              <p className="font-medium text-gray-900 text-sm">{s.name}</p>
              <p className="text-xs text-gray-500">
                技能: {(s.skills || []).join('、') || '无'} · 当前负载: {s.current_load}单 · 评分: {s.rating.toFixed(1)}
              </p>
            </div>
            <Button size="sm" onClick={() => onDispatch(s.id)}>派单</Button>
          </div>
        ))}
      </div>
    </Modal>
  );
}
