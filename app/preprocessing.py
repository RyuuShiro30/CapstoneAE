import re
import unicodedata
from typing import List, Optional

# Kamus normalisasi singkatan & bahasa kasual pelanggan UMKM
SLANG_DICT = {
    "brp": "berapa",
    "brpa": "berapa",
    "hrg": "harga",
    "hrga": "harga",
    "yg": "yang",
    "gk": "tidak",
    "gak": "tidak",
    "ga": "tidak",
    "g": "tidak",
    "tdk": "tidak",
    "blm": "belum",
    "blom": "belum",
    "sdh": "sudah",
    "udh": "sudah",
    "udah": "sudah",
    "bs": "bisa",
    "bsa": "bisa",
    "klo": "kalau",
    "kl": "kalau",
    "kalo": "kalau",
    "dgn": "dengan",
    "dg": "dengan",
    "utk": "untuk",
    "bwt": "buat",
    "dr": "dari",
    "dlm": "dalam",
    "krn": "karena",
    "karna": "karena",
    "sy": "saya",
    "aku": "saya",
    "ak": "saya",
    "min": "admin",
    "kak": "admin",
    "bang": "admin",
    "mang": "admin",
    "mas": "admin",
    "ready": "tersedia",
    "redy": "tersedia",
    "redi": "tersedia",
    "stok": "stok",
    "stock": "stok",
    "uk": "ukuran",
    "ukr": "ukuran",
    "kilo": "kg",
    "kilogram": "kg",
    "ons": "ons",
    "gr": "gram",
    "gram": "gram",
    "bkr": "bakar",
    "grg": "goreng",
    "pesen": "pesan",
    "psn": "pesan",
    "order": "pesan",
    "ordr": "pesan",
    "beli": "beli",
    "bli": "beli",
    "ongkir": "ongkos kirim",
    "cod": "cod",
    "anter": "antar",
    "antr": "antar",
    "krm": "kirim",
    "almt": "alamat",
    "lok": "lokasi",
    "dmn": "dimana",
    "dmna": "dimana",
    "kpn": "kapan",
    "gimana": "bagaimana",
    "gmn": "bagaimana",
    "gmna": "bagaimana",
    "tlg": "tolong",
    "tlng": "tolong",
    "mksih": "terima kasih",
    "makasih": "terima kasih",
    "mksh": "terima kasih",
    "thx": "terima kasih",
    "komplen": "keluhan",
    "komplain": "keluhan",
    "bau": "bau",
    "mati": "mati",
    "telat": "terlambat",
    "lama": "lambat",
}


def clean_text(text: Optional[str]) -> str:
    """
    Membersihkan dan menormalisasi teks pesan pelanggan:
    1. Validasi tipe data & normalisasi Unicode
    2. Case folding (huruf kecil)
    3. Hapus URL, mention, hashtag
    4. Pisahkan angka dan satuan (contoh: '1kg' -> '1 kg')
    5. Hapus tanda baca, emoji, dan simbol non-alfanumerik
    6. Ringkas huruf berulang berlebihan (contoh: 'halooo' -> 'halo')
    7. Normalisasi kata singkatan menggunakan SLANG_DICT
    """
    if text is None or not isinstance(text, str):
        return ""

    # 1. Normalisasi Unicode & case folding
    normalized = unicodedata.normalize("NFKC", text).lower()

    # 2. Hapus URL, mention (@user), dan hashtag (#tag)
    normalized = re.sub(r"http\S+|www\.\S+|@\w+|#\w+", " ", normalized)

    # 3. Pisahkan angka yang menempel dengan huruf (misal: 2kg -> 2 kg)
    normalized = re.sub(r"(\d+)([a-z]+)", r"\1 \2", normalized)
    normalized = re.sub(r"([a-z]+)(\d+)", r"\1 \2", normalized)

    # 4. Hapus karakter selain huruf a-z, angka 0-9, dan spasi
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)

    # 5. Pangkas pengulangan huruf lebih dari 2 kali (contoh: 'readyyyy' -> 'ready')
    normalized = re.sub(r"([a-z])\1{2,}", r"\1", normalized)

    # 6. Tokenisasi berbasis spasi & normalisasi slang
    tokens = normalized.split()
    cleaned_tokens = [SLANG_DICT.get(token, token) for token in tokens]

    return " ".join(cleaned_tokens)


def preprocess_batch(texts: List[Optional[str]]) -> List[str]:
    """Menjalankan clean_text untuk sekumpulan teks (dataset)."""
    return [clean_text(t) for t in texts]
