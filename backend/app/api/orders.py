from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Order, OrderItem, Customer, Staff, Service
from app.schemas.schemas import OrderCreate, OrderResponse, OrderStatusUpdateRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ── 通知调度（轻量 fire-and-forget）─────────────────────

def _schedule_notification(event: str, order: Order, db: AsyncSession) -> None:
    """在后台事件循环中异步发送通知。失败静默，不影响主流程。"""
    import asyncio
    import traceback

    async def _send():
        try:
            from app.services.notification_service import get_notification_engine
            from app.models.models import Customer, Staff
            engine = await get_notification_engine(order.company_id, db)
            if engine is None:
                return

            # 查客户/员工信息
            cust_result = await db.execute(select(Customer).where(Customer.id == order.customer_id))
            customer = cust_result.scalar_one_or_none()

            staff = None
            if order.staff_id:
                staff_result = await db.execute(select(Staff).where(Staff.id == order.staff_id))
                staff = staff_result.scalar_one_or_none()

            # 查订单项
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
            elif event == "staff_dispatched":
                await engine.notify_staff_dispatched(
                    staff_email=staff.email if staff else None,
                    staff_phone=staff.phone if staff else None,
                    staff_name=staff.name if staff else "员工",
                    customer_name=customer.name if customer else "客户",
                    customer_phone=customer.phone if customer else "",
                    order_no=order_no,
                    service_list=service_list,
                    scheduled_at=sched_str,
                    address=order.address or "",
                )
            elif event == "order_completed":
                completed_at = datetime.now(timezone.utc).isoformat()
                await engine.notify_order_completed(
                    customer_email=customer.email if customer else None,
                    customer_phone=customer.phone if customer else None,
                    customer_name=customer.name if customer else "客户",
                    order_no=order_no,
                    service_list=service_list,
                    completed_at=completed_at,
                    amount=amount,
                )
        except Exception:
            logger.error(f"通知发送失败: {traceback.format_exc()}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_send())
        else:
            asyncio.run(_send())
    except RuntimeError:
        pass


# ═══════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════

@router.get("", response_model=dict)
async def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    status: str = Query(""),
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    offset = (page - 1) * limit
    query = (
        select(Order)
        .where(Order.company_id == company_id)
        .options(selectinload(Order.items).selectinload(OrderItem.service))
        .options(selectinload(Order.customer))
        .options(selectinload(Order.assigned_staff))
        .options(selectinload(Order.payment))
    )
    count_query = select(func.count()).select_from(Order).where(Order.company_id == company_id)

    if q:
        query = query.join(Order.customer).where(Customer.name.ilike(f"%{q}%"))
        count_query = count_query.join(Order.customer).where(Customer.name.ilike(f"%{q}%"))
    if status:
        query = query.where(Order.status == status)
        count_query = count_query.where(Order.status == status)

    query = query.offset(offset).limit(limit).order_by(Order.created_at.desc())

    result = await db.execute(query)
    orders = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": str(o.id),
                    "company_id": str(o.company_id),
                    "customer_id": str(o.customer_id),
                    "customer_name": o.customer.name if o.customer else None,
                    "staff_id": str(o.staff_id) if o.staff_id else None,
                    "staff_name": o.assigned_staff.name if o.assigned_staff else None,
                    "status": o.status,
                    "total_amount": float(o.total_amount),
                    "scheduled_at": o.scheduled_at.isoformat() if o.scheduled_at else None,
                    "address": o.address,
                    "notes": o.notes,
                    "payment": {
                        "id": str(o.payment.id),
                        "status": o.payment.status,
                        "method": o.payment.method,
                        "amount": float(o.payment.amount),
                        "transaction_id": o.payment.transaction_id,
                        "paid_at": o.payment.paid_at.isoformat() if o.payment.paid_at else None,
                    } if o.payment else None,
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
                    "created_at": o.created_at.isoformat(),
                }
                for o in orders
            ],
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


@router.post("", response_model=dict, status_code=201)
async def create_order(
    req: OrderCreate,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate customer
    cust_result = await db.execute(
        select(Customer).where(Customer.id == req.customer_id, Customer.company_id == company_id)
    )
    if not cust_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="客户不存在")

    order = Order(
        company_id=company_id,
        customer_id=req.customer_id,
        staff_id=req.staff_id,
        status=req.status,
        total_amount=req.total_amount,
        scheduled_at=req.scheduled_at,
        address=req.address,
        notes=req.notes,
        created_by_id=current_user.id,
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

    # ── 通知（fire-and-forget）─────────────────
    _schedule_notification("order_created", order, db)

    return {"message": "订单创建成功", "order_id": str(order.id)}


@router.put("/{order_id}/status", response_model=dict)
async def update_order_status(
    order_id: str,
    req: OrderStatusUpdateRequest,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    valid_statuses = ["pending", "confirmed", "dispatched", "in_progress", "completed", "cancelled"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.company_id == company_id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    order.status = req.status
    if req.staff_id:
        order.staff_id = req.staff_id

    await db.commit()

    # ── 状态变更通知 ──────────────────────
    if req.status == "dispatched":
        _schedule_notification("staff_dispatched", order, db)
    elif req.status == "completed":
        _schedule_notification("order_completed", order, db)

    return {"message": f"订单状态已更新为 {req.status}"}
