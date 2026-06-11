# 智家管家AI — API 接口文档 v1.0

> Base URL: https://api.zhijiaguanjia.cn/api/v1
> Auth: Bearer Token (JWT)
> Content-Type: application/json

---

## 认证接口

### POST /auth/register
```json
// Request
{
  "name": "张三",
  "email": "zhangsan@example.com",
  "password": "password123",
  "company_name": "洁净家政公司",
  "phone": "13800138000"
}
// Response 201
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "user": { "id": "uuid", "name": "张三", "email": "...", "role": "admin" }
}
```

### POST /auth/login
```json
// Request
{ "email": "zhangsan@example.com", "password": "password123" }
// Response 200
{ "access_token": "...", "refresh_token": "...", "user": {...} }
```

---

## 服务管理

### GET /services?page=1&limit=20&q=保洁
```json
// Response 200
{
  "services": [
    { "id": "uuid", "name": "深度保洁", "price": 299, "duration": 120, "category": "cleaning", "is_active": true }
  ],
  "total": 1, "page": 1, "limit": 20
}
```

### POST /services
```json
// Request
{ "name": "深度保洁", "description": "全屋深度清洁", "price": 299, "duration": 120, "category": "cleaning" }
// Response 201
{ ...service }
```

---

## 订单管理

### GET /orders?page=1&limit=20&status=pending
```json
// Response 200
{
  "orders": [
    {
      "id": "uuid", "customer_name": "李四", "staff_name": null,
      "status": "pending", "total_amount": 299,
      "items": [{"service_name": "深度保洁", "quantity": 1, "price": 299}],
      "created_at": "2026-06-11T10:00:00Z"
    }
  ],
  "total": 1, "page": 1, "limit": 20
}
```

### POST /orders
```json
// Request
{
  "customer_id": "uuid",
  "status": "pending",
  "total_amount": 299,
  "scheduled_at": "2026-06-12T09:00:00Z",
  "address": "北京市朝阳区xxx",
  "items": [{"service_id": "uuid", "quantity": 1, "price": 299}]
}
// Response 201
{ "message": "订单创建成功", "order_id": "uuid" }
```

### PUT /orders/{id}/status?status=dispatched&staff_id=uuid
```json
// Response 200
{ "message": "订单状态已更新为 dispatched" }
```

---

## AI 接口

### POST /ai
```json
// Request
{
  "action": "chat",
  "messages": [
    {"role": "user", "content": "我想预约周末的深度保洁"}
  ],
  "context": {"company": "洁净家政", "city": "北京"}
}
// Response 200
{ "reply": "您好！感谢咨询洁净家政。周末深度保洁..." }
```

**action 类型**:
- `chat` — AI智能客服
- `dispatch` — 智能派单优化
- `copywriter` — 营销文案生成

---

## 数据统计

### GET /stats
```json
// Response 200
{
  "summary": {
    "totalOrders": 120, "pendingOrders": 5, "completedOrders": 110,
    "todayOrders": 3, "thisMonthOrders": 45,
    "totalCustomers": 80, "activeCustomers": 35,
    "totalStaff": 10, "totalRevenue": 35000, "thisMonthRevenue": 8900
  },
  "statusDistribution": [
    {"status": "pending", "count": 5},
    {"status": "completed", "count": 110}
  ],
  "last7Days": [{"date": "06/05", "count": 3, "revenue": 0}],
  "recentOrders": [...]
}
```

---

## 通用错误响应

```json
// 400 Bad Request
{ "detail": "该邮箱已被注册" }
// 401 Unauthorized
{ "detail": "Invalid or expired token" }
// 403 Forbidden
{ "detail": "Insufficient permissions" }
// 404 Not Found
{ "detail": "服务不存在" }
// 422 Validation Error
{ "detail": [{"loc": ["body", "email"], "msg": "value is not a valid email"}] }
// 500 Server Error
{ "detail": "Internal Server Error" }
```
