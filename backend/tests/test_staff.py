"""
单元测试: 员工管理 (Staff)
测试员工 CRUD 和技能标签
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_staff(client: AsyncClient, auth_headers: dict):
    """创建新员工"""
    response = await client.post("/api/v1/staff", json={
        "name": "李师傅",
        "phone": "13900001111",
        "email": "lisf@example.com",
        "skills": ["cleaning", "repair"],
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "李师傅"
    assert data["phone"] == "13900001111"
    assert "cleaning" in data["skills"]
    assert "repair" in data["skills"]
    assert data["is_active"] is True
    assert data["rating"] == 5.0
    assert data["current_load"] == 0


@pytest.mark.asyncio
async def test_list_staff(client: AsyncClient, auth_headers: dict):
    """获取员工列表"""
    for name in ["王师傅", "刘阿姨", "张工"]:
        await client.post("/api/v1/staff", json={
            "name": name, "phone": "13800000000",
        }, headers=auth_headers)

    response = await client.get("/api/v1/staff", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["staff"]) == 3


@pytest.mark.asyncio
async def test_search_staff_by_name(client: AsyncClient, auth_headers: dict):
    """按名称搜索员工"""
    await client.post("/api/v1/staff", json={
        "name": "张师傅", "phone": "13811111111",
    }, headers=auth_headers)
    await client.post("/api/v1/staff", json={
        "name": "李师傅", "phone": "13822222222",
    }, headers=auth_headers)

    response = await client.get("/api/v1/staff?q=张", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["staff"][0]["name"] == "张师傅"


@pytest.mark.asyncio
async def test_delete_staff(client: AsyncClient, auth_headers: dict):
    """删除员工"""
    create_resp = await client.post("/api/v1/staff", json={
        "name": "待删除员工", "phone": "13800000000",
    }, headers=auth_headers)
    staff_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/staff/{staff_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "删除成功" in response.json()["message"]

    # Verify deleted
    list_resp = await client.get("/api/v1/staff", headers=auth_headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_staff(client: AsyncClient, auth_headers: dict):
    """删除不存在的员工应返回 404"""
    response = await client.delete("/api/v1/staff/fake-staff-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_staff_with_skills(client: AsyncClient, auth_headers: dict):
    """创建带多个技能标签的员工"""
    skills = ["cleaning", "cooking", "babysitting", "elderlycare", "repair"]
    response = await client.post("/api/v1/staff", json={
        "name": "全能阿姨",
        "phone": "13833333333",
        "skills": skills,
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data["skills"]) == 5
    assert all(s in data["skills"] for s in skills)
