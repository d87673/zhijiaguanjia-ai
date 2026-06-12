from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Service
from app.schemas.schemas import ServiceCreate, ServiceUpdate, ServiceResponse

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=dict)
async def list_services(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: str = Query(""),
    category: str = Query(""),
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    offset = (page - 1) * limit
    query = select(Service).where(Service.company_id == company_id)
    count_query = select(func.count()).select_from(Service).where(Service.company_id == company_id)

    if q:
        query = query.where(Service.name.ilike(f"%{q}%"))
        count_query = count_query.where(Service.name.ilike(f"%{q}%"))
    if category:
        query = query.where(Service.category == category)
        count_query = count_query.where(Service.category == category)

    query = query.offset(offset).limit(limit).order_by(Service.created_at.desc())

    result = await db.execute(query)
    services = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "success": True,
        "data": {
            "items": [ServiceResponse.model_validate(s).model_dump() for s in services],
            "total": total,
            "page": page,
            "limit": limit,
        },
    }


@router.post("", response_model=ServiceResponse, status_code=201)
async def create_service(
    req: ServiceCreate,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = Service(company_id=company_id, **req.model_dump())
    db.add(svc)
    await db.flush()
    await db.commit()
    return ServiceResponse.model_validate(svc)


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    req: ServiceUpdate,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.company_id == company_id)
    )
    svc = result.scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="服务不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(svc, key, value)

    await db.commit()
    return ServiceResponse.model_validate(svc)


@router.delete("/{service_id}", response_model=dict)
async def delete_service(
    service_id: str,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.company_id == company_id)
    )
    svc = result.scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="服务不存在")
    await db.delete(svc)
    await db.commit()
    return {"message": "删除成功"}
