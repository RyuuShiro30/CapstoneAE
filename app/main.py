from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.routers import chat
from app.services.chat_service import ChatService


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "Input yang dikirim tidak valid atau pesan kosong.",
            "detail": [
                {field: error[field] for field in ("type", "loc", "msg")}
                for error in exc.errors()
            ],
        },
    )


async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "gurami-mang-ujang-ai"}


def create_app(
    settings: Settings | None = None, *, chat_service: ChatService | None = None
) -> FastAPI:
    """Create the existing API with a reusable chatbot service."""
    settings = settings if settings is not None else Settings.from_env()
    application = FastAPI(
        title="AI Chatbot API - Gurami Konsumsi Mang Ujang",
        description=(
            "REST API layanan AI Customer Service Chatbot untuk "
            "UMKM Gurami Konsumsi Mang Ujang."
        ),
        version="1.0.0",
    )
    application.state.chat_service = (
        chat_service if chat_service is not None else ChatService(settings)
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    application.get("/health", tags=["System"], response_model=None)(health_check)
    application.include_router(chat.router)
    return application


app = create_app()
