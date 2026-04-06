# Dokumen Teknis Infrastruktur — DENAI
**PT Semen Indonesia Group | Enterprise HR AI Chatbot**
*Disusun untuk keperluan pengambilan keputusan infrastruktur.*

---

## 1. Prosedur Deployment di VPS (DigitalOcean Ubuntu 24.04)

### A. Akses Server
```bash
ssh root@152.42.252.61
```

### B. Instalasi Dependensi Sistem
```bash
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip nginx git certbot python3-certbot-nginx
```

### C. Upload Project ke Server
```bash
mkdir -p /var/www/denai
cd /var/www/denai

# Via Git:
git clone <repo-url> .

# Via SCP (dari laptop):
# scp -r /path/to/project root@152.42.252.61:/var/www/denai
```

### D. Instalasi Library Python
```bash
cd /var/www/denai
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### E. Konfigurasi Environment (.env)
```bash
nano /var/www/denai/.env
```
```env
ENVIRONMENT=production

OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX=...
COHERE_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_CONNECTION_STRING=...
UPSTASH_REDIS_URL=...
UPSTASH_REDIS_TOKEN=...
ELEVENLABS_API_KEY=...
GOOGLE_MAPS_API_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...

ALLOWED_ORIGINS=https://denai.online
```

### F. Instalasi dan Konfigurasi PM2 (Auto-Start)
```bash
# Install Node.js dan PM2
apt install -y nodejs npm
npm install -g pm2

# Masuk ke folder project dan aktifkan virtual environment
cd /var/www/denai
source venv/bin/activate

# Jalankan DENAI via PM2
pm2 start "venv/bin/gunicorn backend.main:app \
  --workers 3 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --timeout 120 \
  --graceful-timeout 30" \
  --name denai \
  --cwd /var/www/denai

# Simpan konfigurasi PM2 dan aktifkan auto-start saat server reboot
pm2 startup
# Jalankan perintah yang muncul dari output pm2 startup (biasanya dimulai dengan sudo env ...)
pm2 save

# Setup log rotation — wajib agar log tidak memenuhi disk server
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 50M    # rotate jika log mencapai 50MB
pm2 set pm2-logrotate:retain 7        # simpan log 7 hari terakhir
pm2 set pm2-logrotate:compress true   # kompres log lama
```

Perintah PM2 yang sering digunakan:
```bash
pm2 status              # lihat status semua proses
pm2 logs denai          # lihat log aplikasi secara live
pm2 restart denai       # restart aplikasi
pm2 stop denai          # hentikan aplikasi
pm2 delete denai        # hapus proses dari PM2
pm2 monit               # monitor CPU dan RAM secara real-time
```

### G. Konfigurasi Nginx
```bash
nano /etc/nginx/sites-available/denai
```
```nginx
server {
    listen 80;
    server_name denai.online www.denai.online;

    # Batas ukuran upload — wajib untuk fitur Call Mode (audio upload)
    # Default Nginx hanya 1MB, audio bisa sampai 5–10MB
    client_max_body_size 20m;

    root /var/www/denai/web;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # SSE Streaming (diperlukan untuk fitur chat real-time)
    location ~ ^/(ask|call|speech|sessions|history) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
        proxy_buffering off;
        proxy_cache off;
    }
}
```
```bash
ln -s /etc/nginx/sites-available/denai /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### H. SSL/HTTPS
```bash
certbot --nginx -d denai.online -d www.denai.online
```

### I. Firewall
```bash
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable
# Port 8000 tidak dibuka ke publik — hanya dapat diakses oleh Nginx secara internal
```

### J. Verifikasi
```bash
pm2 status                    # DENAI harus: online
systemctl status nginx        # harus: active (running)
curl http://127.0.0.1:8000/   # harus: return JSON status DENAI
```

---

## 2. Daftar Program yang Dibutuhkan di Server

| Program | Fungsi |
|---|---|
| Python 3.11 | Runtime aplikasi backend DENAI |
| pip + venv | Manajemen library Python |
| Gunicorn + Uvicorn | Web server dan process manager |
| Nginx | Reverse proxy dan penyaji frontend |
| Certbot | Pengelolaan SSL/HTTPS otomatis |
| PM2 | Pengelolaan proses dan auto-restart aplikasi |
| Node.js + npm | Diperlukan untuk instalasi PM2 |
| ufw | Firewall keamanan port server |
| Git | Pengelolaan dan pembaruan kode |
| Docker | Diperlukan apabila layanan self-host dijalankan |

