import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Numeric, ForeignKey, JSON, Text, ARRAY, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


def utcnow():
    """返回当前 UTC 时间，替代已弃用的 utcnow()"""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(DateTime(timezone=True), nullable=True)
    image = Column(String(500), nullable=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), default="admin")  # admin, manager, staff
    phone = Column(String(20), nullable=True)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company = relationship("Company", back_populates="users")
    created_orders = relationship("Order", back_populates="creator", foreign_keys="Order.created_by_id")
    assigned_orders = relationship("Order", back_populates="assignee", foreign_keys="Order.assigned_to_id")


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    plan = Column(String(20), default="free")  # free, pro, enterprise
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    users = relationship("User", back_populates="company")
    services = relationship("Service", back_populates="company", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="company", cascade="all, delete-orphan")
    staff = relationship("Staff", back_populates="company", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), default=0)
    duration = Column(Integer, default=60)  # minutes
    category = Column(String(50), nullable=True, index=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company = relationship("Company", back_populates="services")
    order_items = relationship("OrderItem", back_populates="service")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company = relationship("Company", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer_ref")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    skills = Column(ARRAY(String), default=list)
    is_active = Column(Boolean, default=True)
    current_load = Column(Integer, default=0)
    rating = Column(Float, default=5.0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company = relationship("Company", back_populates="staff")
    orders = relationship("Order", back_populates="assigned_staff")


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=False), ForeignKey("staff.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    assigned_to_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="pending", index=True)
    # pending, confirmed, dispatched, in_progress, completed, cancelled
    total_amount = Column(Numeric(10, 2), default=0)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    customer = relationship("Customer", back_populates="orders")
    assigned_staff = relationship("Staff", back_populates="orders")
    creator = relationship("User", back_populates="created_orders", foreign_keys=[created_by_id])
    assignee = relationship("User", back_populates="assigned_orders", foreign_keys=[assigned_to_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    order_id = Column(UUID(as_uuid=False), ForeignKey("orders.id"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=False), ForeignKey("services.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Numeric(10, 2), default=0)

    order = relationship("Order", back_populates="items")
    service = relationship("Service", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    order_id = Column(UUID(as_uuid=False), ForeignKey("orders.id"), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), default=0)
    method = Column(String(20), default="wechat")  # wechat, alipay, cash, card
    status = Column(String(20), default="pending", index=True)  # pending, paid, refunded, failed
    transaction_id = Column(String(100), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    order = relationship("Order", back_populates="payment")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    source = Column(String(20), default="web")  # web, wechat, phone
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    customer_ref = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    conversation_id = Column(UUID(as_uuid=False), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")
