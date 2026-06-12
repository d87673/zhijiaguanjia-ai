"""
智家管家AI — 通知服务
=====================
邮件（SMTP）+ 短信（阿里云短信 / 腾讯云短信）

设计原则：
- Provider 抽象：可插拔的邮件和短信通道
- 模板化：通知内容由模板函数生成，不硬编码
- 异步发送：不阻塞主流程，发送失败不影响业务
- 配置存储：company.settings.api_keys 中配置

触发点（在业务 API 中调用）:
- 订单创建 → 客户收到确认通知
- 派单成功 → 客户收到派单通知、员工收到接单通知
- 服务完成 → 客户收到评价邀请
- 支付成功 → 客户收到付款凭证
"""

from __future__ import annotations

import json
import re
import smtplib
import hashlib
import hmac
import base64
import uuid
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Company


# ═══════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════

@dataclass
class Notification:
    """通知实体"""
    to_email: Optional[str] = None
    to_phone: Optional[str] = None
    subject: str = ""
    body_text: str = ""
    body_html: Optional[str] = None
    template_id: str = ""         # 短信模板 ID（阿里云/腾讯云）
    template_params: Dict[str, str] = field(default_factory=dict)


@dataclass
class NotifyResult:
    success: bool
    channel: str  # "email" | "sms"
    error: Optional[str] = None


# ═══════════════════════════════════════════════════
# 模板引擎（极简 Python f-string 风格）
# ═══════════════════════════════════════════════════

class NotificationTemplates:
    """通知模板集合。使用 {var} 占位。"""

    ORDER_CREATED_SUBJECT = "【智家管家AI】下单成功 - 订单号 {order_no}"

    ORDER_CREATED_BODY = """尊敬的 {customer_name}：

您的家政服务订单已创建成功！
订单编号：{order_no}
服务项目：{service_list}
预约时间：{scheduled_at}
服务地址：{address}
订单金额：¥{amount}

我们将尽快为您安排服务人员，请保持手机畅通。

如有疑问，请联系客服：{company_phone}

—— {company_name} · 智家管家AI"""

    STAFF_DISPATCHED_SUBJECT = "【智家管家AI】您有新的派单 - 订单号 {order_no}"

    STAFF_DISPATCHED_BODY = """{staff_name} 您好：

您有一个新的服务订单已派发给您！
客户：{customer_name}
服务项目：{service_list}
预约时间：{scheduled_at}
客户地址：{address}
客户电话：{customer_phone}

请按时到达并提供优质服务。服务完成后请在系统中确认。

—— {company_name} · 智家管家AI"""

    ORDER_COMPLETED_SUBJECT = "【智家管家AI】服务完成，请评价 - 订单号 {order_no}"

    ORDER_COMPLETED_BODY = """尊敬的 {customer_name}：

您的家政服务订单已标记完成！
订单编号：{order_no}
服务项目：{service_list}
完成时间：{completed_at}
实付金额：¥{amount}

如果满意我们的服务，请给个好评哦！
（评价功能即将上线，敬请期待）

—— {company_name} · 智家管家AI"""

    PAYMENT_SUCCESS_SUBJECT = "【智家管家AI】支付成功 - 订单号 {order_no}"

    PAYMENT_SUCCESS_BODY = """尊敬的 {customer_name}：

您的支付已成功！
订单编号：{order_no}
支付金额：¥{amount}
支付方式：{method_label}
支付时间：{paid_at}

我们将尽快为您安排服务。

—— {company_name} · 智家管家AI"""

    # ── 短信模板（简短，适合 70 字符限制）─────────────────

    SMS_ORDER_CREATED = "【{company_name}】{customer_name}您好，订单{order_no}已创建，{service_list}，预约{date}，客服{company_phone}"

    SMS_STAFF_DISPATCHED = "【{company_name}】{staff_name}您好，新订单{order_no}：{customer_name}，{service_list}，{date}，{address}，电话{customer_phone}"

    SMS_ORDER_COMPLETED = "【{company_name}】{customer_name}您好，订单{order_no}已完成，感谢您的信任！如有不满请联系{company_phone}"

    SMS_PAYMENT_SUCCESS = "【{company_name}】支付成功！订单{order_no}，金额¥{amount}，感谢您的付款。"

    @classmethod
    def render(cls, template: str, **kwargs) -> str:
        """简单模板渲染：{var} 替换"""
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value) if value is not None else "")
        return result

    # ── Builder 方法 ──

    @classmethod
    def order_created(cls, **kw) -> Notification:
        return Notification(
            subject=cls.render(cls.ORDER_CREATED_SUBJECT, **kw),
            body_text=cls.render(cls.ORDER_CREATED_BODY, **kw),
            template_id="order_created",
            template_params=kw,
        )

    @classmethod
    def staff_dispatched(cls, **kw) -> Notification:
        return Notification(
            subject=cls.render(cls.STAFF_DISPATCHED_SUBJECT, **kw),
            body_text=cls.render(cls.STAFF_DISPATCHED_BODY, **kw),
            template_id="staff_dispatched",
            template_params=kw,
        )

    @classmethod
    def order_completed(cls, **kw) -> Notification:
        return Notification(
            subject=cls.render(cls.ORDER_COMPLETED_SUBJECT, **kw),
            body_text=cls.render(cls.ORDER_COMPLETED_BODY, **kw),
            template_id="order_completed",
            template_params=kw,
        )

    @classmethod
    def payment_success(cls, **kw) -> Notification:
        return Notification(
            subject=cls.render(cls.PAYMENT_SUCCESS_SUBJECT, **kw),
            body_text=cls.render(cls.PAYMENT_SUCCESS_BODY, **kw),
            template_id="payment_success",
            template_params=kw,
        )