---

## 3. Kapasitas Sistem — Workers, Pengguna, dan Spesifikasi Server

### Cara Kerja Kapasitas

Aplikasi DENAI menggunakan arsitektur **asynchronous** (non-blocking). Artinya, satu worker tidak hanya melayani satu pengguna dalam satu waktu — ia dapat menangani banyak permintaan secara bersamaan selama menunggu respons dari layanan eksternal (OpenAI, database, dsb).

Setiap pertanyaan staff membutuhkan waktu proses **±5–15 detik** (tergantung kompleksitas). Selama waktu tunggu tersebut, worker yang sama melayani pengguna lain secara paralel.

---

### Tabel Kapasitas: Workers → Pengguna → Spesifikasi Server

| Jumlah Workers | Pengguna Aktif Bersamaan | Total Staff yang Dapat Dilayani | CPU yang Dibutuhkan | RAM yang Dibutuhkan |
|---|---|---|---|---|
| 3 workers | ±30–50 pengguna | hingga 500 staff | 4 core | 8 GB |
| 5 workers | ±80–120 pengguna | hingga 1.000 staff | 8 core | 16 GB |
| 9 workers | ±200–300 pengguna | hingga 3.000 staff | 16 core | 32 GB |
| 17 workers | ±500+ pengguna | hingga 5.000+ staff | 32 core | 64 GB |

> **Catatan:** "Pengguna aktif bersamaan" adalah jumlah staff yang mengirim pesan pada detik yang sama.
> Dari total 1.000 staff, estimasi yang aktif bersamaan di jam sibuk adalah 50–100 orang.
> Angka workers dapat disesuaikan di file konfigurasi server tanpa perubahan kode aplikasi.

---

### Penentuan Jumlah Workers Berdasarkan Spesifikasi Server

```
Rumus : Workers = (2 × jumlah CPU core) + 1

Contoh:
  Server  4 core  →  9 workers  → cukup untuk 1.000 staff
  Server  8 core  → 17 workers  → cukup untuk 2.000–3.000 staff
  Server 16 core  → 33 workers  → cukup untuk 5.000+ staff
```

---

### Spesifikasi Server Fisik (On-Premise)

Berikut adalah kebutuhan spesifikasi hardware server fisik untuk menjalankan aplikasi DENAI beserta seluruh layanan pendukung di lingkungan internal perusahaan.

---

### Dasar Perhitungan Kebutuhan

| Komponen yang Berjalan di Server | Kebutuhan CPU | Kebutuhan RAM | Kebutuhan Storage |
|---|---|---|---|
| DENAI Backend (aplikasi utama) | 2 core | 2 GB | 10 GB |
| PostgreSQL / Supabase (database HR) | 2 core | 4 GB | 100 GB SSD |
| Qdrant (vector database dokumen SOP) | 1 core | 2 GB | 50 GB SSD |
| Redis (cache percakapan) | 1 core | 1 GB | 5 GB |
| Langfuse (log & audit AI) | 1 core | 2 GB | 50 GB SSD |
| Nginx (web server) | 1 core | 512 MB | — |
| Sistem operasi + buffer | — | 2 GB | 50 GB |
| **Total kebutuhan** | **8 core** | **±13.5 GB** | **±265 GB** |

---

### Spesifikasi Minimum

Spesifikasi ini mencukupi untuk menjalankan DENAI dengan kapasitas hingga **±100 pengguna aktif bersamaan** (estimasi kebutuhan 1.000 staff).

| Komponen | Spesifikasi Minimum |
|---|---|
| **Prosesor (CPU)** | 8 core / 16 thread, clock speed ≥ 2.5 GHz |
| **RAM** | 16 GB DDR4 |
| **Storage Utama (OS + Aplikasi)** | 256 GB SSD |
| **Storage Data (Database)** | 500 GB SSD *(terpisah dari OS)* |
| **Jaringan** | 1 Gbps LAN, akses internet ≥ 50 Mbps |
| **Sistem Operasi** | Ubuntu Server 22.04 LTS atau 24.04 LTS (64-bit) |
| **Catu Daya** | Redundant PSU (disarankan) |

