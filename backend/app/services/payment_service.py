"""
智家管家AI — 支付服务抽象层
================================
统一支付网关：微信支付 + 支付宝

设计原则：
- Provider 模式：通过抽象基类 PaymentProvider 统一接口
- 签名为纯 Python 实现（使用 cryptography 库），不依赖 SDK 黑盒
- 每个 Provider 明确声明所需配置项（从 company.settings.api_keys 读取）
- 回调通知端点无需登录态，仅依赖支付平台签名验证

使用方式:
    from app.services.payment_service import get_payment_service
    service = await get_payment_service(company_id, db)
    result = await service.create_payment(order_id, amount, desc, method="wechat")
"""

from __future__ import annotations

import json
import time
import uuid
import hashlib
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from enum import Enum

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.models import Order, Payment, Company


# ═══════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════

class PayMethod(str, Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"


class PayType(str, Enum):
    """支付场景"""
    NATIVE = "native"       # 微信 Native（扫码支付，返回 code_url）
    JSAPI = "jsapi"         # 微信 JSAPI（公众号/小程序内支付，需要 openid）
    H5 = "h5"               # 微信 H5（移动端浏览器）
    QR = "qr"               # 支付宝预下单（扫码支付）
    PAGE = "page"           # 支付宝网页支付（PC 跳转）


@dataclass
class PaymentResult:
    """统一下单返回"""
    success: bool
    pay_url: Optional[str] = None        # 支付链接 / code_url
    qr_content: Optional[str] = None     # 二维码内容（同 pay_url）
    out_trade_no: Optional[str] = None   # 商户订单号
    prepay_id: Optional[str] = None      # 预支付 ID
    error: Optional[str] = None
    provider_data: Dict[str, Any] = field(default_factory=dict)  # 原始响应


@dataclass
class CallbackData:
    """支付回调标准化"""
    success: bool
    out_trade_no: str        # 商户订单号
    transaction_id: str      # 平台交易号
    amount: float            # 实付金额（元）
    method: str              # wechat / alipay
    payer_info: Dict[str, str] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════
# 抽象基类
# ═══════════════════════════════════════════════════

class PaymentProvider(ABC):
    """支付渠道抽象"""

    method: str  # "wechat" | "alipay"

    @abstractmethod
    async def create_payment(
        self,
        out_trade_no: str,
        amount_yuan: float,
        description: str,
        pay_type: PayType = PayType.NATIVE,
        **kwargs,
    ) -> PaymentResult:
        """创建支付订单。各渠道支持的 pay_type 不同。"""
        ...

    @abstractmethod
    async def query_payment(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        """查询支付单状态"""
        ...

    @abstractmethod
    async def verify_callback(
        self, headers: Dict[str, str], body: bytes
    ) -> CallbackData:
        """验证并解析支付回调"""
        ...

    @abstractmethod
    async def close_payment(self, out_trade_no: str) -> bool:
        """关闭未支付的订单"""
        ...

    @abstractmethod
    async def apply_refund(
        self,
        out_trade_no: str,
        refund_amount_yuan: float,
        reason: str = "",
    ) -> Tuple[bool, str]:
        """申请退款。返回 (成功, 退款单号或错误信息)。"""
        ...


# ═══════════════════════════════════════════════════
# 微信支付 APIv3
# ═══════════════════════════════════════════════════

class WeChatPayProvider(PaymentProvider):
    """
    微信支付 APIv3 实现

    所需配置项（company.settings.api_keys）:
      - wechat_mch_id       : 商户号
      - wechat_appid        : 公众号/小程序 AppID
      - wechat_api_v3_key   : APIv3 密钥（32 字节，用于回调解密）
      - wechat_cert_serial  : 商户 API 证书序列号
      - wechat_private_key  : 商户 API 私钥（PEM 格式）
      - payment_notify_host : 回调通知域名（如 https://api.example.com）
    """

    BASE_URL = "https://api.mch.weixin.qq.com"
    method = "wechat"

    def __init__(self, config: Dict[str, str]):
        self.mch_id = config.get("wechat_mch_id", "")
        self.appid = config.get("wechat_appid", "")
        self.api_v3_key = config.get("wechat_api_v3_key", "").encode()
        self.cert_serial = config.get("wechat_cert_serial", "")
        self.notify_host = config.get("payment_notify_host", "").rstrip("/")

        pem = config.get("wechat_private_key", "")
        self.private_key: Optional[RSAPrivateKey] = None
        if pem:
            pem = pem.strip()
            if "-----BEGIN" not in pem:
                pem = f"-----BEGIN PRIVATE KEY-----\n{pem}\n-----END PRIVATE KEY-----"
            self.private_key = serialization.load_pem_private_key(
                pem.encode(), password=None
            )

    # ── 签名工具 ────────────────────────────────

    def _sign(self, message: str) -> str:
        """RSA-SHA256 签名 → base64"""
        if not self.private_key:
            raise RuntimeError("微信商户私钥未配置")
        sig = self.private_key.sign(
            message.encode(), asym_padding.PKCS1v15(), hashes.SHA256()
        )
        return base64.b64encode(sig).decode()

    def _make_auth(self, method: str, path: str, body: str = "") -> str:
        """构造 Authorization 请求头"""
        nonce = uuid.uuid4().hex[:32]
        ts = int(time.time())
        message = f"{method}\n{path}\n{ts}\n{nonce}\n{body}\n"
        signature = self._sign(message)
        return (
            f'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.mch_id}",'
            f'nonce_str="{nonce}",'
            f'timestamp="{ts}",'
            f'serial_no="{self.cert_serial}",'
            f'signature="{signature}"'
        )

    def _build_notify_url(self) -> str:
        return f"{self.notify_host}/api/v1/payments/notify/wechat"

    # ── 统一下单 ────────────────────────────────

    async def create_payment(
        self,
        out_trade_no: str,
        amount_yuan: float,
        description: str,
        pay_type: PayType = PayType.NATIVE,
        openid: str = "",
    ) -> PaymentResult:
        path = f"/v3/pay/transactions/{pay_type.value}"
        body: Dict[str, Any] = {
            "appid": self.appid,
            "mchid": self.mch_id,
            "description": description[:127],
            "out_trade_no": out_trade_no,
            "notify_url": self._build_notify_url(),
            "amount": {
                "total": int(round(amount_yuan * 100)),
                "currency": "CNY",
            },
        }

        # 场景附加字段
        if pay_type == PayType.JSAPI:
            if not openid:
                return PaymentResult(success=False, error="JSAPI 支付需要 openid")
            body["payer"] = {"openid": openid}
        elif pay_type == PayType.H5:
            body["scene_info"] = {
                "payer_client_ip": "0.0.0.0",  # 服务端发起，可传 0
                "h5_info": {"type": "Wap"},
            }

        body_str = json.dumps(body, ensure_ascii=False)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.BASE_URL}{path}",
                    content=body_str,
                    headers={
                        "Authorization": self._make_auth("POST", path, body_str),
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
            data = resp.json() if resp.text else {}
        except Exception as e:
            return PaymentResult(success=False, error=f"微信支付请求失败: {e}")

        if resp.status_code in (200, 202):
            code_url = data.get("code_url", "")
            return PaymentResult(
                success=True,
                out_trade_no=out_trade_no,
                pay_url=code_url,
                qr_content=code_url or data.get("h5_url"),
                prepay_id=data.get("prepay_id"),
                provider_data=data,
            )

        return PaymentResult(
            success=False,
            error=data.get("message", resp.text[:300]),
            provider_data=data,
        )

    # ── 查询 ────────────────────────────────────

    async def query_payment(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        """按商户订单号查询"""
        path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={self.mch_id}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.BASE_URL}{path}",
                    headers={
                        "Authorization": self._make_auth("GET", path),
                        "Accept": "application/json",
                    },
                )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    # ── 回调验证 ────────────────────────────────

    async def verify_callback(
        self, headers: Dict[str, str], body: bytes
    ) -> CallbackData:
        """
        验证微信支付回调
        1. 验签（Wechatpay-Signature 请求头）
        2. 用 APIv3 密钥解密 resource.ciphertext
        """
        fail = CallbackData(
            success=False,
            out_trade_no="",
            transaction_id="",
            amount=0,
            method="wechat",
        )

        try:
            serial = headers.get("wechatpay-serial", "")
            timestamp = headers.get("wechatpay-timestamp", "")
            nonce = headers.get("wechatpay-nonce", "")
            wechat_sig = headers.get("wechatpay-signature", "")

            if not all([serial, timestamp, nonce, wechat_sig]):
                fail.raw = {"reason": "缺少回调请求头"}
                return fail

            # 验签
            message = f"{timestamp}\n{nonce}\n{body.decode()}\n"
            if self.private_key:
                expected_sig = self._sign(message)
                if not _timing_safe_compare(expected_sig, wechat_sig):
                    fail.raw = {"reason": "签名验证失败"}
                    return fail

            # 解密
            resource: Dict = json.loads(body).get("resource", {})
            ciphertext = resource.get("ciphertext", "")
            nonce_b64 = resource.get("nonce", "")
            associated_data = resource.get("associated_data", "")

            if not ciphertext or not self.api_v3_key:
                fail.raw = {"reason": "缺少密文或 APIv3 密钥"}
                return fail

            aesgcm = AESGCM(self.api_v3_key)
            plain = aesgcm.decrypt(
                base64.b64decode(nonce_b64),
                base64.b64decode(ciphertext),
                associated_data.encode(),
            )
            tx = json.loads(plain)

            return CallbackData(
                success=tx.get("trade_state") == "SUCCESS",
                out_trade_no=tx.get("out_trade_no", ""),
                transaction_id=tx.get("transaction_id", ""),
                amount=float(tx.get("amount", {}).get("total", 0)) / 100,
                method="wechat",
                payer_info={"openid": tx.get("payer", {}).get("openid", "")},
                raw=tx,
            )

        except Exception as e:
            fail.raw = {"reason": f"回调处理异常: {e}"}
            return fail

    # ── 关单 / 退款 ─────────────────────────────

    async def close_payment(self, out_trade_no: str) -> bool:
        path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}/close"
        body = json.dumps({"mchid": self.mch_id})
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.BASE_URL}{path}",
                    content=body,
                    headers={
                        "Authorization": self._make_auth("POST", path, body),
                        "Content-Type": "application/json",
                    },
                )
            return resp.status_code == 204
        except Exception:
            return False

    async def apply_refund(
        self, out_trade_no: str, refund_amount_yuan: float, reason: str = ""
    ) -> Tuple[bool, str]:
        path = "/v3/refund/domestic/refunds"
        refund_no = f"RF{out_trade_no[-28:]}{int(time.time()) % 100000:05d}"
        body = json.dumps({
            "out_trade_no": out_trade_no,
            "out_refund_no": refund_no,
            "amount": {
                "refund": int(round(refund_amount_yuan * 100)),
                "total": int(round(refund_amount_yuan * 100)),  # 简化；实际需从订单查
                "currency": "CNY",
            },
            "reason": reason or "用户退款",
        })
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.BASE_URL}{path}",
                    content=body,
                    headers={
                        "Authorization": self._make_auth("POST", path, body),
                        "Content-Type": "application/json",
                    },
                )
            data = resp.json() if resp.text else {}
            if resp.status_code in (200, 202):
                return True, refund_no
            return False, data.get("message", resp.text[:200])
        except Exception as e:
            return False, str(e)


