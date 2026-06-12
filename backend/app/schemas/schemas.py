from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ─── User ───
class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: Optional[str]
    email: str
    role: str
    phone: Optional[str]
    company_id: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class OrderStatusUpdateRequest(BaseModel):
    status: str
    staff_id: Optional[str] = None


# ─── Company ───
class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class CompanyKeysUpdateRequest(BaseModel):
    deepseek_key: Optional[str] = None
    doubao_key: Optional[str] = None
    wechat_mch_id: Optional[str] = None
    wechat_appid: Optional[str] = None
    wechat_api_v3_key: Optional[str] = None
    wechat_cert_serial: Optional[str] = None
    wechat_private_key: Optional[str] = None
    alipay_app_id: Optional[str] = None
    alipay_private_key: Optional[str] = None
    alipay_public_key: Optional[str] = None
    payment_notify_host: Optional[str] = None


# ─── Company ───
class CompanyResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    settings: dict
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Service ───
class ServiceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    price: float = Field(ge=0, default=0)
    duration: int = Field(ge=0, default=60)
    category: Optional[str] = None
    image_url: Optional[str] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: Optional[str]
    price: float
    duration: int
    category: Optional[str]
    image_url: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Customer ───
class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=100)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []


class CustomerResponse(BaseModel):
    id: str
    company_id: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    tags: List[str]
    order_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Staff ───
class StaffCreate(BaseModel):
    name: str = Field(..., max_length=100)
    phone: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = []


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[List[str]] = None
    is_active: Optional[bool] = None


class StaffResponse(BaseModel):
    id: str
    company_id: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    skills: List[str]
    is_active: bool
    rating: float
    current_load: int
    order_count: int = 0

    model_config = {"from_attributes": True}


# ─── Order ───
class OrderItemCreate(BaseModel):
    service_id: str
    quantity: int = Field(ge=1, default=1)
    price: float = Field(ge=0, default=0)


class OrderCreate(BaseModel):
    customer_id: str
    staff_id: Optional[str] = None
    status: str = "pending"
    total_amount: float = Field(ge=0, default=0)
    scheduled_at: Optional[datetime] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate] = []


class OrderResponse(BaseModel):
    id: str
    company_id: str
    customer_id: str
    customer_name: Optional[str] = None
    staff_id: Optional[str] = None
    staff_name: Optional[str] = None
    status: str
    total_amount: float
    scheduled_at: Optional[datetime]
    address: Optional[str]
    notes: Optional[str]
    items: list = []
    payment: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── AI ───
# ─── Payment ───
class PaymentCreateRequest(BaseModel):
    order_id: str
    method: str = "wechat"  # wechat | alipay
    pay_type: str = "native"  # native | jsapi | h5 | qr | page
    openid: Optional[str] = None  # JSAPI 时必填


class PaymentRefundRequest(BaseModel):
    amount: float = Field(ge=0, default=0)  # 0 = 全额退款
    reason: str = ""


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: float
    method: str
    status: str
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    action: str = "chat"  # chat, dispatch, copywriter
    messages: List[dict]
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str


# ─── Stats ───
class StatsResponse(BaseModel):
    summary: dict
    status_distribution: List[dict]
    last_7_days: List[dict]
    recent_orders: List[dict]


# ─── H5 (客户自助端) ───
class H5OrderItemCreate(BaseModel):
    service_id: str
    quantity: int = Field(ge=1, default=1)
    price: float = Field(ge=0, default=0)


class H5OrderCreate(BaseModel):
    scheduled_at: Optional[datetime] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    items: List[H5OrderItemCreate] = []


class H5ReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class H5OrderResponse(BaseModel):
    id: str
    status: str
    total_amount: float
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    staff_name: Optional[str] = None
    staff_phone: Optional[str] = None
    items: list = []
    payment: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Pagination ───
class PaginatedResponse(BaseModel):
    success: bool = True
    data: dict
