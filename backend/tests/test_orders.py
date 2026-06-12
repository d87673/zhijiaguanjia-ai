"""
单元测试: 订单管理 (Orders)
测试订单创建、状态流转、筛选、派单
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def setup_order_deps(client, auth_headers):
    """Create prerequisite entities for order testing."""

    # Create customer
    cust_resp = await client.post("/api/v1/customers", json={
        "name": "测试客户", "phone": "13900001111",
    }, headers=auth_headers)
    customer_id = cust_resp.json()["id"]

    # Create service
    svc_resp = await client.post("/api/v1/services", json={
        "name": "日常保洁", "price": 60.0, "duration": 120,
    }, headers=auth_headers)
    service_id = svc_resp.json()["id"]

    # Create staff
    staff_resp = await client.post("/api/v1/staff", json={
        "name": "王师傅", "phone": "13800000000",
    }, headers=auth_headers)
    staff_id = staff_resp.json()["id"]

    return customer_id, service_id, staff_id


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, auth_headers: dict, setup_order_deps):
    """创建新订单"""
    customer_id, service_id, _staff_id = setup_order_deps

    response = await client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "status": "pending",
        "total_amount": 60.0,
        "scheduled_at": "2026-06-15T09:00:00",
        "address": "北京市朝阳区测试小区1号楼",
        "notes": "有宠物，注意关门",
        "items": [
            {"service_id": service_id, "quantity": 1, "price": 60.0},
        ],
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "订单创建成功"
    assert data["order_id"]


@pytest.mark.asyncio
async def test_create_order_invalid_customer(client: AsyncClient, auth_headers: dict):
    """创建订单时使用不存在的客户应返回 404"""
    response = await client.post("/api/v1/orders", json={
        "customer_id": "nonexistent-customer-id",
        "total_amount": 100.0,
        "items": [],
    }, headers=auth_headers)
    assert response.status_code == 404
    assert "客户不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient, auth_headers: dict, setup_order_deps):
    """获取订单列表"""
    customer_id, service_id, _staff_id = setup_order_deps

    # Create 3 orders
    for i in range(3):
        await client.post("/api/v1/orders", json={
            "customer_id": customer_id,
            "total_amount": 60.0,
            "items": [{"service_id": service_id, "quantity": 1, "price": 60.0}],
        }, headers=auth_headers)

    response = await client.get("/api/v1/orders", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["orders"]) == 3


@pytest.mark.asyncio
async def test_filter_orders_by_status(client: AsyncClient, auth_headers: dict, setup_order_deps):
    """按状态筛选订单"""
    customer_id, service_id, _staff_id = setup_order_deps

    # Create 2 pending orders
    for _ in range(2):
        await client.post("/api/v1/orders", json={
            "customer_id": customer_id,
            "status": "pending",
            "total_amount": 60.0,
            "items": [{"service_id": service_id, "quantity": 1, "price": 60.0}],
        }, headers=auth_headers)

    # Create 1 confirmed order (via status update)
    create_resp = await client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "status": "pending",
        "total_amount": 100.0,
        "items": [{"service_id": service_id, "quantity": 1, "price": 100.0}],
    }, headers=auth_headers)
    order_id = create_resp.json()["order_id"]
    await client.put(f"/api/v1/orders/{order_id}/status?status=confirmed", headers=auth_headers)

    response = await client.get("/api/v1/orders?status=pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(o["status"] == "pending" for o in data["orders"])


@pytest.mark.asyncio
async def test_update_order_status_flow(client: AsyncClient, auth_headers: dict, setup_order_deps):
    """测试完整订单状态流转: pending → confirmed → dispatched → in_progress → completed"""
    customer_id, service_id, staff_id = setup_order_deps

    # Create order
    create_resp = await client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "status": "pending",
        "total_amount": 60.0,
        "items": [{"service_id": service_id, "quantity": 1, "price": 60.0}],
    }, headers=auth_headers)
    order_id = create_resp.json()["order_id"]

    # pending → confirmed
    resp1 = await client.put(f"/api/v1/orders/{order_id}/status?status=confirmed", headers=auth_headers)
    assert resp1.status_code == 200

    # confirmed → dispatched (with staff assignment)
    resp2 = await client.put(
        f"/api/v1/orders/{order_id}/status?status=dispatched&staff_id={staff_id}",
        headers=auth_headers,
    )
    assert resp2.status_code == 200

    # dispatched → in_progress
    resp3 = await client.put(f"/api/v1/orders/{order_id}/status?status=in_progress", headers=auth_headers)
    assert resp3.status_code == 200

    # in_progress → completed
    resp4 = await client.put(f"/api/v1/orders/{order_id}/status?status=completed", headers=auth_headers)
    assert resp4.status_code == 200


@pytest.mark.asyncio
async def test_cancel_order_from_pending(client: AsyncClient, auth_headers: dict, setup_order_deps):
    """从 pending 状态取消订单"""
    customer_id, service_id, _staff_id = setup_order_deps

    create_resp = await client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "status": "pending",
        "total_amount": 60.0,
        "items": [{"service_id": service_id, "quantity": 1, "price": 60.0}],
    }, headers=auth_headers)
    order_id = create_resp.json()["order_id"]

    response = await client.put(f"/api/v1/orders/{order_id}/status?status=cancelled", headers=auth_headers)
    assert response.status_code == 200
    assert "已更新为 cancelled" in response.json()["message"]


@pytest.mark.asyncio
async def test_update_order_invalid_status(client: AsyncClient, auth_headers: dict, setup_order_deps):
    """使用无效状态更新订单应返回 400"""
    customer_id, service_id, _staff_id = setup_order_deps

    create_resp = await client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "total_amount": 60.0,
        "items": [{"service_id": service_id, "quantity": 1, "price": 60.0}],
    }, headers=auth_headers)
    order_id = create_resp.json()["order_id"]

    response = await client.put(f"/api/v1/orders/{order_id}/status?status=invalid_status", headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_nonexistent_order(client: AsyncClient, auth_headers: dict):
    """更新不存在的订单应返回 404"""
    response = await client.put("/api/v1/orders/fake-order-id/status?status=confirmed", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_order_unauthenticated(client: AsyncClient):
    """测试环境认证覆盖下，创建订单可访问"""
    response = await client.post("/api/v1/orders", json={
        "customer_id": "test-id",
        "total_amount": 100.0,
        "items": [],
    })
    # With override: 404 (customer not found), without: 401/403
    assert response.status_code in (404, 401, 403)


@pytest.mark.asyncio
async def test_order_contains_customer_name(client: AsyncClient, auth_headers: dict, setup_order_deps):
    """订单列表应包含客户名称（通过 join 加载）"""
    customer_id, service_id, _staff_id = setup_order_deps

    # Create order
    await client.post("/api/v1/orders", json={
        "customer_id": customer_id,
        "total_amount": 60.0,
        "items": [{"service_id": service_id, "quantity": 1, "price": 60.0}],
    }, headers=auth_headers)

    response = await client.get("/api/v1/orders", headers=auth_headers)
    orders = response.json()["orders"]
    assert orders[0]["customer_name"] == "测试客户"
    assert orders[0]["status"] == "pending"
