from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, examples=["user-123"])
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        examples=["Halo, harga gurame per kg berapa?"],
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Pesan tidak boleh kosong atau hanya berisi spasi.")
        return cleaned


class ChatResponse(BaseModel):
    status: str = "success"
    intent: str = Field(..., examples=["tanya_produk"])
    reply: str = Field(..., examples=["Ikan gurame konsumsi dijual per kilogram."])
    redirect_whatsapp: bool = False


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str = Field(..., examples=["INVALID_INPUT"])
    message: str = Field(..., examples=["Input pesan tidak valid."])
    detail: Optional[str] = None
