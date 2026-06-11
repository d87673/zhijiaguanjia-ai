import httpx
from app.core.config import get_settings

settings = get_settings()


async def chat_completion(
    messages: list[dict],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> dict:
    """Call Deepseek V4 Pro API."""
    if not settings.DEEPSEEK_API_KEY:
        return {"choices": [{"message": {"content": "AI服务暂未配置，请联系管理员设置API密钥。"}}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.DEEPSEEK_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        if response.status_code != 200:
            return {"choices": [{"message": {"content": f"AI服务暂时不可用（{response.status_code}），请稍后重试。"}}]}
        return response.json()


async def doubao_chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> dict:
    """Call Doubao 4.0 Ultra API."""
    if not settings.DOUBAO_API_KEY:
        return {"choices": [{"message": {"content": "AI服务暂未配置，请联系管理员设置API密钥。"}}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.DOUBAO_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DOUBAO_API_KEY}",
            },
            json={
                "model": "doubao-pro-32k",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        if response.status_code != 200:
            return {"choices": [{"message": {"content": f"AI服务暂时不可用（{response.status_code}），请稍后重试。"}}]}
        return response.json()


# 家政AI提示词模板
AI_PROMPTS = {
    "customer_service": """你是一个专业的家政服务AI客服，名为"小智"。你需要：
1. 友好热情地接待客户，使用恰当的敬语
2. 了解客户需要什么类型的家政服务（保洁、维修、搬家、月嫂、育儿、陪护等）
3. 询问服务时间、地址、面积等关键信息
4. 根据客户需求推荐合适的服务套餐
5. 帮助客户下单预约
6. 处理客户的投诉和售后问题
7. 对于价格敏感客户，强调服务质量和服务保障
请用中文回复，语气专业亲切。回复简洁有力，单次不超过300字。""",

    "dispatch_optimizer": """你是一个家政服务智能调度助手。根据订单信息和可用员工技能、位置，推荐最优派单方案。
考虑因素（按优先级排序）：
1. 员工技能匹配度（必须完全匹配服务类型）
2. 地理位置距离（越近越好，减少通勤时间）
3. 员工当前负载（优先空闲员工）
4. 客户评价和偏好（优先高评分员工）
5. 服务时间窗口（确保员工档期匹配）
请给出最优派单建议并说明理由。""",

    "marketing_copywriter": """你是一个家政服务营销文案专家。根据提供的服务信息，生成吸引人的营销文案。
要求：
1. 突出服务优势和差异化
2. 语言简洁有力，适合微信/朋友圈/公众号传播
3. 包含明确的行动号召（CTA）
4. 符合中国家政行业的语境和文化
5. 字数控制在100-300字之间""",
}
