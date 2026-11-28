import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import TypeVar

from app.ai.generation import (
    GenerationProvider,
    GenerationQuotaExceeded,
    KnowledgeRetriever,
    build_product_prompt,
)
from app.ai.guardrails import should_refuse
from app.ai.intent import Intent, IntentClassifier, RuleBasedIntentClassifier
from app.core.config import Settings
from app.integrations.catalog import CatalogReader

logger = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ChatResult:
    intent: str
    reply: str
    redirect_whatsapp: bool = False


PRODUCT_REPLY = (
    "Kami menyediakan ikan gurame konsumsi berukuran besar, dijual per kilogram."
)
APPROVED_PRODUCT_REPLIES = {
    "product": PRODUCT_REPLY,
    "unit": "Penjualan ikan gurame dihitung berdasarkan berat dalam kilogram.",
}
REFUSAL_REPLY = (
    "Maaf, saya hanya bisa membantu seputar produk dan pemesanan "
    "Gurami Konsumsi Mang Ujang."
)

RESPONSES = {
    Intent.PRICE: ChatResult(
        "tanya_produk",
        "Saya belum bisa memastikan harga gurame terbaru. "
        "Silakan konfirmasi harga per kilogram melalui WhatsApp pengelola.",
        True,
    ),
    Intent.STOCK: ChatResult(
        "tanya_produk",
        "Saya belum bisa memastikan stok gurame saat ini. "
        "Silakan cek ketersediaan melalui WhatsApp pengelola.",
        True,
    ),
    Intent.POLICY: ChatResult(
        "tanya_produk",
        "Informasi tersebut perlu dikonfirmasi langsung melalui WhatsApp pengelola.",
        True,
    ),
    Intent.ORDER: ChatResult(
        "pemesanan",
        "Silakan konfirmasi jumlah kilogram dan pilihan COD atau ambil langsung "
        "melalui WhatsApp pengelola.",
        True,
    ),
    Intent.COMPLAINT: ChatResult(
        "keluhan",
        "Mohon maaf atas ketidaknyamanannya. Silakan hubungi pengelola melalui "
        "WhatsApp agar keluhan Anda bisa ditangani.",
        True,
    ),
    Intent.GREETING: ChatResult(
        "tanya_produk",
        "Halo! Saya bisa membantu seputar produk dan pemesanan Gurami Konsumsi Mang Ujang.",
    ),
    Intent.OUT_OF_SCOPE: ChatResult("tanya_produk", REFUSAL_REPLY),
}


class ChatService:
    """Route customer messages without depending on HTTP or vendor APIs."""

    def __init__(
        self,
        settings: Settings,
        *,
        classifier: IntentClassifier | None = None,
        catalog: CatalogReader | None = None,
        retriever: KnowledgeRetriever | None = None,
        generation: GenerationProvider | None = None,
    ) -> None:
        self.settings = settings
        self.classifier = (
            classifier if classifier is not None else RuleBasedIntentClassifier()
        )
        self.catalog = catalog
        self.retriever = retriever
        self.generation = generation

    async def respond(self, message: str) -> ChatResult:
        """Return a public reply for a single, stateless customer message."""
        if should_refuse(message):
            return RESPONSES[Intent.OUT_OF_SCOPE]

        prediction = await asyncio.to_thread(self.classifier.predict, message)
        if prediction.confidence is not None and not (
            self.settings.intent_min_confidence <= prediction.confidence <= 1
        ):
            return ChatResult(
                "tanya_produk",
                "Boleh diperjelas? Saya bisa membantu soal produk, harga, stok, atau pemesanan.",
            )

        intent = prediction.intent
        if intent == Intent.PRODUCT:
            return await self._respond_to_product_question(message)
        if intent in {Intent.PRICE, Intent.STOCK} and self.catalog is not None:
            return await self._respond_from_catalog(intent, self.catalog)
        return RESPONSES[intent]

    async def _respond_to_product_question(self, message: str) -> ChatResult:
        replies = APPROVED_PRODUCT_REPLIES
        if self.retriever is not None:
            ranked = await self._within_budget(
                self.retriever.retrieve_reply_ids(message), "knowledge retrieval"
            )
            retrieved = {key: replies[key] for key in ranked or () if key in replies}
            if retrieved:
                replies = retrieved

        selected = next(iter(replies))
        if self.generation is not None:
            prompt = build_product_prompt(message, replies)
            proposed = await self._within_budget(
                self.generation.generate(prompt), "generation"
            )
            if isinstance(proposed, str) and proposed.strip() in replies:
                selected = proposed.strip()
        return ChatResult("tanya_produk", replies[selected])

    async def _respond_from_catalog(
        self, intent: Intent, catalog: CatalogReader
    ) -> ChatResult:
        snapshot = await self._within_budget(catalog.get_current_product(), "catalog")
        if snapshot is not None:
            if intent == Intent.PRICE and snapshot.price_idr_per_kg is not None:
                amount = f"{snapshot.price_idr_per_kg:,}".replace(",", ".")
                return ChatResult(
                    "tanya_produk", f"Harga gurame saat ini Rp{amount} per kilogram."
                )
            if intent == Intent.STOCK and snapshot.in_stock is not None:
                availability = "tersedia" if snapshot.in_stock else "sedang habis"
                return ChatResult("tanya_produk", f"Stok gurame {availability}.")
        return RESPONSES[intent]

    async def _within_budget(self, operation: Awaitable[T], component: str) -> T | None:
        # Optional read-only adapters get one attempt. The fallback stays available.
        try:
            return await asyncio.wait_for(
                operation, timeout=self.settings.external_timeout_seconds
            )
        except TimeoutError:
            logger.warning("Chat %s timed out", component)
        except GenerationQuotaExceeded:
            logger.warning("Chat %s quota exceeded", component)
        except Exception as exc:
            logger.warning("Chat %s unavailable (%s)", component, type(exc).__name__)
        return None
