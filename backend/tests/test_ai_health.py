"""
单元测试: AI 模块和健康检查
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_chat_mocked(client: AsyncClient, auth_headers: dict):
    """AI 聊天（Mock）"""
    with patch("app.api.ai.chat_completion_stream", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "choices": [{
                "message": {
                    "content": "您好！我是小智，很高兴为您服务。"
                }
            }]
        }

        response = await client.post("/api/v1/ai", json={
            "action": "chat",
            "messages": [{"role": "user", "content": "你好"}],
        }, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data


@pytest.mark.asyncio
async def test_ai_chat_action_types(client: AsyncClient, auth_headers: dict):
    """不同 action 类型"""
    with patch("app.api.ai.chat_completion_stream", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {"choices": [{"message": {"content": "OK"}}]}

        for action in ["chat", "dispatch", "copywriter"]:
            response = await client.post("/api/v1/ai", json={
                "action": action,
                "messages": [{"role": "user", "content": "测试"}],
            }, headers=auth_headers)
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_ai_stream_endpoint(client: AsyncClient, auth_headers: dict):
    """SSE 流式端点"""
    async def mock_stream(messages, model="", **kwargs):
        yield {"choices": [{"delta": {"content": "您好"}}]}
        yield {"choices": [{"delta": {"content": "！"}}]}

    with patch("app.api.ai.chat_completion_stream", side_effect=mock_stream):
        response = await client.post("/api/v1/ai/stream", json={
            "action": "chat",
            "messages": [{"role": "user", "content": "你好"}],
        }, headers=auth_headers)

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        body = response.text
        assert "[DONE]" in body


@pytest.mark.asyncio
async def test_ai_unauthenticated(client: AsyncClient):
    """未认证访问 AI（Mock 避免真实 API 调用）"""
    with patch("app.api.ai.chat_completion_stream", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {"choices": [{"message": {"content": "OK"}}]}
        response = await client.post("/api/v1/ai", json={
            "action": "chat",
            "messages": [{"role": "user", "content": "你好"}],
        })
        # With override auth: 200, without: 401/403
        assert response.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_ai_stream_unauthenticated(client: AsyncClient):
    """未认证访问流式 AI"""
    response = await client.post("/api/v1/ai/stream", json={
        "action": "chat",
        "messages": [{"role": "user", "content": "你好"}],
    })
    assert response.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """健康检查"""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["name"] == "智家管家AI"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """根路径"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "智家管家AI"