# ═══════════════════════════════════════════════════
# 抽象 Provider
# ═══════════════════════════════════════════════════

class EmailProvider(ABC):
    """邮件发送抽象"""

    @abstractmethod
    async def send(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> NotifyResult:
        ...


class SMSProvider(ABC):
    """短信发送抽象"""

    @abstractmethod
    async def send(self, phone: str, content: str, template_id: str = "", template_params: Dict[str, str] = None) -> NotifyResult:
        ...


# ═══════════════════════════════════════════════════
# SMTP 邮件实现
# ═══════════════════════════════════════════════════

class SMTPEmailProvider(EmailProvider):
    """
    标准 SMTP 邮件发送。

    所需配置项:
      - smtp_host         : SMTP 服务器地址
      - smtp_port         : 端口（465 for SSL, 587 for STARTTLS）
      - smtp_username     : 发件邮箱地址
      - smtp_password     : 邮箱密码/授权码
      - smtp_from_name    : 发件人显示名称
    """

    def __init__(self, config: Dict[str, str]):
        self.host = config.get("smtp_host", "")
        self.port = int(config.get("smtp_port", "465"))
        self.username = config.get("smtp_username", "")
        self.password = config.get("smtp_password", "")
        self.from_name = config.get("smtp_from_name", "智家管家AI")

    async def send(
        self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None
    ) -> NotifyResult:
        if not self.host or not self.username:
            return NotifyResult(success=False, channel="email", error="SMTP 未配置")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.username}>"
        msg["To"] = to_email
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            if self.port == 465:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=15)
                server.starttls()

            server.login(self.username, self.password)
            server.sendmail(self.username, to_email, msg.as_string())
            server.quit()
            return NotifyResult(success=True, channel="email")
        except Exception as e:
            return NotifyResult(success=False, channel="email", error=str(e))


# ═══════════════════════════════════════════════════
# 阿里云短信实现
# ═══════════════════════════════════════════════════

class AliyunSMSProvider(SMSProvider):
    """
    阿里云短信服务。

    所需配置项:
      - sms_provider       : "aliyun"
      - sms_access_key_id  : RAM AccessKey
      - sms_access_secret  : RAM AccessKey Secret
      - sms_sign_name      : 短信签名
      - sms_template_ids   : JSON string, e.g. '{"order_created":"SMS_xxx",...}'
    """

    ENDPOINT = "https://dysmsapi.aliyuncs.com"

    def __init__(self, config: Dict[str, str]):
        self.access_key = config.get("sms_access_key_id", "")
        self.access_secret = config.get("sms_access_secret", "")
        self.sign_name = config.get("sms_sign_name", "")
        self.template_ids = {}
        _tids = config.get("sms_template_ids", "{}")
        try:
            self.template_ids = json.loads(_tids)
        except json.JSONDecodeError:
            pass

    def _sign(self, params: Dict[str, str]) -> str:
        """阿里云签名（HMAC-SHA1 然后 Base64）"""
        sorted_params = sorted(params.items())
        qs = "&".join(
            f"{self._encode(k)}={self._encode(v)}"
            for k, v in sorted_params
        )
        string_to_sign = f"GET&{self._encode('/')}&{self._encode(qs)}"
        key = self.access_secret + "&"
        h = hmac.new(key.encode(), string_to_sign.encode(), hashlib.sha1)
        return base64.b64encode(h.digest()).decode()

    @staticmethod
    def _encode(s: str) -> str:
        return httpx.URL("https://a.com?" + s).raw_path.decode().lstrip("/")

    async def send(
        self, phone: str, content: str, template_id: str = "", template_params: Dict[str, str] = None
    ) -> NotifyResult:
        if not self.access_key:
            return NotifyResult(success=False, channel="sms", error="短信未配置")

        tpl_code = self.template_ids.get(template_id, template_id) if template_id else ""

        params = {
            "AccessKeyId": self.access_key,
            "Action": "SendSms",
            "Format": "JSON",
            "PhoneNumbers": phone,
            "SignName": self.sign_name,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid4()),
            "SignatureVersion": "1.0",
            "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Version": "2017-05-25",
        }

        if tpl_code:
            params["TemplateCode"] = tpl_code
            if template_params:
                params["TemplateParam"] = json.dumps(template_params, ensure_ascii=False)
        else:
            # 无模板 ID → 直接发内容
            pass

        params["Signature"] = self._sign(params)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.ENDPOINT, params=params)
            data = resp.json()
            if data.get("Code") == "OK":
                return NotifyResult(success=True, channel="sms")
            return NotifyResult(success=False, channel="sms", error=data.get("Message", str(data)))
        except Exception as e:
            return NotifyResult(success=False, channel="sms", error=str(e))


