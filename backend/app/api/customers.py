from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Customer
from app.schemas.schemas import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=dict)
async def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    offset = (page - 1) * limit
    query = select(Customer).where(Customer.company_id == company_id).options(selectinload(Customer.orders))
    count_query = select(func.count()).select_from(Customer).where(Customer.company_id == company_id)

    if q:
        query = query.where(
            Customer.name.ilike(f"%{q}%")
            | Customer.phone.ilike(f"%{q}%")
            | Customer.email.ilike(f"%{q}%")
        )
        count_query = count_query.where(
            Customer.name.ilike(f"%{q}%")
            | Customer.phone.ilike(f"%{q}%")
            | Customer.email.ilike(f"%{q}%")
        )

    query = query.offset(offset).limit(limit).order_by(Customer.created_at.desc())

    result = await db.execute(query)
    customers = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "success": True,
        "data": {
            "items": [
                {**CustomerResponse.model_validate(c).model_dump(), "order_count": len(c.orders) if c.orders else 0}
                for c in customers
            ],
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    req: CustomerCreate,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = Customer(company_id=company_id, **req.model_dump())
    db.add(customer)
    await db.flush()
    await db.commit()
    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    req: CustomerCreate,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.company_id == company_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    for key, value in req.model_dump().items():
        setattr(customer, key, value)

    await db.commit()
    return CustomerResponse.model_validate(customer)


@router.delete("/{customer_id}", response_model=dict)
async def delete_customer(
    customer_id: str,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.company_id == company_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    await db.delete(customer)
    await db.commit()
    return {"message": "删除成功"}
