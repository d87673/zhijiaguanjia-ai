from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Company
from app.schemas.schemas import CompanyUpdateRequest, CompanyKeysUpdateRequest

router = APIRouter(prefix="/company", tags=["Company"])


@router.put("", response_model=dict)
async def update_company(
    req: CompanyUpdateRequest,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    update_data = req.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        return {"message": "没有需要更新的字段"}

    current_settings = dict(company.settings or {})
    if "name" in update_data:
        company.name = update_data.pop("name")
    if "phone" in update_data:
        current_settings["phone"] = update_data.pop("phone")
    if "address" in update_data:
        current_settings["address"] = update_data.pop("address")
    company.settings = current_settings
    flag_modified(company, "settings")

    await db.commit()
    return {"message": "公司信息已更新"}


@router.put("/keys", response_model=dict)
async def update_company_keys(
    req: CompanyKeysUpdateRequest,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    update_data = req.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        return {"message": "没有需要更新的字段"}

    current_settings = dict(company.settings or {})
    api_keys = dict(current_settings.get("api_keys", {}))
    api_keys.update(update_data)
    current_settings["api_keys"] = api_keys
    company.settings = current_settings
    flag_modified(company, "settings")

    await db.commit()
    return {"message": "密钥已更新"}


@router.get("", response_model=dict)
async def get_company(
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    return {
        "id": str(company.id),
        "name": company.name,
        "slug": company.slug,
        "plan": company.plan,
        "settings": company.settings,
        "created_at": company.created_at.isoformat(),
    }
