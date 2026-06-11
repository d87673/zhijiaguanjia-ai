from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Order, OrderItem, Customer, Staff, Service
from app.schemas.schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


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
        "orders": [
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

    return {"message": "订单创建成功", "order_id": str(order.id)}


@router.put("/{order_id}/status", response_model=dict)
async def update_order_status(
    order_id: str,
    status: str = Query(...),
    staff_id: str = Query(None),
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    valid_statuses = ["pending", "confirmed", "dispatched", "in_progress", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.company_id == company_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    order.status = status
    if staff_id:
        order.staff_id = staff_id

    await db.commit()
    return {"message": f"订单状态已更新为 {status}"}
