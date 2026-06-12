"""
智家管家AI — 支付 API 端点
=========================
POST   /payments/create      — 创建支付（统一下单）
POST   /payments/notify/wechat — 微信支付回调（无需登录）
POST   /payments/notify/alipay — 支付宝支付回调（无需登录）
GET    /payments/{id}        — 查询支付状态
POST   /payments/{id}/refund — 退款
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_company
from app.models.models import User, Order, Payment, Company
from app.schemas.schemas import PaymentCreateRequest, PaymentRefundRequest
from app.services.payment_service import (
    get_payment_service,
    get_provider_from_company,
    gen_out_trade_no,
    PayType,
)
import logging

logger = logging.getLogger(__name__)
from datetime import datetime, timezone

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create", response_model=dict)
async def create_payment(
    req: PaymentCreateRequest,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建支付单并返回支付链接 / 二维码内容。

    请求体:
    {
        "order_id": "uuid",
        "method": "wechat",       // wechat | alipay
        "pay_type": "native",     // native(扫码) | jsapi(小程序) | h5 | qr | page
        "openid": ""              // JSAPI 时必填
    }
    """
    # 1. 查订单
    result = await db.execute(
        select(Order)
        .where(Order.id == req.order_id, Order.company_id == company_id)
        .options(selectinload(Order.payment))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.total_amount <= 0:
        raise HTTPException(status_code=400, detail="订单金额为 0，无需支付")

    # 2. 检查是否已有支付单
    if order.payment and order.payment.status == "paid":
        raise HTTPException(status_code=400, detail="该订单已支付")

    # 3. 获取支付 Provider
    provider = await get_payment_service(company_id, req.method, db)
    if provider is None:
        raise HTTPException(
            status_code=400,
            detail=f"{req.method} 支付未配置。请在设置页面填写必需的 API 密钥。",
        )

    # 4. 创建或复用本地 Payment 记录
    if order.payment:
        payment = order.payment
        payment.method = req.method
        payment.status = "pending"
        payment.amount = float(order.total_amount)
    else:
        payment = Payment(
            order_id=order.id,
            amount=float(order.total_amount),
            method=req.method,
            status="pending",
        )
        db.add(payment)

    await db.flush()

    # 5. 调用 Provider 创建支付
    out_trade_no = gen_out_trade_no(order.id)
    pay_type = PayType(req.pay_type) if req.pay_type else PayType.NATIVE

    pay_result = await provider.create_payment(
        out_trade_no=out_trade_no,
        amount_yuan=float(order.total_amount),
        description=f"家政服务订单 - {order.id[:8]}",
        pay_type=pay_type,
        openid=req.openid or "",
    )

    if not pay_result.success:
        raise HTTPException(
            status_code=502,
            detail=f"支付创建失败: {pay_result.error}",
        )

    # 6. 保存 out_trade_no
    payment.transaction_id = out_trade_no
    await db.commit()

    return {
        "success": True,
        "data": {
            "payment_id": str(payment.id),
            "out_trade_no": out_trade_no,
            "pay_url": pay_result.pay_url,
            "qr_content": pay_result.qr_content,
            "prepay_id": pay_result.prepay_id,
            "amount": float(order.total_amount),
            "method": req.method,
        },
    }


@router.get("/{payment_id}", response_model=dict)
async def get_payment(
    payment_id: str,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """查询支付状态"""
    result = await db.execute(
        select(Payment)
        .join(Order)
        .where(Payment.id == payment_id, Order.company_id == company_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    return {
        "success": True,
        "data": {
            "id": str(payment.id),
            "order_id": str(payment.order_id),
            "amount": float(payment.amount),
            "method": payment.method,
            "status": payment.status,
            "transaction_id": payment.transaction_id,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        },
    }


@router.post("/{payment_id}/refund", response_model=dict)
async def refund_payment(
    payment_id: str,
    req: PaymentRefundRequest,
    company_id: str = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """退款"""
    result = await db.execute(
        select(Payment)
        .join(Order)
        .where(Payment.id == payment_id, Order.company_id == company_id)
        .options(selectinload(Payment.order))
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    if payment.status != "paid":
        raise HTTPException(status_code=400, detail="只有已支付的订单可以退款")

    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()

    provider = get_provider_from_company(company, payment.method)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"{payment.method} 支付未配置")

    refund_amount = req.amount if req.amount > 0 else float(payment.amount)
    success, msg = await provider.apply_refund(
        payment.transaction_id or "",
        refund_amount,
        req.reason,
    )

    if success:
        payment.status = "refunded"
        # 同步订单状态
        payment.order.status = "cancelled"
        await db.commit()
        return {"success": True, "data": {"refund_no": msg, "amount": refund_amount}}

    raise HTTPException(status_code=502, detail=f"退款失败: {msg}")


# ═══════════════════════════════════════════════════
# 支付回调 — 无需登录
# ═══════════════════════════════════════════════════

@router.post("/notify/wechat", response_model=dict)
async def wechat_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    微信支付回调通知

    微信会发送带有签名的 JSON 通知。此处：
    1. 反查 company（从 body 中提取，遍历 or 通过 notify_url 参数）
    2. 验证签名 + 解密
    3. 更新 Payment & Order 状态
    """
    body = await request.body()
    headers = dict(request.headers)

    # 先解析 body 获取 out_trade_no
    import json as _json
    try:
        alert = _json.loads(body)
        resource = alert.get("resource", {})
        ciphertext = resource.get("ciphertext", "")
    except Exception:
        return {"code": "FAIL", "message": "Invalid JSON"}

    # 需要找到对应的 company → 尝试所有公司中已配置微信支付的
    companies_result = await db.execute(select(Company))
    companies = companies_result.scalars().all()

    callback_data = None
    for company in companies:
        provider = get_provider_from_company(company, "wechat")
        if provider is None:
            continue
        try:
            data = await provider.verify_callback(headers, body)
            if data.success or data.raw.get("out_trade_no"):
                callback_data = data
                break
        except Exception:
            continue

    if callback_data is None:
        logger.warning("微信回调无法匹配任何公司: {}", alert.get("id", ""))
        return {"code": "FAIL", "message": "No matching company"}

    if not callback_data.success:
        return {"code": "SUCCESS", "message": "通知已接收（非成功状态）"}

    # 更新支付记录
    await _handle_callback(db, callback_data)
    return {"code": "SUCCESS", "message": "OK"}


@router.post("/notify/alipay", response_model=dict)
async def alipay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    支付宝支付回调通知

    支付宝发送 form-encoded POST。
    查找匹配的公司 → 验签 → 更新状态。
    """
    body = await request.body()
    headers = dict(request.headers)

    from urllib.parse import parse_qs
    params = parse_qs(body.decode())
    out_trade_no = (params.get("out_trade_no", [""])[0]) if "out_trade_no" in params else ""

    companies_result = await db.execute(select(Company))
    companies = companies_result.scalars().all()

    callback_data = None
    for company in companies:
        provider = get_provider_from_company(company, "alipay")
        if provider is None:
            continue
        try:
            data = await provider.verify_callback(headers, body)
            if data.success or data.raw.get("out_trade_no"):
                callback_data = data
                break
        except Exception:
            continue

    if callback_data is None:
        return "fail"

    if not callback_data.success:
        return "success"

    await _handle_callback(db, callback_data)
    return "success"


# ═══════════════════════════════════════════════════
# 内部 Helper
# ═══════════════════════════════════════════════════

async def _handle_callback(db: AsyncSession, data):
    """统一处理支付回调：更新 Payment + Order"""
    out_trade_no = data.out_trade_no
    if not out_trade_no:
        return

    # 查 Payment（通过 transaction_id = out_trade_no）
    result = await db.execute(
        select(Payment)
        .where(Payment.transaction_id == out_trade_no)
        .options(selectinload(Payment.order))
    )
    payment = result.scalar_one_or_none()
    if not payment:
        logger.warning(f"支付回调找不到记录: out_trade_no={out_trade_no}")
        return

    if payment.status == "paid":
        return  # 已处理，幂等

    payment.status = "paid"
    payment.paid_at = datetime.now(timezone.utc)
    payment.method = data.method
    payment.transaction_id = data.transaction_id or payment.transaction_id

    # 更新订单状态
    if payment.order and payment.order.status in ("pending", "confirmed"):
        payment.order.status = "confirmed"

    await db.commit()
    logger.info(
        f"支付成功: order={payment.order_id}, "
        f"amount={data.amount}, method={data.method}, "
        f"txn={data.transaction_id}"
    )
