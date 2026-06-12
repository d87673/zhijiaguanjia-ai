from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import ChatRequest
from app.services.ai_service import chat_completion_stream, AI_PROMPTS, select_model
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("", response_model=dict)
async def ai_endpoint(
    req: ChatRequest,
    _: User = Depends(get_current_user),
):
    """AI endpoint: chat, dispatch optimization, marketing copywriting"""
    system_prompt = AI_PROMPTS.get(req.action, AI_PROMPTS["customer_service"])
    model = select_model(action=req.action)

    full_messages = [{"role": "system", "content": system_prompt}]
    if req.context:
        full_messages.append({"role": "system", "content": f"额外信息: {req.context}"})
    full_messages.extend(req.messages)

    result = await chat_completion_stream(full_messages, model=model)
    reply = result.get("choices", [{}])[0].get("message", {}).get("content", "AI服务暂不可用")

    return {"reply": reply}


@router.post("/stream")
async def ai_stream_endpoint(
    req: ChatRequest,
    _: User = Depends(get_current_user),
):
    """Streaming AI response via Server-Sent Events (SSE)."""
    system_prompt = AI_PROMPTS.get(req.action, AI_PROMPTS["customer_service"])
    model = select_model(action=req.action)

    full_messages = [{"role": "system", "content": system_prompt}]
    if req.context:
        full_messages.append({"role": "system", "content": f"额外信息: {req.context}"})
    full_messages.extend(req.messages)

    async def event_generator():
        try:
            async for chunk in chat_completion_stream(full_messages, model=model):
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

            # Signal end
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
