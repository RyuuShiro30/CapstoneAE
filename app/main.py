from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import chat

app = FastAPI(
    title="AI Chatbot API - Gurami Konsumsi Mang Ujang",
    description="REST API layanan AI Customer Service Chatbot untuk UMKM Gurami Konsumsi Mang Ujang.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "Input yang dikirim tidak valid atau pesan kosong.",
            "detail": exc.errors(),
        },
    )


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "gurami-mang-ujang-ai"}


app.include_router(chat.router)