# ═══════════════════════════════════════════════════
# 支付宝（REST API）
# ═══════════════════════════════════════════════════

class AlipayProvider(PaymentProvider):
    """
    支付宝支付实现

    所需配置项（company.settings.api_keys）:
      - alipay_app_id        : 应用 ID
      - alipay_private_key   : 应用私钥（PEM）
      - alipay_public_key    : 支付宝公钥（PEM, 用于回调验签）
      - payment_notify_host  : 回调通知域名
    """

    GATEWAY = "https://openapi.alipay.com/gateway.do"
    method = "alipay"

    def __init__(self, config: Dict[str, str]):
        self.app_id = config.get("alipay_app_id", "")
        self.notify_host = config.get("payment_notify_host", "").rstrip("/")

        # 加载私钥
        priv_pem = config.get("alipay_private_key", "")
        self.private_key: Optional[RSAPrivateKey] = None
        if priv_pem:
            priv_pem = priv_pem.strip()
            if "-----BEGIN" not in priv_pem:
                priv_pem = (
                    f"-----BEGIN RSA PRIVATE KEY-----\n{priv_pem}\n"
                    f"-----END RSA PRIVATE KEY-----"
                )
            self.private_key = serialization.load_pem_private_key(
                priv_pem.encode(), password=None
            )

        # 加载支付宝公钥
        pub_pem = config.get("alipay_public_key", "")
        self.public_key = None
        if pub_pem:
            pub_pem = pub_pem.strip()
            if "-----BEGIN" not in pub_pem:
                pub_pem = (
                    f"-----BEGIN PUBLIC KEY-----\n{pub_pem}\n"
                    f"-----END PUBLIC KEY-----"
                )
            self.public_key = serialization.load_pem_public_key(pub_pem.encode())

    # ── 签名 ────────────────────────────────────

    def _sign_params(self, params: Dict[str, str]) -> str:
        """对参数字典排序 → query_string → RSA-SHA256 签名 → base64"""
        if not self.private_key:
            raise RuntimeError("支付宝私钥未配置")
        sorted_items = sorted(params.items())
        qs = "&".join(f"{k}={v}" for k, v in sorted_items if v)
        sig = self.private_key.sign(
            qs.encode(), asym_padding.PKCS1v15(), hashes.SHA256()
        )
        return base64.b64encode(sig).decode()

    def _verify_signature(self, params: Dict[str, str], sign: str) -> bool:
        """验证支付宝回调签名"""
        if not self.public_key:
            return False
        sorted_items = sorted(
            [(k, v) for k, v in params.items() if k not in ("sign", "sign_type")],
            key=lambda x: x[0],
        )
        qs = "&".join(f"{k}={v}" for k, v in sorted_items if v)
        try:
            self.public_key.verify(
                base64.b64decode(sign),
                qs.encode(),
                asym_padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    # ── 统一下单 ────────────────────────────────

    async def create_payment(
        self,
        out_trade_no: str,
        amount_yuan: float,
        description: str,
        pay_type: PayType = PayType.QR,
        **kwargs,
    ) -> PaymentResult:
        method = (
            "alipay.trade.precreate"      # 扫码付
            if pay_type == PayType.QR
            else "alipay.trade.page.pay"  # 网页付
        )

        biz_content = {
            "out_trade_no": out_trade_no,
            "total_amount": f"{amount_yuan:.2f}",
            "subject": description[:256],
            "product_code": (
                "FACE_TO_FACE_PAYMENT" if pay_type == PayType.QR
                else "FAST_INSTANT_TRADE_PAY"
            ),
        }

        params = {
            "app_id": self.app_id,
            "method": method,
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": f"{self.notify_host}/api/v1/payments/notify/alipay",
            "biz_content": json.dumps(biz_content, ensure_ascii=False),
        }

        sign = self._sign_params(params)
        params["sign"] = sign

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    self.GATEWAY,
                    data=params,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            text = resp.text

            # 支付宝返回 JSON
            resp_data = json.loads(text)
            resp_inner = (
                resp_data.get("alipay_trade_precreate_response")
                or resp_data.get("alipay_trade_page_pay_response")
                or {}
            )
        except Exception as e:
            return PaymentResult(success=False, error=f"支付宝请求失败: {e}")

        if resp_inner.get("code") == "10000":
            return PaymentResult(
                success=True,
                out_trade_no=out_trade_no,
                pay_url=resp_inner.get("qr_code") or "",
                qr_content=resp_inner.get("qr_code", ""),
                provider_data=resp_inner,
            )

        return PaymentResult(
            success=False,
            error=f"{resp_inner.get('sub_msg', resp_inner.get('msg', '未知错误'))}",
            provider_data=resp_inner,
        )

    # ── 查询 ────────────────────────────────────

    async def query_payment(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        biz_content = json.dumps({"out_trade_no": out_trade_no})
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.query",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": biz_content,
        }
        params["sign"] = self._sign_params(params)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.GATEWAY, data=params)
            data = json.loads(resp.text)
            inner = data.get("alipay_trade_query_response", {})
            if inner.get("code") == "10000":
                return inner
        except Exception:
            pass
        return None

    # ── 回调验证 ────────────────────────────────

    async def verify_callback(
        self, headers: Dict[str, str], body: bytes
    ) -> CallbackData:
        """验证支付宝异步通知"""
        fail = CallbackData(
            success=False,
            out_trade_no="",
            transaction_id="",
            amount=0,
            method="alipay",
        )

        try:
            # 解析 form-encoded body
            from urllib.parse import parse_qs
            params = {
                k: v[0] if isinstance(v, list) else v
                for k, v in parse_qs(body.decode()).items()
            }

            sign = params.pop("sign", "")
            sign_type = params.pop("sign_type", "RSA2")

            if not self._verify_signature(params, sign):
                fail.raw = {"reason": "支付宝签名验证失败"}
                return fail

            trade_status = params.get("trade_status", "")
            success = trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED")

            return CallbackData(
                success=success,
                out_trade_no=params.get("out_trade_no", ""),
                transaction_id=params.get("trade_no", ""),
                amount=float(params.get("total_amount", 0)),
                method="alipay",
                payer_info={"buyer_id": params.get("buyer_id", "")},
                raw=params,
            )

        except Exception as e:
            fail.raw = {"reason": f"回调处理异常: {e}"}
            return fail

    # ── 关单 / 退款 ─────────────────────────────

    async def close_payment(self, out_trade_no: str) -> bool:
        biz_content = json.dumps({"out_trade_no": out_trade_no})
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.close",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": biz_content,
        }
        params["sign"] = self._sign_params(params)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.GATEWAY, data=params)
            data = json.loads(resp.text)
            return data.get("alipay_trade_close_response", {}).get("code") == "10000"
        except Exception:
            return False

    async def apply_refund(
        self, out_trade_no: str, refund_amount_yuan: float, reason: str = ""
    ) -> Tuple[bool, str]:
        biz_content = json.dumps({
            "out_trade_no": out_trade_no,
            "refund_amount": f"{refund_amount_yuan:.2f}",
            "refund_reason": reason or "用户退款",
        })
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.refund",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": biz_content,
        }
        params["sign"] = self._sign_params(params)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.GATEWAY, data=params)
            data = json.loads(resp.text)
            inner = data.get("alipay_trade_refund_response", {})
            if inner.get("code") == "10000":
                return True, inner.get("trade_no", out_trade_no)
            return False, inner.get("sub_msg", inner.get("msg", "退款失败"))
        except Exception as e:
            return False, str(e)


