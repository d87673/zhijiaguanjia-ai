from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Staff
from app.schemas.schemas import StaffCreate, StaffResponse

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("", response_model=dict)
async def list_staff(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    offset = (page - 1) * limit
    query = select(Staff).where(Staff.company_id == company_id)
    count_query = select(func.count()).select_from(Staff).where(Staff.company_id == company_id)

    if q:
        query = query.where(Staff.name.ilike(f"%{q}%") | Staff.phone.ilike(f"%{q}%"))
        count_query = count_query.where(Staff.name.ilike(f"%{q}%") | Staff.phone.ilike(f"%{q}%"))

    query = query.offset(offset).limit(limit).order_by(Staff.created_at.desc())

    result = await db.execute(query)
    staff_list = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "staff": [
            {**StaffResponse.model_validate(s).model_dump(), "order_count": len(s.orders) if s.orders else 0}
            for s in staff_list
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("", response_model=StaffResponse, status_code=201)
async def create_staff(
    req: StaffCreate,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    staff = Staff(company_id=company_id, **req.model_dump())
    db.add(staff)
    await db.flush()
    await db.commit()
    return StaffResponse.model_validate(staff)


@router.delete("/{staff_id}", response_model=dict)
async def delete_staff(
    staff_id: str,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.company_id == company_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="员工不存在")
    await db.delete(s)
    await db.commit()
    return {"message": "删除成功"}
