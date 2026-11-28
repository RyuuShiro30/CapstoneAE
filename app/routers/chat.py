from fastapi import APIRouter, HTTPException, status
from app.schemas import ChatRequest, ChatResponse, ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["Chatbot"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def chat_endpoint(payload: ChatRequest):
    try:
        user_text = payload.message.lower()

        if "keluhan" in user_text or "komplain" in user_text:
            return ChatResponse(
                intent="keluhan",
                reply="Mohon maaf atas ketidaknyamanannya. Pesan Anda akan diteruskan langsung kepada pengelola Gurami Konsumsi Mang Ujang.",
                redirect_whatsapp=True,
            )

        if "pesan" in user_text or "beli" in user_text or "order" in user_text:
            return ChatResponse(
                intent="pemesanan",
                reply="Baik, untuk pemesanan ikan gurame silakan lanjutkan konfirmasi jumlah kg dan metode COD/ambil di lokasi melalui WhatsApp kami.",
                redirect_whatsapp=True,
            )

        return ChatResponse(
            intent="tanya_produk",
            reply="Halo! Selamat datang di Gurami Konsumsi Mang Ujang. Kami menyediakan ikan gurame konsumsi ukuran besar dijual per kilogram. Ada yang bisa dibantu?",
            redirect_whatsapp=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error_code": "AI_SERVICE_UNAVAILABLE",
                "message": "Maaf, layanan asisten AI sedang sibuk. Silakan coba beberapa saat lagi atau hubungi pengelola via WhatsApp.",
                "detail": str(exc),
            },
        )