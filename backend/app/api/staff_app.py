"""员工移动端 PWA API — 免密 Token 认证"""
import hmac
import hashlib
import asyncio
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import get_settings
from app.models.models import Staff, Order, OrderItem, Service, Customer, Payment

router = APIRouter(prefix="/staff-app", tags=["Staff PWA"])

# ── Token 工具 ──

@lru_cache(maxsize=1)
def _get_secret() -> str:
    return get_settings().JWT_SECRET


def generate_staff_token(staff_id: str) -> str:
    """HMAC-SHA256(jwt_secret, staff_id) → hex digest"""
    return hmac.new(
        _get_secret().encode("utf-8"),
        staff_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_staff_token(staff_id: str, token: str) -> bool:
    """时间恒定比较，防止时序攻击"""
    expected = generate_staff_token(staff_id)
    return hmac.compare_digest(expected, token)


# ── 依赖 ──

async def get_staff_from_token(
    staff_id: str,
    x_staff_token: str = Header(..., alias="X-Staff-Token"),
    db: AsyncSession = Depends(get_db),
) -> Staff:
    """验证 Staff Token，返回员工对象"""
    if not verify_staff_token(staff_id, x_staff_token):
        raise HTTPException(status_code=401, detail="无效的访问令牌")

    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.is_active == True)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="员工不存在或已离职")
    return staff


# ═══════════════════════════════════════════════════
# 端点
# ═══════════════════════════════════════════════════

@router.get("/{staff_id}/me")
async def get_my_profile(
    staff: Staff = Depends(get_staff_from_token),
):
    """获取我的个人信息"""
    return {
        "id": str(staff.id),
        "name": staff.name,
        "phone": staff.phone,
        "email": staff.email,
        "skills": staff.skills or [],
        "rating": staff.rating,
        "current_load": staff.current_load,
        "is_active": staff.is_active,
    }