---

### Spesifikasi yang Lebih Luas

Spesifikasi ini memberikan ruang untuk pertumbuhan pengguna dan penambahan fitur tanpa perlu penggantian hardware dalam jangka pendek.

| Komponen | Spesifikasi Lebih Luas |
|---|---|
| **Prosesor (CPU)** | 16 core / 32 thread, clock speed ≥ 3.0 GHz |
| **RAM** | 32 GB DDR4 ECC |
| **Storage Utama (OS + Aplikasi)** | 512 GB NVMe SSD |
| **Storage Data (Database)** | 2 TB SSD *(terpisah, RAID 1)* |
| **Jaringan** | 10 Gbps LAN, akses internet ≥ 100 Mbps |
| **Sistem Operasi** | Ubuntu Server 24.04 LTS (64-bit) |
| **Catu Daya** | Redundant PSU |
| **Backup** | Storage tambahan atau NAS untuk backup berkala |

---

## 4. Kemampuan AI — Fitur Aktif dan Potensi Pengembangan

### Fitur yang Aktif Saat Ini

| Fitur | Cara Kerja | Pengguna yang Dapat Mengakses |
|---|---|---|
| **Tanya-jawab SOP & Kebijakan** | AI mencari jawaban dari dokumen SOP perusahaan yang telah diunggah | Semua staff |
| **Analitik Data HR** | AI mengubah pertanyaan bahasa natural menjadi query database, mengeksekusi ke database HR, dan menyajikan hasilnya dalam bentuk teks, tabel, dan grafik | Role HR / Admin / Manager |
| **Voice Call Mode** | Staff dapat berbicara langsung ke aplikasi; AI memproses suara, menjawab, dan merespons dengan suara | Semua staff |
| **Streaming Real-time** | Jawaban AI muncul kata per kata secara langsung tanpa menunggu jawaban selesai | Semua staff |
| **Riwayat Percakapan** | Setiap sesi percakapan tersimpan dan dapat dilanjutkan kapan saja | Semua staff |
| **Multi-sesi** | Setiap staff dapat memiliki beberapa sesi percakapan berbeda sekaligus | Semua staff |

---

### Kemampuan Analitik Database yang Sudah Ada

DENAI dapat mengakses dan menganalisis database HR secara langsung melalui percakapan bahasa natural. Tidak diperlukan pengetahuan teknis dari pengguna.

| Kategori | Contoh Pertanyaan yang Dapat Dijawab |
|---|---|
| **Distribusi karyawan** | "Berapa jumlah karyawan per divisi?" |
| **Struktur jabatan** | "Berapa jumlah karyawan di setiap grade atau band?" |
| **Agregasi & statistik** | "Berapa rata-rata masa kerja karyawan per departemen?" |
| **Filter & pencarian** | "Tampilkan daftar karyawan yang bergabung tahun ini" |
| **Visualisasi data** | Hasil ditampilkan dalam grafik batang, pie chart, line chart, dan tabel interaktif yang dapat diurutkan |

Seluruh akses database dilindungi oleh lapisan keamanan yang hanya mengizinkan operasi **baca (SELECT)**. Tidak ada data yang dapat diubah atau dihapus melalui chatbot.

---

### Fitur yang Dapat Dikembangkan

| Fitur | Keterangan |
|---|---|
| **Penambahan dokumen SOP** | Dokumen kebijakan baru dapat diunggah dan langsung tersedia untuk AI tanpa perubahan kode |
| **Akses analitik untuk role tambahan** | Fitur analitik database dapat dibuka untuk role lain seperti Manager atau Direktur |
| **Ringkasan dokumen otomatis** | AI meringkas dokumen panjang menjadi poin-poin utama |
| **Laporan berkala otomatis** | Sistem dijadwalkan menghasilkan laporan HR rutin (harian / mingguan / bulanan) |
| **Notifikasi proaktif** | Integrasi dengan email atau WhatsApp untuk mengirimkan informasi kebijakan terbaru ke karyawan |
| **Dashboard penggunaan internal** | Statistik penggunaan chatbot: jumlah pertanyaan per hari, topik yang paling sering ditanyakan, tingkat kepuasan pengguna |
| **Integrasi sistem HR existing** | DENAI dapat dihubungkan ke sistem HRIS yang sudah ada (SAP, Oracle HCM, dll) |
| **Multi-entitas** | Sistem dapat dikonfigurasi untuk melayani lebih dari satu entitas dalam grup dengan pemisahan data yang ketat |
| **Audit trail lengkap** | Seluruh percakapan, query database, dan aksi AI tercatat otomatis untuk keperluan audit dan compliance |

