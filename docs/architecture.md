# 智家管家AI — 系统架构设计文档 v1.0

> 文档版本: v1.0 | 更新日期: 2026-06-11

---

## 1. 架构概览

```
                    ┌──────────────────────────┐
                    │      用户 / 客户          │
                    │  (浏览器 / 微信 / 手机)    │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │   Nginx (HTTPS / 静态文件) │
                    │   Port: 80 / 443          │
                    └──────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  React SPA  │  │ FastAPI      │  │ API Docs    │
    │  (Static)   │  │ Port: 8000   │  │ /docs /redoc│
    └─────────────┘  └──────┬──────┘  └─────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ PostgreSQL  │  │   Redis     │  │  External   │
    │   16        │  │   7         │  │  APIs       │
    └─────────────┘  └─────────────┘  └──────┬──────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                      ┌──────────┐  ┌──────────┐  ┌──────────┐
                      │ Deepseek │  │  豆包    │  │微信/支付宝│
                      │ V4 Pro   │  │ 4.0 Ultra│  │  支付    │
                      └──────────┘  └──────────┘  └──────────┘
```

---

## 2. 技术栈

| 层次 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **前端** | React + TypeScript | 19 + 5.7 | SPA |
| **UI框架** | Tailwind CSS | v4 | 原子化CSS |
| **路由** | React Router | v7 | 客户端路由 |
| **状态管理** | Zustand | v5 | 全局状态 |
| **后端** | Python + FastAPI | 3.12 + 0.115 | REST API |
| **ORM** | SQLAlchemy | 2.0 | 异步数据库操作 |
| **数据库** | PostgreSQL | 16 | 主数据库 |
| **缓存** | Redis | 7 | 会话/缓存/队列 |
| **认证** | JWT (python-jose) | - | 无状态认证 |
| **AI服务** | Deepseek V4 Pro + 豆包 Seed 2.0 Pro | - | AI客服/调度/营销 |
| **支付** | 微信支付 + 支付宝 | - | 收款 |
| **反向代理** | Nginx | Alpine | 静态文件 + API代理 |
| **容器化** | Docker + Compose | - | 部署 |
| **CI/CD** | GitHub Actions | - | 自动测试+部署 |

---

## 3. 项目目录结构

```
家政AI自动化系统/
├── backend/                         # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py                  # FastAPI 应用入口
│   │   ├── api/                     # API 路由模块
│   │   │   ├── auth.py              # 认证 (注册/登录)
│   │   │   ├── services.py          # 服务管理 CRUD
│   │   │   ├── customers.py         # 客户管理 CRUD
│   │   │   ├── staff.py             # 员工管理 CRUD
│   │   │   ├── orders.py            # 订单管理 CRUD
│   │   │   ├── ai.py                # AI 接口
│   │   │   └── stats.py             # 数据统计
│   │   ├── core/                    # 核心模块
│   │   │   ├── config.py            # 配置管理 (pydantic-settings)
│   │   │   ├── database.py          # 数据库连接池
│   │   │   ├── security.py          # JWT + bcrypt
│   │   │   └── deps.py              # 依赖注入 (认证中间件)
│   │   ├── models/                  # SQLAlchemy 数据模型
│   │   │   └── models.py            # 10张核心表
│   │   ├── schemas/                 # Pydantic 请求/响应模型
│   │   │   └── schemas.py           # 数据验证
│   │   └── services/                # 业务逻辑层
│   │       └── ai_service.py        # AI API 调用封装
│   ├── tests/                       # 测试用例
│   └── requirements.txt             # Python 依赖
├── frontend/                        # React + TypeScript 前端
│   ├── public/
│   ├── src/
│   │   ├── components/              # UI 组件
│   │   ├── pages/                   # 页面
│   │   ├── hooks/                   # 自定义 Hooks
│   │   ├── lib/                     # 工具函数 + API 客户端
│   │   ├── types/                   # TypeScript 类型定义
│   │   └── App.tsx                  # 根组件 + 路由
│   ├── package.json
│   └── vite.config.ts
├── docs/                            # 设计文档
│   ├── database-design.md           # 数据库设计
│   ├── api-spec.md                  # API 接口文档
│   └── architecture.md              # 架构设计文档
├── memory/                          # 经营报告
│   └── daily-reports/
├── scripts/                         # 运维脚本
│   └── daily-report.ts
├── docker-compose.yml               # Docker 部署编排
├── Dockerfile.backend               # 后端 Docker
├── nginx.conf                       # Nginx 配置
├── .github/workflows/               # CI/CD
│   └── deploy.yml
├── .env                             # 密钥（不提交）
├── .env.example                     # 密钥模板
└── .gitignore                       # Git 忽略规则
```

---

## 4. API 接口设计

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/health | 健康检查 | 否 |
| POST | /api/v1/auth/register | 注册 | 否 |
| POST | /api/v1/auth/login | 登录 | 否 |
| GET | /api/v1/auth/me | 当前用户 | 是 |
| GET | /api/v1/services | 服务列表 | 是 |
| POST | /api/v1/services | 创建服务 | 是 |
| PUT | /api/v1/services/{id} | 更新服务 | 是 |
| DELETE | /api/v1/services/{id} | 删除服务 | 是 |
| GET | /api/v1/customers | 客户列表 | 是 |
| POST | /api/v1/customers | 创建客户 | 是 |
| GET | /api/v1/staff | 员工列表 | 是 |
| POST | /api/v1/staff | 创建员工 | 是 |
| GET | /api/v1/orders | 订单列表 | 是 |
| POST | /api/v1/orders | 创建订单 | 是 |
| PUT | /api/v1/orders/{id}/status | 更新状态 | 是 |
| POST | /api/v1/ai | AI接口 | 是 |
| GET | /api/v1/stats | 数据统计 | 是 |

---

## 5. 安全架构

| 层级 | 措施 |
|------|------|
| 传输层 | HTTPS + TLS 1.3 |
| 认证层 | JWT (Access + Refresh Token 双令牌) |
| 密码 | bcrypt (cost=12) |
| API层 | 请求频率限制 (Nginx limit_req) |
| 数据库 | SSL加密连接 + 连接池 |
| 代码层 | 所有密钥通过环境变量注入，零硬编码 |
| 部署层 | Docker 隔离 + 最小权限运行 |
