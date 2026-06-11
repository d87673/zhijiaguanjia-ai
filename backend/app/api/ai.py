from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import ChatRequest
from app.services.ai_service import chat_completion, AI_PROMPTS

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("", response_model=dict)
async def ai_endpoint(
    req: ChatRequest,
    _: User = Depends(get_current_user),
):
    """AI endpoint: chat, dispatch optimization, marketing copywriting"""
    system_prompt = AI_PROMPTS.get(req.action, AI_PROMPTS["customer_service"])

    full_messages = [{"role": "system", "content": system_prompt}]
    if req.context:
        full_messages.append({"role": "system", "content": f"额外信息: {req.context}"})
    full_messages.extend(req.messages)

    result = await chat_completion(full_messages)
    reply = result.get("choices", [{}])[0].get("message", {}).get("content", "AI服务暂不可用")

    return {"reply": reply}
