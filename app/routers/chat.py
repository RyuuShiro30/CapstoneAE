import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chatbot"])


async def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def chat_endpoint(
    payload: ChatRequest,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    try:
        result = await chat_service.respond(payload.message)
        return ChatResponse(
            intent=result.intent,
            reply=result.reply,
            redirect_whatsapp=result.redirect_whatsapp,
        )
    except Exception as exc:
        logger.error("Chat request failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error_code": "AI_SERVICE_UNAVAILABLE",
                "message": (
                    "Maaf, layanan asisten AI sedang sibuk. Silakan coba beberapa saat "
                    "lagi atau hubungi pengelola via WhatsApp."
                ),
                "detail": "Layanan chat sementara tidak tersedia.",
            },
        ) from None
