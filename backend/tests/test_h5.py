"""客户自助 H5 API 测试"""
import hashlib
import hmac
import pytest
from app.core.config import get_settings


def _token(customer_id: str) -> str:
    secret = get_settings().JWT_SECRET_KEY
    return hmac.new(secret.encode(), customer_id.encode(), hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_h5_services_list(client, auth_headers, db_session):
    """H5 获取服务列表 — 需要 customer token"""
    from app.models.models import Customer, Service

    cust = Customer(
        id="b0000000-0000-0000-0000-000000000001",
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="H5测试客户",
        phone="13900000111",
    )
    svc = Service(
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="保洁服务",
        price=100,
        category="cleaning",
        is_active=True,
    )
    db_session.add_all([cust, svc])
    await db_session.commit()

    token = _token("b0000000-0000-0000-0000-000000000001")
    cid = "b0000000-0000-0000-0000-000000000001"
    resp = await client.get(
        f"/api/v1/h5/{cid}/services",
        headers={"X-Customer-Token": token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]
    items = data["data"]["items"]
    assert any(s["name"] == "保洁服务" for s in items)


@pytest.mark.asyncio
async def test_h5_services_bad_token(client):
    """H5 错误 token → 401"""
    cid = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(
        f"/api/v1/h5/{cid}/services",
        headers={"X-Customer-Token": "bad-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_h5_create_order(client, db_session):
    """H5 客户下单"""
    from app.models.models import Customer, Service

    cid = "b0000000-0000-0000-0000-000000000002"
    cust = Customer(
        id=cid,
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="下单客户",
        phone="13900000222",
    )
    svc = Service(
        id="a0000000-0000-0000-0000-000000000010",
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="维修服务",
        price=150,
        is_active=True,
    )
    db_session.add_all([cust, svc])
    await db_session.commit()

    token = _token(cid)
    resp = await client.post(
        f"/api/v1/h5/{cid}/orders",
        json={
            "address": "测试小区3栋501",
            "items": [{"service_id": "a0000000-0000-0000-0000-000000000010", "quantity": 1, "price": 150}],
        },
        headers={"X-Customer-Token": token},
    )
    assert resp.status_code == 201
    d = resp.json()
    assert d["success"] and d["data"]["order_id"]


@pytest.mark.asyncio
async def test_h5_create_order_empty_items(client, db_session):
    """H5 下单 — 空服务列表应报错"""
    from app.models.models import Customer

    cid = "b0000000-0000-0000-0000-000000000003"
    cust = Customer(
        id=cid,
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="空客户",
        phone="13900000333",
    )
    db_session.add(cust)
    await db_session.commit()

    token = _token(cid)
    resp = await client.post(
        f"/api/v1/h5/{cid}/orders",
        json={"address": "x", "items": []},
        headers={"X-Customer-Token": token},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_h5_list_my_orders(client, db_session):
    """H5 查看我的订单"""
    from app.models.models import Customer

    cid = "b0000000-0000-0000-0000-000000000004"
    cust = Customer(
        id=cid,
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="查单客户",
        phone="13900000444",
    )
    db_session.add(cust)
    await db_session.commit()

    token = _token(cid)
    resp = await client.get(
        f"/api/v1/h5/{cid}/orders",
        headers={"X-Customer-Token": token},
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["success"]
    assert "items" in d["data"]


@pytest.mark.asyncio
async def test_h5_get_company(client, db_session):
    """H5 获取公司信息"""
    from app.models.models import Customer

    cid = "b0000000-0000-0000-0000-000000000005"
    cust = Customer(
        id=cid,
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="客户5",
    )
    db_session.add(cust)
    await db_session.commit()

    token = _token(cid)
    resp = await client.get(
        f"/api/v1/h5/{cid}/company",
        headers={"X-Customer-Token": token},
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["data"]["customer_name"] == "客户5"


@pytest.mark.asyncio
async def test_h5_review_not_completed(client, db_session):
    """H5 评价未完成订单 → 应报错"""
    from app.models.models import Customer, Order

    cid = "b0000000-0000-0000-0000-000000000006"
    oid = "e0000000-0000-0000-0000-000000000001"
    cust = Customer(
        id=cid,
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="评价客户",
    )
    order = Order(
        id=oid,
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        customer_id=cid,
        status="pending",
        total_amount=50,
    )
    db_session.add_all([cust, order])
    await db_session.commit()

    token = _token(cid)
    resp = await client.post(
        f"/api/v1/h5/{cid}/orders/{oid}/review",
        json={"rating": 5, "comment": "好"},
        headers={"X-Customer-Token": token},
    )
    assert resp.status_code == 400
    assert "完成" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_h5_wrong_customer_order(client, db_session):
    """H5 客户A不能访问客户B的订单"""
    from app.models.models import Customer

    cid = "b0000000-0000-0000-0000-000000000007"
    cust = Customer(
        id=cid,
        company_id="c0d1e2f3-a4b5-6789-abcd-ef1234567890",
        name="客户A",
    )
    db_session.add(cust)
    await db_session.commit()

    token = _token(cid)
    resp = await client.get(
        f"/api/v1/h5/{cid}/orders/00000000-0000-0000-0000-000000000099",
        headers={"X-Customer-Token": token},
    )
    assert resp.status_code == 404