---

## 5. Layanan Eksternal yang Digunakan

Aplikasi DENAI saat ini bergantung pada delapan layanan pihak ketiga. Berikut adalah rincian fungsi, status ketersediaan versi lokal, serta informasi biaya masing-masing layanan.

---

### Layanan yang Tersedia Versi Lokal (Dapat Diinstal di Server Sendiri)

---

#### Redis
| | |
|---|---|
| **Fungsi di DENAI** | Menyimpan cache history percakapan selama 24 jam |
| **Kondisi saat ini** | Menggunakan Upstash (cloud) |
| **Versi lokal** | Tersedia — Redis adalah software open source |
| **Biaya versi cloud** | $0–10/bulan |
| **Biaya versi lokal** | $0 (berjalan di dalam server yang sudah ada) |
| **Kebutuhan RAM** | ±50–100 MB |
| **Estimasi waktu setup** | 30 menit |

Prosedur instalasi versi lokal:
```bash
apt install -y redis-server
nano /etc/redis/redis.conf
# Pastikan dua baris berikut aktif:
#   bind 127.0.0.1
#   requirepass PASSWORD_KUAT

systemctl restart redis-server
systemctl enable redis-server
redis-cli ping  # jawaban yang diharapkan: PONG
```

Perubahan konfigurasi `.env` apabila beralih ke Redis lokal:
```env
UPSTASH_REDIS_URL=
UPSTASH_REDIS_TOKEN=
REDIS_URL=redis://:PASSWORD_KUAT@127.0.0.1:6379
```

---

#### Supabase
| | |
|---|---|
| **Fungsi di DENAI** | Menyimpan data HR karyawan dan history percakapan secara permanen |
| **Kondisi saat ini** | Menggunakan Supabase cloud |
| **Versi lokal** | Tersedia — Supabase memiliki versi self-host resmi berbasis Docker |
| **Biaya versi cloud** | $25/bulan (Pro) |
| **Biaya versi lokal** | $0 (berjalan di dalam server yang dialokasikan) |
| **Kebutuhan RAM** | ±1–1.5 GB |
| **Estimasi waktu setup** | 1–2 jam |

Prosedur instalasi versi lokal:
```bash
apt install -y docker.io docker-compose-plugin
systemctl enable docker && systemctl start docker

git clone --depth 1 https://github.com/supabase/supabase /opt/supabase
cd /opt/supabase/docker
cp .env.example .env
nano .env
# Isi: POSTGRES_PASSWORD, JWT_SECRET, ANON_KEY, SERVICE_ROLE_KEY

docker compose up -d
# Dashboard dapat diakses di: http://IP_SERVER:3000
```

Perubahan konfigurasi `.env` apabila beralih ke Supabase lokal:
```env
SUPABASE_URL=http://127.0.0.1:8000
SUPABASE_ANON_KEY=ANON_KEY_DARI_SUPABASE_LOKAL
SUPABASE_CONNECTION_STRING=postgresql://postgres:PASSWORD@127.0.0.1:5432/postgres
```

---

#### Qdrant *(sebagai pengganti Pinecone)*
| | |
|---|---|
| **Fungsi di DENAI** | Menyimpan embedding dokumen SOP untuk pencarian semantik |
| **Kondisi saat ini** | Menggunakan Pinecone (cloud) |
| **Status Pinecone** | Tidak tersedia versi lokal — cloud-only |
| **Alternatif lokal** | Qdrant — software open source dengan fungsi identik |
| **Biaya Pinecone** | $70/bulan (Starter) |
| **Biaya Qdrant lokal** | $0 (berjalan di dalam server yang dialokasikan) |
| **Kebutuhan RAM** | ±200–400 MB |
| **Estimasi waktu setup** | 1 jam + 3–4 jam penyesuaian kode aplikasi |