# ═══════════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════════

def _get_config(company: Company) -> Dict[str, str]:
    """从 company.settings 提取支付配置"""
    settings = dict(company.settings or {})
    api_keys = dict(settings.get("api_keys", {}))
    # 同时合并顶层的通知域名（如果有）
    for key in ("payment_notify_host",):
        if key in settings:
            api_keys.setdefault(key, settings[key])
    return api_keys


def get_provider(method: str, config: Dict[str, str]) -> Optional[PaymentProvider]:
    """根据支付方式获取 Provider 实例"""
    if method == "wechat":
        mch_id = config.get("wechat_mch_id")
        if not mch_id:
            return None
        return WeChatPayProvider(config)
    elif method == "alipay":
        app_id = config.get("alipay_app_id")
        if not app_id:
            return None
        return AlipayProvider(config)
    return None


async def get_payment_service(
    company_id: str,
    method: str,
    db: AsyncSession,
) -> Optional[PaymentProvider]:
    """
    获取支付服务实例（读 DB 配置）

    用法:
        service = await get_payment_service(company_id, "wechat", db)
        if service is None:
            raise HTTPException(400, "微信支付未配置")
        result = await service.create_payment(...)
    """
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        return None
    config = _get_config(company)
    return get_provider(method, config)


def get_provider_from_company(company: Company, method: str) -> Optional[PaymentProvider]:
    """直接从 Company ORM 对象获取 Provider（不需要再次查库）"""
    config = _get_config(company)
    return get_provider(method, config)


# ═══════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════

def gen_out_trade_no(order_id: str) -> str:
    """生成商户订单号 (≤32 字符)"""
    short = order_id.replace("-", "")[:24]
    ts = str(int(time.time() * 1000))[-8:]
    return f"ZJ{short}{ts}"


def parse_order_id(out_trade_no: str) -> str:
    """从 out_trade_no 反查 order_id（仅用于日志）"""
    # ZJ + 24 hex + 8 ts → order_id 部分为 hex
    hex_part = out_trade_no[2:-8]
    return (
        f"{hex_part[0:8]}-{hex_part[8:12]}-{hex_part[12:16]}-"
        f"{hex_part[16:20]}-{hex_part[20:24]}"
    )


def _timing_safe_compare(a: str, b: str) -> bool:
    """时间恒定字符串比较"""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
