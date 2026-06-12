"""
单元测试: 公司管理 (Company)
测试公司信息获取、更新和密钥管理
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_company(client: AsyncClient, auth_headers: dict):
    """获取当前公司信息"""
    response = await client.get("/api/v1/company", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试家政公司"
    assert data["plan"] == "pro"
    assert "slug" in data
    assert "settings" in data


@pytest.mark.asyncio
async def test_update_company_name(client: AsyncClient, auth_headers: dict):
    """更新公司名称"""
    response = await client.put("/api/v1/company", json={
        "name": "新公司名称",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert "已更新" in response.json()["message"]

    # Verify the change
    get_resp = await client.get("/api/v1/company", headers=auth_headers)
    assert get_resp.json()["name"] == "新公司名称"


@pytest.mark.asyncio
async def test_update_company_phone_and_address(client: AsyncClient, auth_headers: dict):
    """更新公司联系方式和地址（存储在 settings JSON 字段中）"""
    response = await client.put("/api/v1/company", json={
        "phone": "400-888-9999",
        "address": "北京市朝阳区XX大厦18层",
    }, headers=auth_headers)
    assert response.status_code == 200

    # Verify settings updated
    get_resp = await client.get("/api/v1/company", headers=auth_headers)
    settings = get_resp.json()["settings"]
    assert settings["phone"] == "400-888-9999"
    assert settings["address"] == "北京市朝阳区XX大厦18层"


@pytest.mark.asyncio
async def test_update_company_empty_body(client: AsyncClient, auth_headers: dict):
    """空请求体更新应返回提示"""
    response = await client.put("/api/v1/company", json={}, headers=auth_headers)
    assert response.status_code == 200
    assert "没有需要更新" in response.json()["message"]


@pytest.mark.asyncio
async def test_update_company_keys(client: AsyncClient, auth_headers: dict):
    """更新 API 密钥"""
    response = await client.put("/api/v1/company/keys", json={
        "deepseek_key": "sk-test-deepseek-key-12345",
        "doubao_key": "db-test-doubao-key-67890",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert "已更新" in response.json()["message"]

    # Verify keys stored in settings.api_keys
    get_resp = await client.get("/api/v1/company", headers=auth_headers)
    api_keys = get_resp.json()["settings"]["api_keys"]
    assert api_keys["deepseek_key"] == "sk-test-deepseek-key-12345"
    assert api_keys["doubao_key"] == "db-test-doubao-key-67890"


@pytest.mark.asyncio
async def test_update_company_keys_partial(client: AsyncClient, auth_headers: dict):
    """部分更新密钥 — 只更新一个，不影响其余的"""
    # Set initial keys
    await client.put("/api/v1/company/keys", json={
        "deepseek_key": "sk-first",
        "doubao_key": "db-first",
    }, headers=auth_headers)

    # Partially update only doubao
    response = await client.put("/api/v1/company/keys", json={
        "doubao_key": "db-updated",
    }, headers=auth_headers)
    assert response.status_code == 200

    # Verify: doubao updated, deepseek preserved
    get_resp = await client.get("/api/v1/company", headers=auth_headers)
    api_keys = get_resp.json()["settings"]["api_keys"]
    assert api_keys["deepseek_key"] == "sk-first"
    assert api_keys["doubao_key"] == "db-updated"


@pytest.mark.asyncio
async def test_update_company_keys_empty_body(client: AsyncClient, auth_headers: dict):
    """空密钥更新应返回提示"""
    response = await client.put("/api/v1/company/keys", json={}, headers=auth_headers)
    assert response.status_code == 200
    assert "没有需要更新" in response.json()["message"]


@pytest.mark.asyncio
async def test_update_company_keys_wechat_alipay(client: AsyncClient, auth_headers: dict):
    """更新微信支付和支付宝密钥"""
    response = await client.put("/api/v1/company/keys", json={
        "wechat_mch_id": "WX1234567890",
        "alipay_app_id": "ALIPAY20240001",
    }, headers=auth_headers)
    assert response.status_code == 200

    get_resp = await client.get("/api/v1/company", headers=auth_headers)
    api_keys = get_resp.json()["settings"]["api_keys"]
    assert api_keys["wechat_mch_id"] == "WX1234567890"
    assert api_keys["alipay_app_id"] == "ALIPAY20240001"