Prosedur instalasi Qdrant:
```bash
docker run -d \
  --name qdrant \
  --restart always \
  -p 127.0.0.1:6333:6333 \
  -v /var/lib/qdrant:/qdrant/storage \
  qdrant/qdrant

curl http://127.0.0.1:6333/healthz  # jawaban: {"title":"qdrant"}
```

Perubahan konfigurasi `.env` apabila beralih ke Qdrant:
```env
PINECONE_API_KEY=
PINECONE_INDEX=
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=sop_documents
```

> Perpindahan dari Pinecone ke Qdrant memerlukan penyesuaian kode pada bagian RAG engine.
> Seluruh data dokumen SOP yang ada di Pinecone dapat dipindahkan ke Qdrant melalui
> script migrasi. Estimasi waktu pengerjaan: 3–4 jam.

---

#### Langfuse
| | |
|---|---|
| **Fungsi di DENAI** | Mencatat log percakapan AI, tracing, dan skor evaluasi untuk audit |
| **Kondisi saat ini** | Menggunakan Langfuse cloud |
| **Versi lokal** | Tersedia — Langfuse memiliki versi self-host resmi berbasis Docker |
| **Biaya versi cloud** | $0–59/bulan |
| **Biaya versi lokal** | $0 (berjalan di dalam server yang dialokasikan) |
| **Kebutuhan RAM** | ±500 MB – 1 GB |
| **Estimasi waktu setup** | 1–2 jam |

Prosedur instalasi versi lokal:
```bash
git clone https://github.com/langfuse/langfuse.git /opt/langfuse
cd /opt/langfuse
cp .env.example .env
nano .env
# Isi: DATABASE_URL, NEXTAUTH_SECRET, SALT, NEXTAUTH_URL

docker compose up -d
# Dashboard dapat diakses di: http://IP_SERVER:3000
```

Perubahan konfigurasi `.env` apabila beralih ke Langfuse lokal:
```env
LANGFUSE_BASE_URL=http://127.0.0.1:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

---

### Layanan yang Tidak Tersedia Versi Lokal (Tetap Cloud)

Layanan berikut adalah produk proprietary. Tidak tersedia versi yang dapat diinstal di server sendiri. Layanan ini tetap diakses melalui internet.

---

#### OpenAI
| | |
|---|---|
| **Fungsi di DENAI** | Model bahasa utama (GPT-4o-mini), Speech-to-Text (Whisper), pembuatan embedding dokumen SOP |
| **Status** | Tidak tersedia versi lokal — tetap menggunakan layanan cloud |
| **Biaya** | ±$20–50/bulan tergantung volume penggunaan |
| **Kebijakan data** | Berdasarkan Terms of Service OpenAI: data yang dikirim melalui API tidak digunakan untuk pelatihan model dan dihapus dalam 30 hari |

---

#### Cohere
| | |
|---|---|
| **Fungsi di DENAI** | Mengurutkan hasil pencarian dokumen SOP berdasarkan relevansi |
| **Status** | Tidak tersedia versi lokal — tetap menggunakan layanan cloud |
| **Biaya** | $0–20/bulan |

---

#### ElevenLabs
| | |
|---|---|
| **Fungsi di DENAI** | Text-to-Speech Bahasa Indonesia untuk fitur voice pada jawaban AI |
| **Status** | Tidak tersedia versi lokal — tetap menggunakan layanan cloud |
| **Biaya** | $5–22/bulan |

---

#### Google Maps API
| | |
|---|---|
| **Fungsi di DENAI** | Perhitungan jarak antar kota untuk penentuan kategori perjalanan dinas |
| **Status** | Tidak tersedia versi lokal — tetap menggunakan layanan cloud |
| **Biaya** | ±$0–5/bulan tergantung volume |

---

### Ringkasan Biaya Operasional Layanan Eksternal

| Layanan | Status | Biaya/bulan |
|---|---|---|
| OpenAI | Wajib cloud | $20–50 |
| ElevenLabs | Wajib cloud | $5–22 |
| Cohere | Wajib cloud | $0–20 |
| Google Maps | Wajib cloud | $0–5 |
| Supabase | Dapat dilokalisasi | $25 (cloud) / $0 (lokal) |
| Upstash Redis | Dapat dilokalisasi | $0–10 (cloud) / $0 (lokal) |
| Pinecone | Dapat diganti Qdrant (lokal) | $70 (cloud) / $0 (lokal) |
| Langfuse | Dapat dilokalisasi | $0–59 (cloud) / $0 (lokal) |
| **Total jika semua cloud** | | **$120–261/bulan** |
| **Total jika Supabase/Redis/Pinecone/Langfuse lokal** | | **$25–97/bulan** |

---

### Kebutuhan RAM apabila Supabase, Redis, Qdrant, dan Langfuse Dijalankan Lokal

| Komponen | Kebutuhan RAM |
|---|---|
| DENAI Backend (3 workers) | ±1.2 GB |
| Redis | ±100 MB |
| Qdrant | ±400 MB |
| Supabase (Docker stack) | ±1.5 GB |
| Langfuse | ±800 MB |
| Sistem operasi + Nginx | ±300 MB |
| **Total** | **±4.3 GB** |

Menjalankan keempat layanan tersebut secara lokal memerlukan server dengan RAM minimal 8 GB.

---

### Pilihan Arsitektur

Catatan: OpenAI, Cohere, ElevenLabs, dan Google Maps pada ketiga opsi di bawah
selalu tetap menggunakan layanan cloud karena tidak tersedia versi lokal.

---

**Opsi A — Semua Layanan Data di Cloud**
```
Server         : 1 server (spesifikasi minimum)
  └── DENAI Backend + Nginx

