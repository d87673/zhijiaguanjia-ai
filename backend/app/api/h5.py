"""
智家管家AI — 客户自助 H5 API
=============================
免登 Token 认证：token = HMAC-SHA256(jwt_secret, customer_id)
客户通过管理员生成的链接访问：/h5/{customer_id}?token={token}

端点 (prefix="/api/v1/h5"):
  GET    /services              → 浏览服务列表
  POST   /orders                → 客户下单
  GET    /orders                → 我的订单列表
  GET    /orders/{id}           → 订单详情
  GET    /orders/{id}/stream    → SSE 实时状态推送
  POST   /orders/{id}/review    → 评价订单
  GET    /company               → 公司信息（名称、电话）
"""

import hashlib
import hmac
import json
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import get_settings
from app.models.models import (
    User, Company, Service, Customer, Order, OrderItem, Staff, Payment,
)
from app.schemas.schemas import (
    H5OrderCreate, H5OrderResponse, H5ReviewRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/h5", tags=["H5 Customer"])


# ═══════════════════════════════════════════════════
# Token 工具
# ═══════════════════════════════════════════════════

def generate_customer_token(customer_id: str) -> str:
    """生成客户访问 Token。管理员用它创建分享链接。"""
    secret = get_settings().JWT_SECRET_KEY
    return hmac.new(
        secret.encode(), customer_id.encode(), hashlib.sha256
    ).hexdigest()


def verify_customer_token(customer_id: str, token: str) -> bool:
    """验证客户 Token。时间恒定比较防止时序攻击。"""
    expected = generate_customer_token(customer_id)
    if len(token) != len(expected):
        return False
    result = 0
    for a, b in zip(token, expected):
        result |= ord(a) ^ ord(b)
    return result == 0


async def get_customer_from_token(
    customer_id: str,
    x_customer_token: str = Header(..., alias="X-Customer-Token"),
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """验证 Token 并返回 Customer 对象（FastAPI Dependency）。"""
    if not verify_customer_token(customer_id, x_customer_token):
        raise HTTPException(status_code=401, detail="无效的访问链接，请联系管理员获取新链接")

    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer


async def get_company_from_customer(
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
) -> Company:
    """从已验证的 Customer 反查 Company。"""
    result = await db.execute(select(Company).where(Company.id == customer.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


# ═══════════════════════════════════════════════════
# H5 API 端点
# ═══════════════════════════════════════════════════

@router.get("/{customer_id}/services", response_model=dict)
async def list_services(
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
):
    """获取该客户所属公司的启用服务列表"""
    result = await db.execute(
        select(Service)
        .where(Service.company_id == customer.company_id, Service.is_active == True)
        .order_by(Service.category, Service.name)
    )
    services = result.scalars().all()

    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "description": s.description,
                    "price": float(s.price),
                    "duration": s.duration,
                    "category": s.category,
                    "image_url": s.image_url,
                }
                for s in services
            ],
        },
    }


@router.get("/{customer_id}/company", response_model=dict)
async def get_company_info(
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
):
    """获取公司名称和客服电话"""
    result = await db.execute(select(Company).where(Company.id == customer.company_id))
    company = result.scalar_one_or_none()
    settings = dict(company.settings or {}) if company else {}

    return {
        "success": True,
        "data": {
            "name": company.name if company else "",
            "phone": settings.get("phone", ""),
            "customer_name": customer.name,
            "customer_id": str(customer.id),
        },
    }


@router.post("/{customer_id}/orders", response_model=dict, status_code=201)
async def create_order(
    req: H5OrderCreate,
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
):
    """客户自助下单"""
    if not req.items or len(req.items) == 0:
        raise HTTPException(status_code=400, detail="请至少选择一个服务")

    # 计算总价
    total = sum(item.price * item.quantity for item in req.items)

    order = Order(
        company_id=customer.company_id,
        customer_id=customer.id,
        status="pending",
        total_amount=total,
        scheduled_at=req.scheduled_at,
        address=req.address or customer.address,
        notes=req.notes,
    )
    db.add(order)
    await db.flush()

    for item in req.items:
        oi = OrderItem(
            order_id=order.id,
            service_id=item.service_id,
            quantity=item.quantity,
            price=item.price,
        )
        db.add(oi)

    await db.commit()

    # ── 异步通知 ──
    _schedule_h5_notification("order_created", customer.company_id, order, db)

    return {"success": True, "data": {"order_id": str(order.id)}}


