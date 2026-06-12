"""支付 API 测试"""
import pytest


@pytest.mark.asyncio
async def test_create_payment_order_not_found(client, auth_headers):
    """支付创建 — 订单不存在"""
    resp = await client.post(
        "/api/v1/payments/create",
        json={"order_id": "00000000-0000-0000-0000-000000000000", "method": "wechat", "pay_type": "native"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert "订单不存在" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_payment_missing_config(client, auth_headers):
    """支付创建 — 公司未配置支付密钥"""
    cust_resp = await client.post(
        "/api/v1/customers",
        json={"name": "支付测试客户", "phone": "13000000000"},
        headers=auth_headers,
    )
    d = cust_resp.json()
    customer_id = d["data"]["id"] if "data" in d else d.get("id")

    order_resp = await client.post(
        "/api/v1/orders",
        json={
            "customer_id": customer_id,
            "total_amount": 99.00,
            "address": "测试地址",
            "items": [],
        },
        headers=auth_headers,
    )
    od = order_resp.json()
    order_id = od["order_id"] if "order_id" in od else od.get("data", {}).get("order_id")

    resp = await client.post(
        "/api/v1/payments/create",
        json={"order_id": order_id, "method": "wechat", "pay_type": "native"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "未配置" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_payment_not_found(client, auth_headers):
    """查询支付 — 记录不存在"""
    resp = await client.get(
        "/api/v1/payments/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_refund_not_paid(client, auth_headers):
    """退款 — 无支付记录的订单退款失败"""
    cust_resp = await client.post(
        "/api/v1/customers",
        json={"name": "退款测试", "phone": "13100000000"},
        headers=auth_headers,
    )
    d = cust_resp.json()
    cid = d["data"]["id"] if "data" in d else d.get("id")

    order_resp = await client.post(
        "/api/v1/orders",
        json={"customer_id": cid, "total_amount": 50, "address": "x", "items": []},
        headers=auth_headers,
    )
    od = order_resp.json()
    oid = od["order_id"] if "order_id" in od else od.get("data", {}).get("order_id")

    resp = await client.post(
        f"/api/v1/payments/{oid}/refund",
        json={"reason": "测试"},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 404)
