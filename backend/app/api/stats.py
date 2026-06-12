from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Order, Customer, Staff, Payment

router = APIRouter(prefix="/stats", tags=["Stats"])


ORDER_STATUSES = ["pending", "confirmed", "dispatched", "in_progress", "completed", "cancelled"]


@router.get("", response_model=dict)
async def get_stats(
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    async def count(model, **filters):
        q = select(func.count()).select_from(model).where(model.company_id == company_id)
        for k, v in filters.items():
            q = q.where(getattr(model, k) == v)
        r = await db.execute(q)
        return r.scalar() or 0

    async def count_today(model):
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        r = await db.execute(
            select(func.count()).select_from(model).where(
                model.company_id == company_id, model.created_at >= today
            )
        )
        return r.scalar() or 0

    async def count_this_month(model, date_field=None):
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        field = date_field or model.created_at
        r = await db.execute(
            select(func.count()).select_from(model).where(
                model.company_id == company_id, field >= start
            )
        )
        return r.scalar() or 0

    # Summary counts
    total_orders = await count(Order)
    pending_orders = await count(Order, status="pending")
    completed_orders = await count(Order, status="completed")
    today_orders = await count_today(Order)
    month_orders = await count_this_month(Order)
    total_customers = await count(Customer)
    month_customers = await count_this_month(Customer)
    total_staff = await count(Staff, is_active=True)

    # Revenue
    paid_result = await db.execute(
        select(func.sum(Payment.amount)).select_from(Payment)
        .join(Order, Payment.order_id == Order.id)
        .where(Order.company_id == company_id, Payment.status == "paid")
    )
    total_revenue = float(paid_result.scalar() or 0)

    month_rev_result = await db.execute(
        select(func.sum(Payment.amount)).select_from(Payment)
        .join(Order, Payment.order_id == Order.id)
        .where(
            Order.company_id == company_id,
            Payment.status == "paid",
            Payment.paid_at >= datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        )
    )
    month_revenue = float(month_rev_result.scalar() or 0)

    # Status distribution
    status_dist = []
    for s in ORDER_STATUSES:
        cnt = await count(Order, status=s)
        status_dist.append({"status": s, "count": cnt})

    # Last 7 days
    last_7 = []
    for i in range(6, -1, -1):
        day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        next_day = day + timedelta(days=1)
        r = await db.execute(
            select(func.count()).select_from(Order).where(
                Order.company_id == company_id,
                Order.created_at >= day,
                Order.created_at < next_day,
            )
        )
        last_7.append({"date": day.strftime("%m/%d"), "count": r.scalar() or 0, "revenue": 0})

    # Recent orders
    recent_result = await db.execute(
        select(Order)
        .options(selectinload(Order.customer))
        .where(Order.company_id == company_id)
        .order_by(Order.created_at.desc())
        .limit(5)
    )
    recent = recent_result.scalars().all()

    return {
        "summary": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "today_orders": today_orders,
            "this_month_orders": month_orders,
            "total_customers": total_customers,
            "active_customers": month_customers,
            "total_staff": total_staff,
            "total_revenue": total_revenue,
            "this_month_revenue": month_revenue,
        },
        "status_distribution": status_dist,
        "last_7_days": [
            {"date": d["date"], "orders": d["count"], "revenue": d["revenue"]}
            for d in last_7
        ],
        "recent_orders": [
            {
                "id": str(o.id),
                "customer_name": o.customer.name if o.customer else "(客户信息)",
                "status": o.status,
                "total_amount": float(o.total_amount),
                "created_at": o.created_at.isoformat(),
                "address": o.address,
            }
            for o in recent
        ],
    }
