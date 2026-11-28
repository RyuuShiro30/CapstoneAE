# CapstoneAE

Layanan chatbot pelanggan untuk **Gurami Konsumsi Mang Ujang**, dikembangkan oleh tim **A26-CS181** pada Asah 2026 bersama Dicoding dan GoTo.

## Business Problem and AI Objective

Calon pembeli sering perlu menghubungi pengelola untuk mengetahui produk, harga, dan ketersediaan. Chatbot membantu pembeli rumahan, pelanggan acara keluarga, dan pelaku kuliner menemukan informasi gurame konsumsi. Target model intent adalah mengarahkan pertanyaan pelanggan ke jalur yang tepat, termasuk konfirmasi pesanan dan keluhan melalui WhatsApp. Manfaat yang dituju adalah akses informasi yang lebih cepat dan berkurangnya pertanyaan berulang kepada pengelola.

## Foundation Status

- FastAPI mengarahkan request ke layanan chatbot dengan classifier berbasis aturan, pemeriksaan permintaan sensitif, jawaban Bahasa Indonesia, dan handoff WhatsApp.
- Produk yang terverifikasi adalah gurame konsumsi berukuran besar, dijual per kilogram. Harga, stok, ongkir, jam operasional, alamat, promosi, dan ketentuan terkini memerlukan sumber yang disetujui. Jalur pemesanan meminta pelanggan mengonfirmasi jumlah dan opsi COD atau ambil langsung dengan pengelola.
- Classifier, katalog, retrieval, dan provider dapat dipasang melalui dependency injection. Default berjalan tanpa kredensial eksternal. Histori, model terlatih, katalog aktual, provider proprietary dan RAG aktif masuk tahap berikutnya.

Lihat [Chatbot Architecture](docs/architecture.md) dan [API Contract](docs/api-contract.md).

## Stack and Project Structure

Python 3.11+, FastAPI, Pydantic, Uvicorn, pytest, dan scikit-learn untuk evaluasi offline opsional. Tes diverifikasi pada Python 3.11 dan 3.13.

~~~text
app/
  main.py                   Application composition and health check
  schemas.py                Existing request and response schemas
  routers/chat.py           HTTP adapter
  core/config.py            Environment settings
  services/chat_service.py  Intent routing, response and handoff
  ai/                       Intent, normalization, prompts and guardrails
  integrations/catalog.py   Public product read contract
docs/                       Architecture and API contract
evaluations/datasets/       Synthetic foundation cases
scripts/                    Chat smoke evaluation and model comparison
tests/                      Unit and API integration tests
~~~

## Local Setup

Jalankan dari root repo di PowerShell.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
~~~

Pada Linux/macOS gunakan `.venv/bin/python`. Server lokal memakai `http://127.0.0.1:8000` dan Swagger tersedia di `/docs`.

~~~powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/chat -ContentType 'application/json' -Body '{"session_id":"demo-001","message":"Mau pesan gurame 2 kilogram"}'
~~~

### Environment

Pengaturan dibaca saat aplikasi dibuat. Untuk memakai file lokal, salin `.env.example` menjadi `.env` dan tambahkan `--env-file .env` saat menjalankan Uvicorn.

| Environment variable | Default | Meaning |
| --- | --- | --- |
| `CHAT_CORS_ORIGINS` | `*` | Daftar origin dipisah koma. Untuk deployment, isi origin frontend yang disepakati. |
| `CHAT_CORS_ALLOW_CREDENTIALS` | `true` | Default kompatibilitas. Gunakan `false` jika frontend tidak membutuhkan credentials lintas origin. |
| `CHAT_INTENT_MIN_CONFIDENCE` | `0.60` | Ambang classifier yang melaporkan confidence. |
| `CHAT_EXTERNAL_TIMEOUT_SECONDS` | `2.0` | Timeout tiap panggilan adapter opsional. |

## Tests and Evaluation

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.evaluate_chat
.\.venv\Scripts\python.exe -m ruff check --select E,F,I --ignore E501 app scripts tests
.\.venv\Scripts\python.exe -m ruff format --check app scripts tests
~~~

Evaluasi lokal melewati **24/24 skenario sintetis**, terdiri dari **8/8** pertanyaan layanan, **12/12** pertanyaan luar topik yang ditolak dengan sopan, dan **4/4** permintaan internal atau pengambilalihan instruksi yang ditolak. Suite API menyimulasikan timeout, kuota, dan kegagalan provider. Skrip smoke mencatat latensi lokal per eksekusi. Hasil ini mengukur perilaku fondasi pada kasus yang diketahui.

### Intent Model Comparison

Gunakan split CSV UTF-8 berkolom `text,intent` setelah data dan label ditinjau oleh Data Science. Intent kandidat didefinisikan di `app/ai/intent.py`. Simpan data privat di lokasi yang dikecualikan dari Git, misalnya `data/raw/`. Pisahkan kelompok percakapan saat membuat split jika tersedia.

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-eval.txt
.\.venv\Scripts\python.exe -m scripts.evaluate_intent --train data/raw/train.csv --test data/raw/test.csv
~~~

