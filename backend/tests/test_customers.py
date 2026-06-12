"""
单元测试: 客户管理 (Customers)
测试客户 CRUD 和标签管理
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_customer(client: AsyncClient, auth_headers: dict):
    """创建新客户"""
    response = await client.post("/api/v1/customers", json={
        "name": "张先生",
        "phone": "13800138000",
        "email": "zhang@example.com",
        "address": "北京市朝阳区XX小区3号楼",
        "notes": "喜欢下午服务",
        "tags": ["vip", "长期"],
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "张先生"
    assert data["phone"] == "13800138000"
    assert "vip" in data["tags"]
    assert "长期" in data["tags"]


@pytest.mark.asyncio
async def test_list_customers(client: AsyncClient, auth_headers: dict):
    """获取客户列表"""
    for name in ["客户A", "客户B", "客户C"]:
        await client.post("/api/v1/customers", json={
            "name": name, "phone": "13800000000",
        }, headers=auth_headers)

    response = await client.get("/api/v1/customers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["items"]) == 3


@pytest.mark.asyncio
async def test_search_customers_by_name(client: AsyncClient, auth_headers: dict):
    """按名称搜索客户"""
    await client.post("/api/v1/customers", json={
        "name": "王小明", "phone": "13811111111",
    }, headers=auth_headers)
    await client.post("/api/v1/customers", json={
        "name": "李小华", "phone": "13822222222",
    }, headers=auth_headers)

    response = await client.get("/api/v1/customers?q=王", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["name"] == "王小明"


@pytest.mark.asyncio
async def test_search_customers_by_phone(client: AsyncClient, auth_headers: dict):
    """按电话搜索客户"""
    await client.post("/api/v1/customers", json={
        "name": "张三", "phone": "13900001111",
    }, headers=auth_headers)
    await client.post("/api/v1/customers", json={
        "name": "李四", "phone": "13900002222",
    }, headers=auth_headers)

    response = await client.get("/api/v1/customers?q=1111", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["name"] == "张三"


@pytest.mark.asyncio
async def test_update_customer(client: AsyncClient, auth_headers: dict):
    """更新客户信息"""
    create_resp = await client.post("/api/v1/customers", json={
        "name": "旧姓名", "phone": "13800000000",
    }, headers=auth_headers)
    customer_id = create_resp.json()["id"]

    response = await client.put(f"/api/v1/customers/{customer_id}", json={
        "name": "新姓名", "phone": "13900000000", "tags": ["vip"],
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新姓名"
    assert data["phone"] == "13900000000"
    assert "vip" in data["tags"]


@pytest.mark.asyncio
async def test_update_nonexistent_customer(client: AsyncClient, auth_headers: dict):
    """更新不存在的客户应返回 404"""
    response = await client.put("/api/v1/customers/fake-customer-id", json={
        "name": "不存在", "phone": "111",
    }, headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_customer_minimal_fields(client: AsyncClient, auth_headers: dict):
    """最少字段创建客户（仅姓名）"""
    response = await client.post("/api/v1/customers", json={
        "name": "极简客户",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "极简客户"
    assert data["phone"] is None
    assert data["tags"] == []


# ─── Customer Delete ───


@pytest.mark.asyncio
async def test_delete_customer(client: AsyncClient, auth_headers: dict):
    """删除客户"""
    create_resp = await client.post("/api/v1/customers", json={
        "name": "待删除客户", "phone": "13800000000",
    }, headers=auth_headers)
    customer_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/customers/{customer_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "删除成功" in response.json()["message"]

    # Verify deleted
    list_resp = await client.get("/api/v1/customers", headers=auth_headers)
    assert list_resp.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_customer(client: AsyncClient, auth_headers: dict):
    """删除不存在的客户应返回 404"""
    response = await client.delete("/api/v1/customers/fake-customer-id", headers=auth_headers)
    assert response.status_code == 404