Layanan cloud  : Supabase + Pinecone + Upstash Redis + Langfuse
               + OpenAI + Cohere + ElevenLabs + Google Maps

Biaya server   : sesuai harga server yang diadakan
Biaya layanan  : ±$120–261/bulan
Data di server : Tidak ada — seluruh data tersimpan di vendor cloud
```

---

**Opsi B — Sebagian Data di Server**
```
Server         : 1 server (spesifikasi minimum, RAM ≥ 8 GB)
  └── DENAI Backend + Nginx + Redis + Qdrant

Layanan cloud  : Supabase Cloud + Langfuse Cloud
               + OpenAI + Cohere + ElevenLabs + Google Maps

Biaya server   : sesuai harga server yang diadakan
Biaya layanan  : ±$45–95/bulan
Data di server : Cache percakapan, dokumen SOP
Data di cloud  : Data HR karyawan, log AI
```

---

**Opsi C — Maksimal Data di Server**
```
Server 1       : Aplikasi (RAM ≥ 8 GB)
  └── DENAI Backend + Nginx

Server 2       : Database (RAM ≥ 16 GB)
  └── Supabase + Redis + Qdrant + Langfuse

Layanan cloud  : OpenAI + Cohere + ElevenLabs + Google Maps

Biaya server   : sesuai harga server yang diadakan (2 unit)
Biaya layanan  : ±$25–97/bulan
Data di server : Data HR karyawan, percakapan, dokumen SOP, log AI
Data di cloud  : Teks pertanyaan melewati OpenAI API (tidak disimpan permanen)
```

---

## Ringkasan

| Aspek | Kondisi Saat Ini |
|---|---|
| Server | 1 vCPU / 2 GB RAM — DigitalOcean SGP1 |
| Arsitektur backend | Gunicorn 3 workers + Nginx + systemd |
| Keamanan | HTTPS + Firewall + Rate Limiting per IP |
| Kapasitas | ±30–50 pengguna aktif bersamaan |
| Layanan yang dapat dilokalisasi | Redis, Supabase, Qdrant (pengganti Pinecone), Langfuse |
| Layanan yang tidak dapat dilokalisasi | OpenAI, Cohere, ElevenLabs, Google Maps |
| Penyimpanan kredensial | Seluruh API key tersimpan di file `.env` — tidak tercatat di kode |
| Potensi penghematan biaya jika self-host penuh | $95–164/bulan |
