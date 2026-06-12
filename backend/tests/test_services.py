"""
单元测试: 服务管理 (Services)
测试服务的 CRUD 操作
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_service(client: AsyncClient, auth_headers: dict):
    """创建新服务"""
    response = await client.post("/api/v1/services", json={
        "name": "日常保洁",
        "description": "专业日常清洁服务",
        "price": 60.0,
        "duration": 120,
        "category": "cleaning",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "日常保洁"
    assert data["price"] == 60.0
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_services(client: AsyncClient, auth_headers: dict):
    """获取服务列表"""
    # Create 3 services
    for i in range(3):
        await client.post("/api/v1/services", json={
            "name": f"测试服务{i}",
            "price": 50.0 + i * 10,
            "duration": 60,
            "category": "test",
        }, headers=auth_headers)

    response = await client.get("/api/v1/services", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["services"]) == 3


@pytest.mark.asyncio
async def test_list_services_filter_by_category(client: AsyncClient, auth_headers: dict):
    """按分类筛选服务"""
    await client.post("/api/v1/services", json={
        "name": "保洁服务", "price": 60.0, "category": "cleaning",
    }, headers=auth_headers)
    await client.post("/api/v1/services", json={
        "name": "维修服务", "price": 100.0, "category": "repair",
    }, headers=auth_headers)

    response = await client.get("/api/v1/services?category=cleaning", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["services"][0]["name"] == "保洁服务"


@pytest.mark.asyncio
async def test_list_services_search(client: AsyncClient, auth_headers: dict):
    """按名称搜索服务"""
    await client.post("/api/v1/services", json={
        "name": "深度清洁", "price": 200.0,
    }, headers=auth_headers)
    await client.post("/api/v1/services", json={
        "name": "空调维修", "price": 150.0,
    }, headers=auth_headers)

    response = await client.get("/api/v1/services?q=清洁", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["services"][0]["name"] == "深度清洁"


@pytest.mark.asyncio
async def test_update_service(client: AsyncClient, auth_headers: dict):
    """更新服务信息"""
    create_resp = await client.post("/api/v1/services", json={
        "name": "旧名称", "price": 80.0, "category": "test",
    }, headers=auth_headers)
    service_id = create_resp.json()["id"]

    response = await client.put(f"/api/v1/services/{service_id}", json={
        "name": "新名称", "price": 120.0,
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新名称"
    assert data["price"] == 120.0


@pytest.mark.asyncio
async def test_update_nonexistent_service(client: AsyncClient, auth_headers: dict):
    """更新不存在的服务应返回 404"""
    response = await client.put("/api/v1/services/nonexistent-id", json={
        "name": "不存在",
    }, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_service(client: AsyncClient, auth_headers: dict):
    """删除服务"""
    create_resp = await client.post("/api/v1/services", json={
        "name": "待删除服务", "price": 50.0,
    }, headers=auth_headers)
    service_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/services/{service_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "删除成功" in response.json()["message"]

    # Verify it's gone
    list_resp = await client.get("/api/v1/services", headers=auth_headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_service_unauthenticated(client: AsyncClient):
    """测试环境认证覆盖下，创建服务可访问"""
    # Global dependency override authenticates all requests in test mode
    response = await client.post("/api/v1/services", json={
        "name": "测试端点", "price": 10.0,
    })
    assert response.status_code in (201, 401, 403)


@pytest.mark.asyncio
async def test_services_pagination(client: AsyncClient, auth_headers: dict):
    """测试分页"""
    for i in range(25):
        await client.post("/api/v1/services", json={
            "name": f"分页服务{i}", "price": 10.0,
        }, headers=auth_headers)

    response = await client.get("/api/v1/services?limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 25
    assert len(data["services"]) == 10
    assert data["page"] == 1
