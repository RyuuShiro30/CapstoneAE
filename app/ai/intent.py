import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.ai.text import normalize_message


class Intent(StrEnum):
    PRODUCT = "tanya_produk"
    PRICE = "tanya_harga"
    STOCK = "tanya_stok"
    ORDER = "pemesanan"
    COMPLAINT = "keluhan"
    GREETING = "sapaan"
    POLICY = "tanya_kebijakan"
    OUT_OF_SCOPE = "luar_konteks"


@dataclass(frozen=True, slots=True)
class IntentPrediction:
    intent: Intent
    confidence: float | None = None


class IntentClassifier(Protocol):
    def predict(self, message: str) -> IntentPrediction:
        """Classify a raw message and optionally return a calibrated confidence."""
        ...


PRODUCT_TOPIC = re.compile(r"\b(?:guram[ei]|mang ujang|ikan konsumsi)\b")
NON_CUSTOMER_TOPICS = re.compile(r"\b(?:budidaya|pakan|resep|habitat|ternak)\b")

CUSTOMER_INTENTS = (
    (Intent.COMPLAINT, r"\b(?:komplain|keluhan|mengeluh|pengaduan|bermasalah)\b"),
    (
        Intent.POLICY,
        r"\b(?:ongkir(?:nya)?|ongkos kirim|biaya (?:antar|pengiriman|kirim)|"
        r"alamat(?:nya)?|lokasi(?:nya)?|"
        r"jam (?:buka|operasional)|jadwal buka|buka jam|promo(?:si)?|diskon)\b",
    ),
    (Intent.PRICE, r"\b(?:harga(?:nya)?|berapa (?:rupiah|per (?:kg|kilo)))\b"),
    (Intent.STOCK, r"\b(?:stok(?:nya)?|ketersediaan|tersedia|masih ada|habis)\b"),
    (
        Intent.ORDER,
        r"\b(?:pesan(?:an)?|pemesanan|memesan|beli|pembelian|order|"
        r"cod|antar|diantar|ambil langsung|pickup|whatsapp)\b",
    ),
)

# Short utterances can refer to the business without explicitly naming the fish.
STANDALONE_INTENTS = (
    (
        Intent.COMPLAINT,
        r"(?:(?:saya )?(?:mau|ingin) )?(?:komplain|keluhan|pengaduan)"
        r"(?: (?:soal |tentang )?pesanan(?: saya)?)?",
    ),
    (
        Intent.POLICY,
        r"(?:(?:berapa|kapan) )?(?:ongkir(?:nya)?|alamat(?:nya)?(?: di mana)?|"
        r"lokasi(?:nya)?(?: di mana)?|jam buka|buka jam berapa|ada promo|ada diskon)"
        r"(?: berapa)?",
    ),
    (
        Intent.PRICE,
        r"(?:kalau )?(?:berapa (?:harga(?:nya)?|per (?:kg|kilo))|"
        r"harga(?:nya)?(?: per (?:kg|kilo))?(?: berapa)?)",
    ),
    (
        Intent.STOCK,
        r"(?:kalau )?(?:(?:ada|cek|masih ada) stok(?:nya)?|"
        r"stok(?:nya)?(?: masih ada| ada| habis)?|masih ada)",
    ),
    (
        Intent.ORDER,
        r"(?:(?:saya )?(?:mau|ingin) |(?:bagaimana |gimana )?cara |bisa )?"
        r"(?:pesan|memesan|beli|order)(?: (?:\d+ (?:kg|kilo)|lewat whatsapp))?"
        r"|(?:bisa )?(?:cod|ambil langsung)|(?:nomor |kontak )?whatsapp(?:nya)?",
    ),
    (
        Intent.PRODUCT,
        r"(?:produk(?:nya)?(?: apa| apa saja)?|jual ikan apa|dijual per (?:kg|kilo))",
    ),
    (
        Intent.GREETING,
        r"(?:halo|hai|hei|hi|selamat (?:pagi|siang|sore|malam)|"
        r"assalamu'?alaikum)(?:,? (?:kak|min|gan))?",
    ),
)


class RuleBasedIntentClassifier:
    """Deterministic fallback while an evaluated model is being prepared."""

    def predict(self, message: str) -> IntentPrediction:
        text = normalize_message(message)
        if PRODUCT_TOPIC.search(text) and not NON_CUSTOMER_TOPICS.search(text):
            for intent, pattern in CUSTOMER_INTENTS:
                if re.search(pattern, text):
                    return IntentPrediction(intent)
            return IntentPrediction(Intent.PRODUCT)

        text = text.strip(".,!? ")
        for intent, pattern in STANDALONE_INTENTS:
            if re.fullmatch(pattern, text):
                return IntentPrediction(intent)
        return IntentPrediction(Intent.OUT_OF_SCOPE)