# ═══════════════════════════════════════════════════
# 通知引擎（统一的对外接口）
# ═══════════════════════════════════════════════════

@dataclass
class CompanyNotifyConfig:
    """从 company.settings 解析的通知配置"""
    company_name: str = "家政服务公司"
    company_phone: str = ""
    smtp_host: str = ""
    smtp_port: str = "465"
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_name: str = ""
    sms_provider: str = ""                   # "" | "aliyun"
    sms_access_key_id: str = ""
    sms_access_secret: str = ""
    sms_sign_name: str = ""
    sms_template_ids: str = "{}"


class NotificationEngine:
    """
    通知引擎：管理邮件和短信的并发发送

    用法：
        from app.services.notification_service import get_notification_engine
        engine = await get_notification_engine(company_id, db)
        results = await engine.notify_customer(order, "order_created")
    """

    def __init__(self, config: CompanyNotifyConfig):
        self.config = config
        self._email: Optional[EmailProvider] = None
        self._sms: Optional[SMSProvider] = None

    @property
    def email(self) -> Optional[EmailProvider]:
        if self._email is None and self.config.smtp_host:
            self._email = SMTPEmailProvider({
                "smtp_host": self.config.smtp_host,
                "smtp_port": self.config.smtp_port,
                "smtp_username": self.config.smtp_username,
                "smtp_password": self.config.smtp_password,
                "smtp_from_name": self.config.smtp_from_name or self.config.company_name,
            })
        return self._email

    @property
    def sms(self) -> Optional[SMSProvider]:
        if self._sms is None and self.config.sms_access_key_id:
            if self.config.sms_provider == "aliyun":
                self._sms = AliyunSMSProvider({
                    "sms_access_key_id": self.config.sms_access_key_id,
                    "sms_access_secret": self.config.sms_access_secret,
                    "sms_sign_name": self.config.sms_sign_name,
                    "sms_template_ids": self.config.sms_template_ids,
                })
        return self._sms

    def _base_template_vars(self, **overrides) -> Dict[str, str]:
        return {
            "company_name": self.config.company_name,
            "company_phone": self.config.company_phone,
            **overrides,
        }

    # ── 发送方法 ────────────────────────────────

    async def notify_customer_order_created(
        self,
        customer_email: Optional[str],
        customer_phone: Optional[str],
        customer_name: str,
        order_no: str,
        service_list: str,
        scheduled_at: str,
        address: str,
        amount: str,
    ) -> List[NotifyResult]:
        """客户下单成功通知"""
        vars_ = self._base_template_vars(
            customer_name=customer_name,
            order_no=order_no,
            service_list=service_list,
            scheduled_at=scheduled_at,
            address=address,
            amount=amount,
        )
        notif = NotificationTemplates.order_created(**vars_)
        return await self._send(customer_email, customer_phone, notif)

    async def notify_staff_dispatched(
        self,
        staff_email: Optional[str],
        staff_phone: Optional[str],
        staff_name: str,
        customer_name: str,
        customer_phone: str,
        order_no: str,
        service_list: str,
        scheduled_at: str,
        address: str,
    ) -> List[NotifyResult]:
        """员工派单通知"""
        vars_ = self._base_template_vars(
            staff_name=staff_name,
            customer_name=customer_name,
            customer_phone=customer_phone,
            order_no=order_no,
            service_list=service_list,
            scheduled_at=scheduled_at,
            address=address,
        )
        notif = NotificationTemplates.staff_dispatched(**vars_)
        return await self._send(staff_email, staff_phone, notif)

    async def notify_order_completed(
        self,
        customer_email: Optional[str],
        customer_phone: Optional[str],
        customer_name: str,
        order_no: str,
        service_list: str,
        completed_at: str,
        amount: str,
    ) -> List[NotifyResult]:
        """服务完成通知"""
        vars_ = self._base_template_vars(
            customer_name=customer_name,
            order_no=order_no,
            service_list=service_list,
            completed_at=completed_at,
            amount=amount,
        )
        notif = NotificationTemplates.order_completed(**vars_)
        return await self._send(customer_email, customer_phone, notif)

    async def notify_payment_success(
        self,
        customer_email: Optional[str],
        customer_phone: Optional[str],
        customer_name: str,
        order_no: str,
        amount: str,
        method_label: str,
        paid_at: str,
    ) -> List[NotifyResult]:
        """支付成功通知"""
        vars_ = self._base_template_vars(
            customer_name=customer_name,
            order_no=order_no,
            amount=amount,
            method_label=method_label,
            paid_at=paid_at,
        )
        notif = NotificationTemplates.payment_success(**vars_)
        return await self._send(customer_email, customer_phone, notif)

    # ── 内部发送 ────────────────────────────────

    async def _send(
        self,
        email_to: Optional[str],
        phone_to: Optional[str],
        notif: Notification,
    ) -> List[NotifyResult]:
        """并发发送邮件 + 短信，返回所有结果"""
        import asyncio as _asyncio

        tasks = []

        async def _send_email():
            if email_to and self.email:
                return await self.email.send(
                    email_to, notif.subject, notif.body_text, notif.body_html
                )
            return NotifyResult(success=False, channel="email", error="无邮箱或未配置")

        async def _send_sms():
            if phone_to and self.sms:
                # 生成短文案
                sms_text = self._render_sms(notif)
                return await self.sms.send(
                    phone_to, sms_text,
                    template_id=notif.template_id,
                    template_params=notif.template_params,
                )
            return NotifyResult(success=False, channel="sms", error="无手机号或未配置")

        if email_to and self.email:
            tasks.append(_send_email())
        if phone_to and self.sms:
            tasks.append(_send_sms())

        if not tasks:
            return []

        results = await _asyncio.gather(*tasks, return_exceptions=True)
        return [
            NotifyResult(success=False, channel="unknown", error=str(r))
            if isinstance(r, Exception) else r
            for r in results
        ]

    @staticmethod
    def _render_sms(notif: Notification) -> str:
        """从模板参数生成短信文本"""
        tmpl_map = {
            "order_created": NotificationTemplates.SMS_ORDER_CREATED,
            "staff_dispatched": NotificationTemplates.SMS_STAFF_DISPATCHED,
            "order_completed": NotificationTemplates.SMS_ORDER_COMPLETED,
            "payment_success": NotificationTemplates.SMS_PAYMENT_SUCCESS,
        }
        template = tmpl_map.get(notif.template_id, "")
        if not template:
            return notif.subject  # fallback
        # 计算 date 快捷字段
        params = dict(notif.template_params)
        if "scheduled_at" in params and "date" not in params:
            params["date"] = params["scheduled_at"][:16] if params["scheduled_at"] else ""
        if "completed_at" in params and "date" not in params:
            params["date"] = params["completed_at"][:16] if params["completed_at"] else ""
        if "paid_at" in params and "date" not in params:
            params["date"] = params["paid_at"][:16] if params["paid_at"] else ""
        return NotificationTemplates.render(template, **params)


