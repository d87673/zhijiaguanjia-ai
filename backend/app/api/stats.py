from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        r = await db.execute(
            select(func.count()).select_from(model).where(
                model.company_id == company_id, model.created_at >= today
            )
        )
        return r.scalar() or 0

    async def count_this_month(model, date_field=None):
        now = datetime.utcnow()
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
            Payment.paid_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
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
        day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
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
        .where(Order.company_id == company_id)
        .order_by(Order.created_at.desc())
        .limit(5)
    )
    recent = recent_result.scalars().all()

    return {
        "summary": {
            "totalOrders": total_orders,
            "pendingOrders": pending_orders,
            "completedOrders": completed_orders,
            "todayOrders": today_orders,
            "thisMonthOrders": month_orders,
            "totalCustomers": total_customers,
            "activeCustomers": month_customers,
            "totalStaff": total_staff,
            "totalRevenue": total_revenue,
            "thisMonthRevenue": month_revenue,
        },
        "statusDistribution": status_dist,
        "last7Days": last_7,
        "recentOrders": [
            {
                "id": str(o.id),
                "customerName": "(客户信息)",
                "status": o.status,
                "totalAmount": float(o.total_amount),
                "createdAt": o.created_at.isoformat(),
            }
            for o in recent
        ],
    }
