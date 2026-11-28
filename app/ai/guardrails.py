import re

from app.ai.text import normalize_message

PRIVATE_OR_OVERRIDE_REQUEST = re.compile(
    r"\b(?:system[ _-]+prompt|prompt sistem|instruksi sistem|pesan sistem|developer message|"
    r"prompt (?:awal|internal)|(?:abaikan|lupakan|lewati) .{0,60}?(?:instruksi|aturan|prompt)|"
    r"ignore .{0,60}?(?:instructions|rules|prompt)|"
    r"api[ _-]?keys?|password|kata sandi|token akses|data (?:internal|admin|pelanggan)|"
    r"(?:daftar|riwayat) (?:transaksi|pelanggan)|laporan (?:keuangan|penjualan)|"
    r"(?:panel|dashboard) admin|basis data internal)\b"
)


def should_refuse(message: str) -> bool:
    """Identify requests for internal information and common instruction overrides."""
    return bool(PRIVATE_OR_OVERRIDE_REQUEST.search(normalize_message(message)))