# ═══════════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════════

def _parse_config(company: Company) -> CompanyNotifyConfig:
    """从 company.settings 解析通知配置"""
    settings = dict(company.settings or {})
    api_keys = dict(settings.get("api_keys", {}))
    return CompanyNotifyConfig(
        company_name=company.name,
        company_phone=settings.get("phone", ""),
        smtp_host=api_keys.get("smtp_host", ""),
        smtp_port=api_keys.get("smtp_port", "465"),
        smtp_username=api_keys.get("smtp_username", ""),
        smtp_password=api_keys.get("smtp_password", ""),
        smtp_from_name=api_keys.get("smtp_from_name", ""),
        sms_provider=api_keys.get("sms_provider", ""),
        sms_access_key_id=api_keys.get("sms_access_key_id", ""),
        sms_access_secret=api_keys.get("sms_access_secret", ""),
        sms_sign_name=api_keys.get("sms_sign_name", ""),
        sms_template_ids=api_keys.get("sms_template_ids", "{}"),
    )


async def get_notification_engine(
    company_id: str,
    db: AsyncSession,
) -> Optional[NotificationEngine]:
    """根据 company_id 获取通知引擎。未配置则返回 None。"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        return None
    config = _parse_config(company)
    if not config.smtp_host and not config.sms_access_key_id:
        return None  # 完全未配置
    return NotificationEngine(config)