@router.get("/{customer_id}/orders", response_model=dict)
async def list_my_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
):
    """我的订单列表"""
    offset = (page - 1) * limit
    count = await db.execute(
        select(func.count()).select_from(Order).where(Order.customer_id == customer.id)
    )
    total = count.scalar()

    result = await db.execute(
        select(Order)
        .where(Order.customer_id == customer.id)
        .options(selectinload(Order.items).selectinload(OrderItem.service))
        .options(selectinload(Order.assigned_staff))
        .options(selectinload(Order.payment))
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    orders = result.scalars().all()

    return {
        "success": True,
        "data": {
            "items": [_serialize_order(o) for o in orders],
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


@router.get("/{customer_id}/orders/{order_id}", response_model=dict)
async def get_order_detail(
    order_id: str,
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
):
    """订单详情"""
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == customer.id)
        .options(selectinload(Order.items).selectinload(OrderItem.service))
        .options(selectinload(Order.assigned_staff))
        .options(selectinload(Order.payment))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {"success": True, "data": _serialize_order(order)}


@router.get("/{customer_id}/orders/{order_id}/stream")
async def stream_order_status(
    order_id: str,
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
):
    """SSE 实时推送订单状态变化"""
    # 先验证订单属于该客户
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.customer_id == customer.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="订单不存在")

    async def event_generator():
        last_status = None
        for _ in range(300):  # 最多 5 分钟
            async with db.bind.connect() as conn:
                from sqlalchemy import text
                row = await conn.execute(
                    text("SELECT status FROM orders WHERE id = :id"),
                    {"id": order_id},
                )
                current = row.scalar()

            if current != last_status:
                last_status = current
                yield f"data: {json.dumps({'status': current})}\n\n"
                if current in ("completed", "cancelled"):
                    yield f"data: {json.dumps({'status': current, 'done': True})}\n\n"
                    return

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{customer_id}/orders/{order_id}/review", response_model=dict)
async def review_order(
    order_id: str,
    req: H5ReviewRequest,
    customer: Customer = Depends(get_customer_from_token),
    db: AsyncSession = Depends(get_db),
):
    """评价已完成订单"""
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == customer.id)
        .options(selectinload(Order.assigned_staff))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "completed":
        raise HTTPException(status_code=400, detail="只能评价已完成的订单")

    if not (1 <= req.rating <= 5):
        raise HTTPException(status_code=400, detail="评分需在 1-5 之间")

    # 更新员工评分
    if order.assigned_staff:
        staff = order.assigned_staff
        old_avg = staff.rating or 5.0
        # 查找该员工被评价过的订单数
        staff_result = await db.execute(
            select(Order)
            .where(Order.staff_id == staff.id, Order.status == "completed")
        )
        completed_count = len(staff_result.scalars().all())
        new_avg = (old_avg * completed_count + req.rating) / (completed_count + 1)
        staff.rating = round(new_avg, 1)

    # 保存评价到 order 的 notes
    order.notes = (order.notes or "") + f"\n[客户评价] 评分: {req.rating}/5"
    if req.comment:
        order.notes += f" | 留言: {req.comment}"

    await db.commit()

    return {"success": True, "data": {"message": "评价成功，谢谢您的反馈！"}}


# ═══════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════

def _serialize_order(o: Order) -> dict:
    return {
        "id": str(o.id),
        "status": o.status,
        "total_amount": float(o.total_amount),
        "scheduled_at": o.scheduled_at.isoformat() if o.scheduled_at else None,
        "completed_at": o.completed_at.isoformat() if o.completed_at else None,
        "address": o.address,
        "notes": o.notes,
        "staff_name": o.assigned_staff.name if o.assigned_staff else None,
        "staff_phone": o.assigned_staff.phone if o.assigned_staff else None,
        "items": [
            {
                "id": str(item.id),
                "service_id": str(item.service_id),
                "service_name": item.service.name if item.service else None,
                "quantity": item.quantity,
                "price": float(item.price),
            }
            for item in (o.items or [])
        ],
        "payment": {
            "id": str(o.payment.id),
            "status": o.payment.status,
            "method": o.payment.method,
            "amount": float(o.payment.amount),
            "paid_at": o.payment.paid_at.isoformat() if o.payment and o.payment.paid_at else None,
        } if o.payment else None,
        "created_at": o.created_at.isoformat(),
    }


def _schedule_h5_notification(event: str, company_id: str, order: Order, db: AsyncSession):
    """fire-and-forget 通知，失败不影响主流程"""
    import traceback

    async def _send():
        try:
            from app.services.notification_service import get_notification_engine
            engine = await get_notification_engine(company_id, db)
            if engine is None:
                return
            result = await db.execute(
                select(Customer).where(Customer.id == order.customer_id)
            )
            customer = result.scalar_one_or_none()
            items_result = await db.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
                .options(selectinload(OrderItem.service))
            )
            items = items_result.scalars().all()
            service_list = "、".join(
                item.service.name if item.service else "家政服务"
                for item in (items or [])
            ) or "家政服务"
            sched_str = order.scheduled_at.isoformat() if order.scheduled_at else "待确认"
            amount = f"{float(order.total_amount):.2f}"
            order_no = str(order.id)[:8]

            if event == "order_created":
                await engine.notify_customer_order_created(
                    customer_email=customer.email if customer else None,
                    customer_phone=customer.phone if customer else None,
                    customer_name=customer.name if customer else "客户",
                    order_no=order_no,
                    service_list=service_list,
                    scheduled_at=sched_str,
                    address=order.address or "",
                    amount=amount,
                )
        except Exception:
            logger.error(f"H5 通知失败: {traceback.format_exc()}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_send())
        else:
            asyncio.run(_send())
    except RuntimeError:
        pass
