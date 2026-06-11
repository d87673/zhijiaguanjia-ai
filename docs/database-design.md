# 智家管家AI — 数据库设计文档 v1.0

> 文档版本: v1.0 | 更新日期: 2026-06-11 | 数据库: PostgreSQL 16

---

## 1. 数据库概览

| 属性 | 值 |
|------|------|
| 数据库 | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (Async) |
| 字符集 | UTF-8 |
| 主键策略 | UUID v4 |
| 索引策略 | 外键 + 高频查询字段 + 复合索引 |

---

## 2. ER 图（实体关系）

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Company  │────▶│   User   │     │  Staff   │
│  (公司)   │     │  (用户)   │     │ (员工)   │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     │ 1:N            │ 1:N            │ 1:N
     ▼                ▼                ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Service │     │  Order   │◀────│ Customer │
│  (服务)  │◀───│  (订单)   │     │ (客户)   │
└──────────┘     └────┬─────┘     └──────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │OrderItem │ │ Payment  │ │Conversat.│
    │(订单明细)│ │ (支付)   │ │ (会话)   │
    └──────────┘ └──────────┘ └────┬─────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │ Message  │
                              │ (消息)   │
                              └──────────┘
```

---

## 3. 表结构详情

### 3.1 companies (公司)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(200) | 公司名称 |
| slug | VARCHAR(200) UNIQUE | URL标识 |
| plan | VARCHAR(20) | 套餐: free/pro/enterprise |
| settings | JSONB | 公司设置 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

### 3.2 users (用户)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| email | VARCHAR(255) UNIQUE | 邮箱（登录名） |
| password_hash | VARCHAR(255) | bcrypt哈希密码 |
| role | VARCHAR(20) | admin/manager/staff |
| company_id | UUID FK | 所属公司 |
| phone | VARCHAR(20) | 手机号 |
| is_active | BOOLEAN | 是否激活 |

### 3.3 services (服务项目)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| company_id | UUID FK | 所属公司 |
| name | VARCHAR(200) | 服务名称 |
| description | TEXT | 服务描述 |
| price | NUMERIC(10,2) | 价格 |
| duration | INTEGER | 预估时长（分钟） |
| category | VARCHAR(50) | 分类标签 |
| is_active | BOOLEAN | 是否上架 |

### 3.4 customers (客户)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| company_id | UUID FK | 所属公司 |
| name | VARCHAR(100) | 姓名 |
| phone | VARCHAR(20) | 电话 |
| email | VARCHAR(255) | 邮箱 |
| address | TEXT | 地址 |
| tags | VARCHAR[] | 标签数组 |

### 3.5 staff (服务员工)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| company_id | UUID FK | 所属公司 |
| name | VARCHAR(100) | 姓名 |
| skills | VARCHAR[] | 技能标签 |
| rating | FLOAT | 评分 |
| current_load | INTEGER | 当前任务数 |
| is_active | BOOLEAN | 是否在岗 |

### 3.6 orders (订单)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| company_id | UUID FK | 所属公司 |
| customer_id | UUID FK | 客户 |
| staff_id | UUID FK | 派单员工 |
| status | VARCHAR(20) | pending/confirmed/dispatched/in_progress/completed/cancelled |
| total_amount | NUMERIC(10,2) | 总金额 |
| scheduled_at | TIMESTAMPTZ | 预约时间 |
| address | TEXT | 服务地址 |

### 3.7 order_items (订单明细)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_id | UUID FK | 所属订单 |
| service_id | UUID FK | 服务项目 |
| quantity | INTEGER | 数量 |
| price | NUMERIC(10,2) | 单价 |

### 3.8 payments (支付记录)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_id | UUID FK UNIQUE | 关联订单 |
| amount | NUMERIC(10,2) | 支付金额 |
| method | VARCHAR(20) | wechat/alipay/cash/card |
| status | VARCHAR(20) | pending/paid/refunded/failed |
| transaction_id | VARCHAR(100) | 第三方交易号 |

### 3.9 conversations (AI会话)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| company_id | UUID FK | 所属公司 |
| customer_id | UUID FK | 关联客户(可选) |
| source | VARCHAR(20) | web/wechat/phone |
| status | VARCHAR(20) | active/closed |

### 3.10 messages (消息)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| conversation_id | UUID FK | 所属会话 |
| role | VARCHAR(20) | user/assistant/system |
| content | TEXT | 消息内容 |

---

## 4. 索引策略

| 表 | 索引字段 | 类型 |
|------|------|------|
| users | email | UNIQUE |
| companies | slug | UNIQUE |
| services | company_id + category | COMPOSITE |
| customers | company_id + phone | COMPOSITE |
| staff | company_id + is_active | COMPOSITE |
| orders | company_id + status | COMPOSITE |
| orders | company_id + created_at | COMPOSITE |
| payments | status | BTREE |
| conversations | company_id + status | COMPOSITE |
| messages | conversation_id | BTREE |

---

## 5. 安全策略

- 所有密码使用 bcrypt (cost=12) 哈希存储
- API 鉴权使用 JWT (HS256)
- Access Token 有效期 60分钟
- Refresh Token 有效期 30天
- 数据库连接使用 SSL 加密
- 敏感字段(密码/支付密钥)不在 API 响应中暴露