Runner menolak pesan yang duplikat setelah normalisasi dan menghitung distribusi kelas. TF-IDF + Logistic Regression dan TF-IDF + Linear SVM dilatih pada train saja dan memakai holdout yang sama. Output berisi akurasi, precision, recall, F1, confusion matrix, dan rata-rata waktu inferensi. Metrik utama yang diusulkan adalah macro F1, dengan kesalahan per kelas, latensi, dan kompleksitas sebagai pertimbangan. Hasil resmi dan pemilihan model menunggu data tim.

## Data and Resource Attribution

| Source | Purpose and limitation |
| --- | --- |
| Interview dan Use Case UMKM, A26-CS181. Dokumen tim, 23 Oktober 2026. | Sumber primer kebutuhan bisnis dan batas Click-to-Chat. Harga historis dan data kontak internal dikecualikan dari jawaban dan file repo. |
| Checklist Tech Stack Asah 2026, kolom Gen AI, hlm. 1–2. | Acuan penilaian Main Quest dan Side Quest. |
| [Foundation case dataset](evaluations/datasets/foundation_cases.csv) | Contoh sintetis untuk pengujian perilaku dan guardrail. Dataset ini dibatasi untuk pengujian fondasi. |
| Dataset Data Science dan katalog Full-stack | Menunggu penyerahan data dan kontrak. |
| Runtime | API, validasi, dan serving ASGI. [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), [Uvicorn](https://www.uvicorn.org/) |
| Tooling | Evaluasi, komunikasi HTTP in-process, pengujian async, lint, dan format. [scikit-learn](https://scikit-learn.org/stable/), [HTTPX](https://www.python-httpx.org/), [AnyIO](https://anyio.readthedocs.io/), [pytest](https://docs.pytest.org/), [Ruff](https://docs.astral.sh/ruff/) |

## Asah 2026 Checklist

| Main Quest | Status | Evidence or dependency |
| --- | --- | --- |
| MQ-01 Problem definition | DONE | Masalah, pengguna, tujuan model, dan manfaat tercatat di README. |
| MQ-02 Dedicated AI model | BLOCKED | Kontrak classifier dan fallback tersedia. Pelatihan menunggu data dan label dari Data Science. |
| MQ-03 Data preprocessing | PARTIAL | Normalisasi dan pipeline TF-IDF tersedia. Verifikasi pada data proyek belum dilakukan. |
| MQ-04 Attribution | DONE | Sumber, jenis data, dan batas penggunaan tahap ini didokumentasikan. |
| MQ-05 Proprietary model API | SCAFFOLDED | Kontrak provider dan guardrail diuji lewat mock. Menunggu vendor, kebijakan data, dan kredensial. |
| MQ-06 Model comparison | SCAFFOLDED | Runner dua model tersedia. Hasil resmi dan pemilihan model menunggu dataset. |
| MQ-07 REST serving | PARTIAL | Endpoint dan Swagger lulus uji lokal. Model terlatih, deployment dan akses backend Full-stack belum diverifikasi. |

| Relevant Side Quest | Status | Evidence or dependency |
| --- | --- | --- |
| Distribusi kelas, imbalance, tuning, dan data uji | SCAFFOLDED | Runner memakai split terpisah dan melaporkan distribusi. Penanganan imbalance dan tuning mengikuti analisis data. |
| Empat atau lebih intent dengan routing | PARTIAL | Delapan jalur internal dalam fallback. Model terlatih dan label final menunggu Data Science. |
| Embedding, vector database, dan RAG | SCAFFOLDED | Titik integrasi retrieval dan desain pipeline tersedia. Pemilihan embedding dan index masuk tahap berikutnya. |
| Prompt terstruktur dan few-shot | DONE | Prompt memisahkan data pengguna dari instruksi dan memuat contoh terkontrol. |
| Penolakan di luar konteks | DONE | 12/12 kasus sintetis ditolak pada evaluasi lokal. |
| Error input, timeout, kuota, dan API docs | DONE | Lulus tes lokal, termasuk simulasi provider. Swagger tersedia. |
| Kontrak dengan Full-stack dan kanal UMKM | PARTIAL | Kontrak v1 dan flag Click-to-Chat tersedia. Verifikasi tim dan tautan aktif menunggu integrasi. |
| Model pendukung dan model generatif lokal | NOT STARTED | Opsional jika kebutuhan dan sumber dayanya disepakati. |

## Roadmap

1. Finalisasi label dan split Data Science. Jalankan perbandingan, tinjau error per kelas, kalibrasi ambang, lalu pasang model.
2. Sepakati katalog baca, tujuan Click-to-Chat, origin, dan contoh error bersama Full-stack.
3. Pasang provider proprietary dan pipeline retrieval. Ukur kualitas, relevansi, biaya, latensi, dan ketahanan guardrail.
4. Siapkan deployment, monitoring, akses dari backend Full-stack, dan UAT dengan UMKM.

Risiko utama adalah cakupan aturan terhadap parafrasa, schema error Swagger yang berbeda dari runtime sejak baseline, serta ketiadaan sumber resmi untuk memverifikasi harga dan stok saat ini.

## Contributors and AI Disclosure

Tim A26-CS181. Fondasi chatbot dikerjakan untuk bagian AI Engineer, Muhammad Enzi Herwi, dengan bantuan Codex untuk audit, implementasi, dokumentasi, dan pengujian. Kontrak integrasi dan kesiapan deployment perlu ditinjau bersama tim.
