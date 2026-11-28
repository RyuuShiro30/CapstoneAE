import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import httpx
import pytest

from app.main import app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_health_and_openapi(client):
    health = await client.get("/health")
    assert health.json() == {"status": "ok", "service": "gurami-mang-ujang-ai"}
    assert health.status_code == 200
    assert (await client.get("/docs")).status_code == 200
    schema = (await client.get("/openapi.json")).json()
    assert "/api/v1/chat" in schema["paths"]
    assert set(schema["components"]["schemas"]["ChatRequest"]["required"]) == {
        "session_id",
        "message",
    }


@pytest.mark.parametrize(
    ("message", "intent", "handoff"),
    [
        ("Ada ikan gurame?", "tanya_produk", False),
        ("Mau beli gurame", "pemesanan", True),
        ("Komplain pesanan", "keluhan", True),
        ("Mau psn 2kg", "pemesanan", True),
        ("Komplen pesanan", "keluhan", True),
    ],
)
async def test_successful_chat_matches_legacy_contract(
    client, message, intent, handoff
):
    response = await client.post(
        "/api/v1/chat", json={"session_id": "test-session", "message": message}
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "intent", "reply", "redirect_whatsapp"}
    assert body["status"] == "success"
    assert body["intent"] == intent
    assert body["redirect_whatsapp"] is handoff
    assert isinstance(body["reply"], str) and body["reply"]


@pytest.mark.parametrize(
    "payload",
    [
        {"session_id": "test-session", "message": ""},
        {"session_id": "test-session", "message": "  \t  "},
        {"session_id": "test-session", "message": "x" * 1001},
        {"message": "test-sentinel"},
        {"session_id": "test-session", "message": 42},
    ],
)
async def test_invalid_input_has_safe_legacy_error_envelope(client, payload):
    response = await client.post("/api/v1/chat", json=payload)
    assert response.status_code == 400
    body = response.json()
    assert set(body) == {"status", "error_code", "message", "detail"}
    assert body["status"] == "error"
    assert body["error_code"] == "INVALID_INPUT"
    assert body["detail"]
    assert all({"loc", "msg", "type"} <= error.keys() for error in body["detail"])
    assert "test-sentinel" not in response.text
    assert all("ctx" not in error for error in body["detail"])


async def test_malformed_json_returns_bad_request(client):
    response = await client.post(
        "/api/v1/chat", content="{bad", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_INPUT"


@pytest.mark.parametrize(
    ("message", "reply_fragment", "handoff"),
    [
        ("Berapa harga gurame per kg?", "belum bisa memastikan harga", True),
        ("Masih ada stok gurami?", "belum bisa memastikan stok", True),
        ("Berapa ongkir gurame?", "dikonfirmasi langsung", True),
        ("Berapa harga saham hari ini?", "hanya bisa membantu", False),
        ("Brp hrg min?", "belum bisa memastikan harga", True),
        ("Masih ready gak, min?", "belum bisa memastikan stok", True),
        ("Almt kolam Mang Ujang dmn?", "dikonfirmasi langsung", True),
        ("Brp hrg laptop min?", "hanya bisa membantu", False),
    ],
)
async def test_chat_fallback_is_safe_and_compatible(
    client, message, reply_fragment, handoff
):
    response = await client.post(
        "/api/v1/chat", json={"session_id": "test-session", "message": message}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "tanya_produk"
    assert body["redirect_whatsapp"] is handoff
    assert reply_fragment in body["reply"].lower()


async def test_service_failure_keeps_503_envelope_without_exception_text(
    client, monkeypatch
):
    class BrokenService:
        async def respond(self, _message):
            raise RuntimeError("test-only-internal-value")

    monkeypatch.setattr(app.state, "chat_service", BrokenService(), raising=False)
    response = await client.post(
        "/api/v1/chat", json={"session_id": "test-session", "message": "Mau beli"}
    )

    assert response.status_code == 503
    body = response.json()
    assert set(body) == {"detail"}
    assert set(body["detail"]) == {"status", "error_code", "message", "detail"}
    assert body["detail"]["error_code"] == "AI_SERVICE_UNAVAILABLE"
    assert isinstance(body["detail"]["detail"], str)
    assert "test-only-internal-value" not in response.text


@pytest.mark.parametrize(
    ("origin", "status_code"),
    [("https://frontend.example", 200), ("https://other.example", 400)],
)
async def test_cors_allowlist_can_be_configured(origin, status_code):
    from app.core.config import Settings
    from app.main import create_app

    configured_app = create_app(
        Settings(
            cors_origins=("https://frontend.example",),
            cors_allow_credentials=False,
        )
    )
    transport = httpx.ASGITransport(app=configured_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/api/v1/chat",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )

    assert response.status_code == status_code
    assert "Access-Control-Allow-Credentials" not in response.headers
    if status_code == 200:
        assert response.headers["Access-Control-Allow-Origin"] == origin


@pytest.mark.parametrize("failure", ["timeout", "quota", "unavailable"])
async def test_optional_provider_failures_fall_back_over_http(failure, caplog):
    from app.ai.generation import GenerationQuotaExceeded
    from app.core.config import Settings
    from app.main import create_app
    from app.services.chat_service import ChatService

    async def generate(_prompt):
        if failure == "timeout":
            await asyncio.sleep(1)
        if failure == "quota":
            raise GenerationQuotaExceeded("provider-only-debug-text")
        raise RuntimeError("provider-only-debug-text")

    provider = AsyncMock()
    provider.generate.side_effect = generate
    settings = Settings(external_timeout_seconds=0.01)
    service = ChatService(settings, generation=provider)
    transport = httpx.ASGITransport(app=create_app(settings, chat_service=service))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"session_id": "test-session", "message": "Jual gurame apa?"},
        )

    assert response.status_code == 200
    assert "dijual per kilogram" in response.json()["reply"]
    provider.generate.assert_awaited_once()
    assert "provider-only-debug-text" not in response.text
    assert "provider-only-debug-text" not in caplog.text
