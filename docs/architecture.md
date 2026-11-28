# Chatbot Architecture

## Foundation Scope

CapstoneAE membantu pembeli gurame konsumsi mendapatkan informasi dan melanjutkan konfirmasi pesanan atau keluhan ke pengelola. Sumber bisnis tahap ini adalah use case yang divalidasi UMKM, khususnya halaman PDF 21, 25–26, dan 29. Alur chatbot bersifat baca-saja. Pengelola dan backend Full-stack menangani inventaris, pembayaran, dan transaksi.

## Modules and Dependencies

| Layer | Module | Responsibility |
| --- | --- | --- |
| API | `app/main.py`, `app/routers/chat.py`, `app/schemas.py` | Komposisi, CORS, validasi Pydantic, serialisasi, HTTP status dan error envelope. |
| Application | `app/services/chat_service.py` | Orkestrasi satu giliran, pemetaan intent ke kontrak publik, respons aman, dan handoff. |
| AI | `app/ai/intent.py`, `app/ai/text.py`, `app/ai/guardrails.py` | Kontrak classifier, normalisasi, fallback aturan, dan pemeriksaan permintaan sensitif. |
| AI integration | `app/ai/generation.py` | Kontrak provider dan retrieval serta pemisahan peran prompt. |
| Data integration | `app/integrations/catalog.py` | Kontrak baca katalog publik dan validasi harga serta ketersediaan. |
| Configuration | `app/core/config.py` | Pengaturan lingkungan, ambang confidence, dan timeout. |

Router bergantung pada layanan aplikasi. Layanan bergantung pada kontrak Python dan aturan domain. Adapter dapat dipasang di `ChatService` melalui komposisi di `create_app`. Kode AI dan aplikasi tidak mengimpor FastAPI.

## Request Flow

1. FastAPI memvalidasi `session_id` dan `message`. Pesan dibatasi 1.000 karakter. `session_id` tetap diterima untuk kompatibilitas.
2. Guardrail memeriksa permintaan informasi internal dan pola pengambilalihan instruksi sebelum memanggil classifier atau adapter.
3. Classifier dipakai ulang dan berjalan dalam worker thread agar inferensi sinkron tidak menahan event loop. Prediksi model dengan confidence rendah meminta klarifikasi. Fallback aturan memakai confidence `None`.
4. Harga dan stok berasal dari `CatalogReader` jika tersedia. Harga memakai rupiah per kilogram. Nilai yang belum diketahui mendapat respons keterbatasan dan handoff. Katalog membedakan stok habis dari stok yang belum diketahui.
5. Pertanyaan produk dapat memakai `KnowledgeRetriever` untuk memilih ID fakta yang telah disetujui. Output `GenerationProvider` dipakai jika menunjuk salah satu ID yang tersedia. Teks yang dikirim ke pelanggan berasal dari daftar terverifikasi.
6. Pemesanan dan keluhan mengembalikan petunjuk WhatsApp. Integrasi Full-stack bertanggung jawab atas tautan Click-to-Chat yang disetujui UMKM.
7. Layanan mengembalikan satu `ChatResult`. Router mempertahankan tiga nilai intent publik API v1.

## Decisions and Failure Handling

- Default lokal berjalan dengan aturan dan jawaban terverifikasi tanpa koneksi luar. Adapter katalog, retrieval, dan generasi bersifat opsional dan dapat diuji dengan test doubles.
- Adapter opsional mendapat satu percobaan dengan timeout per panggilan. Jalur produk dapat memanggil retrieval dan generasi secara berurutan. Timeout, kuota, dan kegagalan memakai respons lokal. Kegagalan layanan inti memakai HTTP `503` lama dengan pesan yang disanitasi.
- Teks pengguna dan output adapter diperlakukan sebagai data. Aplikasi menyimpan nol riwayat serta mencatat nama komponen dan jenis error tanpa menyertakan isi pesan, ID sesi, atau detail exception. Adapter eksternal juga perlu menjaga batas ini di konfigurasi HTTP dan logging.
- CORS default mengikuti API awal. Untuk deployment, gunakan origin Full-stack yang disepakati. Aktifkan credentials jika diperlukan oleh integrasi.
- Fallback aturan memiliki cakupan terbatas pada parafrasa, intent ambigu, dan konteks percakapan. Evaluasi sintetis memeriksa contoh tertentu. Data baru dan pengujian UMKM diperlukan untuk mengukur cakupan.

## Integration Path

1. **Intent model.** Sepakati label dan kamus data dengan Data Science. Pisahkan data berdasarkan percakapan atau pelanggan jika tersedia, periksa duplikat dan distribusi kelas, lalu evaluasi kedua baseline di split yang sama. Gunakan split validasi untuk tuning dan kalibrasi ambang. Simpan artefak tepercaya dengan metadata versi dan inisialisasi sekali per proses. Pasang adapter `IntentClassifier` untuk inferensi.
2. **Catalog.** Sepakati endpoint baca, autentikasi server, satuan, status kosong, dan batas usia data dengan Full-stack. Validasi payload dan tolak data kedaluwarsa di adapter sebelum mengembalikan snapshot.
3. **Provider and RAG.** Pilih provider setelah menyepakati akses, kuota, dan kebijakan data. Ingest FAQ berizin, validasi dan bersihkan isi, lalu bagi dokumen menjadi chunk. Bandingkan embedding Bahasa Indonesia dan uji retrieval dengan pertanyaan berlabel. Pilih FAISS, ChromaDB, atau alternatif setelah pengukuran. Petakan hasil retrieval ke ID fakta terverifikasi untuk prompt. Evaluasi relevansi retrieval, ketepatan jawaban, guardrail, dan latensi. Harga dan stok tetap dibaca dari katalog.
4. **Conversation context and serving.** Jika konteks dibutuhkan, sepakati batas giliran, kedaluwarsa, pemisahan sesi, dan retensi. Sebelum publikasi, siapkan rate limit dan batas request di gateway, pemantauan latensi dan error, pengujian akses backend Full-stack, dan UAT.
