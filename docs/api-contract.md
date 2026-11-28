# API Contract

Basis perbandingan adalah `main` pada commit `4330022`. Entry point tetap `app.main:app`. Swagger tersedia di `/docs` dan schema di `/openapi.json`.

## Health

`GET /health` → `200`

~~~json
{"status":"ok","service":"gurami-mang-ujang-ai"}
~~~

## Chat

`POST /api/v1/chat` menerima JSON dengan dua string wajib, `session_id` dan `message`. Batas `message` tetap 1 sampai 1.000 karakter. Pesan hanya-spasi ditolak.

~~~json
{"session_id":"demo-001","message":"Mau pesan gurame 2 kilogram"}
~~~

Contoh respons `200`

~~~json
{
  "status": "success",
  "intent": "pemesanan",
  "reply": "Silakan konfirmasi jumlah kilogram dan pilihan COD atau ambil langsung melalui WhatsApp pengelola.",
  "redirect_whatsapp": true
}
~~~

| Public intent | Meaning |
| --- | --- |
| `pemesanan` | Panduan melanjutkan pembicaraan tentang pesanan. |
| `keluhan` | Panduan menghubungi pengelola untuk menangani keluhan. |
| `tanya_produk` | Informasi produk, harga, stok, sapaan, klarifikasi, kebijakan, atau penolakan topik lain. |

Gunakan `redirect_whatsapp` untuk menampilkan handoff melalui tautan Click-to-Chat yang disetujui. Konfirmasi pesanan terjadi dalam percakapan dengan pengelola. API belum menyimpan tautan atau nomor. Jika pesan memuat beberapa kebutuhan, API memproses satu intent per giliran.

## Errors

Respons `400` untuk masukan tidak valid mempertahankan `status`, `error_code`, `message`, dan array `detail`. Tiap item memuat `loc`, `msg`, dan `type`. Nilai input dan konteks exception dikeluarkan dari respons.

~~~json
{
  "status": "error",
  "error_code": "INVALID_INPUT",
  "message": "Input yang dikirim tidak valid atau pesan kosong.",
  "detail": [{"type": "missing", "loc": ["body", "session_id"], "msg": "Field required"}]
}
~~~

Respons `503` memakai envelope `detail` dari FastAPI dan code `AI_SERVICE_UNAVAILABLE`. Isi `detail.detail` berupa string aman.

~~~json
{
  "detail": {
    "status": "error",
    "error_code": "AI_SERVICE_UNAVAILABLE",
    "message": "Maaf, layanan asisten AI sedang sibuk. Silakan coba beberapa saat lagi atau hubungi pengelola via WhatsApp.",
    "detail": "Layanan chat sementara tidak tersedia."
  }
}
~~~

Swagger mendeklarasikan `ErrorResponse` generik. Sejak baseline, definisi tersebut berbeda dari array detail runtime `400` dan envelope runtime `503`. Gunakan contoh runtime di atas sampai Full-stack menyepakati pembetulan spesifikasi. Perbedaan OpenAPI pada branch ini terbatas pada contoh `reply`, yang sekarang memakai informasi satuan penjualan.

## Integration Checklist

- Konfirmasi origin CORS, bentuk error, label intent publik, tautan Click-to-Chat, dan contoh respons dengan Full-stack.
- Sepakati endpoint baca katalog serta perlakuan data yang tidak tersedia atau kedaluwarsa.
- Uji URL deployment dari backend Full-stack sebelum menyatakan serving online selesai.