@router.get("/{staff_id}/orders")
async def get_my_orders(
    status: str = Query(""),
    staff: Staff = Depends(get_staff_from_token),
    db: AsyncSession = Depends(get_db),
):
    """获取分配给我的订单列表"""
    query = (
        select(Order)
        .where(Order.staff_id == staff.id, Order.status != "cancelled")
        .options(selectinload(Order.customer))
        .options(selectinload(Order.items).selectinload(OrderItem.service))
        .options(selectinload(Order.payment))
        .order_by(Order.scheduled_at.desc())
    )

    if status:
        query = query.where(Order.status == status)

    result = await db.execute(query)
    orders = result.scalars().all()

    return {
        "orders": [
            {
                "id": str(o.id),
                "customer_name": o.customer.name if o.customer else "未知客户",
                "customer_phone": o.customer.phone if o.customer else "",
                "status": o.status,
                "total_amount": float(o.total_amount),
                "scheduled_at": o.scheduled_at.isoformat() if o.scheduled_at else None,
                "address": o.address,
                "notes": o.notes,
                "items": [
                    {
                        "service_name": item.service.name if item.service else "家政服务",
                        "quantity": item.quantity,
                        "price": float(item.price),
                    }
                    for item in (o.items or [])
                ],
                "payment_status": o.payment.status if o.payment else "未支付",
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
        "count": len(orders),
    }


@router.get("/{staff_id}/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    staff: Staff = Depends(get_staff_from_token),
    db: AsyncSession = Depends(get_db),
):
    """获取单个订单详情"""
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.staff_id == staff.id)
        .options(selectinload(Order.customer))
        .options(selectinload(Order.items).selectinload(OrderItem.service))
        .options(selectinload(Order.payment))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    items = []
    for item in (order.items or []):
        items.append({
            "service_name": item.service.name if item.service else "家政服务",
            "quantity": item.quantity,
            "price": float(item.price),
        })

    return {
        "id": str(order.id),
        "customer_name": order.customer.name if order.customer else "未知客户",
        "customer_phone": order.customer.phone if order.customer else "",
        "status": order.status,
        "total_amount": float(order.total_amount),
        "scheduled_at": order.scheduled_at.isoformat() if order.scheduled_at else None,
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "address": order.address,
        "notes": order.notes,
        "items": items,
        "payment": {
            "status": order.payment.status,
            "method": order.payment.method,
            "amount": float(order.payment.amount),
        } if order.payment else None,
        "created_at": order.created_at.isoformat(),
    }


@router.put("/{staff_id}/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str = Query(..., pattern="^(in_progress|completed)$"),
    staff: Staff = Depends(get_staff_from_token),
    db: AsyncSession = Depends(get_db),
):
    """员工更新订单状态：开始服务 / 完成服务"""
    from datetime import datetime, timezone

    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.staff_id == staff.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    valid_transitions = {
        "in_progress": ["dispatched"],
        "completed": ["in_progress"],
    }

    if order.status not in valid_transitions.get(status, []):
        raise HTTPException(
            status_code=400,
            detail=f"无法从「{order.status}」变更为「{status}」，当前状态仅允许: {valid_transitions.get(status, [])}",
        )

    order.status = status
    if status == "completed":
        order.completed_at = datetime.now(timezone.utc)
        # 释放员工负载
        if staff.current_load > 0:
            staff.current_load -= 1

    if status == "in_progress":
        # 记录开始服务时间
        pass

    await db.commit()

    # Fire-and-forget 通知
    _schedule_staff_notification(status, order, staff, db)

    return {"message": f"订单状态已更新为「{status}」"}


@router.get("/{staff_id}/orders/{order_id}/stream")
async def stream_order_status(
    order_id: str,
    staff: Staff = Depends(get_staff_from_token),
    db: AsyncSession = Depends(get_db),
):
    """SSE 实时推送订单状态变化（员工端）"""
    async def event_stream():
        last_status = None
        for _ in range(300):  # 最多 5 分钟
            await asyncio.sleep(3)  # 每 3 秒检查一次
            # 每次循环获取新的 db session
            async with db.begin() as txn:
                # No - just re-query
                pass
            result = await db.execute(
                select(Order.status).where(Order.id == order_id)
            )
            current = result.scalar()
            if current is None:
                yield f"event: error\ndata: 订单不存在\n\n"
                return
            if current != last_status:
                last_status = current
                yield f"event: status\ndata: {current}\n\n"
                if current in ("completed", "cancelled"):
                    yield f"event: done\ndata: stream_closed\n\n"
                    return
        yield f"event: done\ndata: stream_timeout\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 通知调度 ──

def _schedule_staff_notification(event: str, order: Order, staff: Staff, db: AsyncSession):
    """Fire-and-forget 通知调度"""
    import asyncio
    import traceback
    import logging
    logger = logging.getLogger(__name__)

    async def _send():
        try:
            from app.services.notification_service import get_notification_engine
            engine = await get_notification_engine(order.company_id, db)
            if engine is None:
                return

            cust_result = await db.execute(
                select(Customer).where(Customer.id == order.customer_id)
            )
            customer = cust_result.scalar_one_or_none()
            order_no = str(order.id)[:8]

            items_result = await db.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
                .options(selectinload(OrderItem.service))
            )
            items = items_result.scalars().all()
            service_list = "、".join(
                item.service.name if item.service else "家政服务"
                for item in (items or [])
            ) or "家政服务"

            if event == "in_progress":
                await engine.notify_order_started(
                    customer_email=customer.email if customer else None,
                    customer_phone=customer.phone if customer else None,
                    customer_name=customer.name if customer else "客户",
                    staff_name=staff.name,
                    order_no=order_no,
                    service_list=service_list,
                )
            elif event == "completed":
                from datetime import datetime, timezone
                await engine.notify_order_completed(
                    customer_email=customer.email if customer else None,
                    customer_phone=customer.phone if customer else None,
                    customer_name=customer.name if customer else "客户",
                    order_no=order_no,
                    service_list=service_list,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    amount=f"{float(order.total_amount):.2f}",
                )
        except Exception:
            logger.error(f"员工通知发送失败: {traceback.format_exc()}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_send())
        else:
            asyncio.run(_send())
    except RuntimeError:
        pass
