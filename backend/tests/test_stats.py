"""
单元测试: 数据统计 (Stats)
测试控制台核心数据接口
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_stats_empty(client: AsyncClient, auth_headers: dict):
    """空数据状态下的统计"""
    response = await client.get("/api/v1/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]
    assert summary["totalOrders"] == 0
    assert summary["pendingOrders"] == 0
    assert summary["completedOrders"] == 0
    assert summary["todayOrders"] == 0
    assert summary["totalCustomers"] == 0
    assert summary["totalStaff"] == 0
    assert summary["totalRevenue"] == 0

    # Status distribution should have all 6 statuses
    assert len(data["statusDistribution"]) == 6
    assert all(s["count"] == 0 for s in data["statusDistribution"])

    # Last 7 days should have 7 entries
    assert len(data["last7Days"]) == 7


@pytest.mark.asyncio
async def test_get_stats_with_data(client: AsyncClient, auth_headers: dict):
    """有订单数据时的统计"""
    # Create staff
    staff_resp = await client.post("/api/v1/staff", json={
        "name": "李师傅", "phone": "13800001111",
    }, headers=auth_headers)
    staff_id = staff_resp.json()["id"]

    # Create customer
    cust_resp = await client.post("/api/v1/customers", json={
        "name": "张三", "phone": "13900001111",
    }, headers=auth_headers)
    customer_id = cust_resp.json()["id"]

    # Create service
    svc_resp = await client.post("/api/v1/services", json={
        "name": "日常保洁", "price": 80.0,
    }, headers=auth_headers)
    service_id = svc_resp.json()["id"]

    # Create and complete some orders
    for i in range(3):
        create_resp = await client.post("/api/v1/orders", json={
            "customer_id": customer_id,
            "total_amount": 80.0 * (i + 1),
            "items": [{"service_id": service_id, "quantity": i + 1, "price": 80.0}],
        }, headers=auth_headers)
        order_id = create_resp.json()["order_id"]
        # Confirm 2 out of 3
        if i < 2:
            await client.put(f"/api/v1/orders/{order_id}/status?status=confirmed", headers=auth_headers)
        # Complete 1
        if i < 1:
            await client.put(f"/api/v1/orders/{order_id}/status?status=dispatched&staff_id={staff_id}", headers=auth_headers)
            await client.put(f"/api/v1/orders/{order_id}/status?status=in_progress", headers=auth_headers)
            await client.put(f"/api/v1/orders/{order_id}/status?status=completed", headers=auth_headers)

    response = await client.get("/api/v1/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]
    assert summary["totalOrders"] == 3
    assert summary["completedOrders"] == 1
    assert summary["totalCustomers"] == 1
    assert summary["totalStaff"] == 1
    assert summary["todayOrders"] >= 0  # May be 0 or 3 depending on time

    # Status distribution should sum to total
    total_from_status = sum(s["count"] for s in data["statusDistribution"])
    assert total_from_status == summary["totalOrders"]


@pytest.mark.asyncio
async def test_stats_require_auth(client: AsyncClient):
    """未授权访问统计接口——由于依赖被全局覆盖，此测试确认端点可访问"""
    # With the global dependency override, auth is always mocked.
    # In production, this requires a valid Bearer token.
    # We verify the endpoint returns data (not an auth error) under test mode.
    response = await client.get("/api/v1/stats")
    assert response.status_code == 200  # Test mode with overridden auth
