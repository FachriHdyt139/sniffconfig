<div align="center">

# 🐴 SNIFF CONFIG

**Web + Bot Telegram untuk membongkar file config tunnel — gratis & instan**

`Web App` · `Telegram Bot` · `Satu Service Render` · `Free Plan Ready`

[![Live](https://img.shields.io/badge/🌐_LIVE-sniffconfig.onrender.com-purple)](https://sniffconfig.onrender.com)
[![Bot](https://img.shields.io/badge/🤖_BOT-@snifferBC__Bot-blue)](https://t.me/snifferBC_Bot)
[![Version](https://img.shields.io/badge/version-v2.1.1-orange)]()
[![License](https://img.shields.io/badge/engine-MIT-green)]()

[🌐 Website](https://sniffconfig.onrender.com) · [🤖 Bot Telegram](https://t.me/snifferBC_Bot) · [👤 Contact](https://t.me/BleackCoderr)

</div>

---

## 📖 Apa Ini?

**Sniff Config** = tool untuk membaca/membongkar isi file config tunnel yang terenkripsi.
Lempar file → format terdeteksi otomatis → isi aslinya muncul (payload, proxy, SSH host, user/pass, dst).

Tersedia **2 jalur**:
| | 🌐 Web | 🤖 Bot Telegram |
|---|---|---|
| Link | [sniffconfig.onrender.com](https://sniffconfig.onrender.com) | [@snifferBC_Bot](https://t.me/snifferBC_Bot) |
| Pemakaian | drag & drop file | kirim file ke chat |
| Hasil | tampil + tombol salin | file `.txt` siap pakai |
| Jeda | 20 req/menit per IP | 3 menit per user |
| Bonus | tema gelap/terang, statistik live | leaderboard `/top`, fun facts |

> 🔒 **Privasi:** file diproses di memori lalu **dibuang** — tidak disimpan, tidak dilog.

## ✨ Format Didukung

| Ekstensi | Aplikasi |
|---|---|
| `.hc` | HTTP Custom |
| `.ehi` | HTTP Injector |
| `.ssc` / `ssc://` | SSC Custom |
| `.npv` / `.npvt` (NPVT1, NPVTSUB1) | NPV Tunnel |
| `.dark` / `darktunnel://` | Dark Tunnel |

## 🤖 Bot Telegram — Fitur

| Perintah | Fungsi |
|---|---|
| `/start` | Menu utama + tombol inline |
| `/help` | Panduan pemakaian |
| `/stats` | Statistik mesin (total/sukses/gagal + sniffer unik) |
| `/top` | 🏆 Leaderboard sniffer paling aktif |
| `/ping` | Cek mesin hidup + latensi |

- **Bisa di-invite ke grup** — chat biasa diabaikan (sopan), file tetap di-sniff
- Jeda 3 menit **per orang** (bukan per grup)
- Hasil dikirim sebagai file `.txt` + reply ke pesan asli
- Laporan tiap aktivitas → dikirim ke bot owner

## 🚀 Deploy ke Render (Free Plan) — Langkah Lengkap

> Total biaya: **$0**. Satu service untuk web + bot sekaligus.

### Prasyarat
- Akun GitHub (code di repo ini)
- Akun [render.com](https://render.com) (sign in pakai GitHub)
- 2 bot Telegram dari [@BotFather](https://t.me/BotFather):
  - **Bot 1** = bot laporan (kirim notifikasi aktivitas ke kamu)
  - **Bot 2** = bot sniff (yang publik dipakai user)
- Chat ID Telegram kamu (bisa via [@userinfobot](https://t.me/userinfobot))

### Langkah 1 — Push kode ke GitHub
```bash
git clone https://github.com/FachriHdyt139/sniffconfig
cd sniffconfig
git remote set-url origin https://github.com/USERNAME_KAMU/sniffconfig
git push -u origin main
```

### Langkah 2 — Buat Web Service di Render
1. Login **render.com** → **New +** → **Web Service**
2. **Connect** repo GitHub kamu
3. Isi form:
   | Field | Nilai |
   |---|---|
   | Name | `sniffconfig` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
   | Instance Type | `Free` |

### Langkah 3 — Environment Variables (PENTING! ⚠️)
Tab **Environment** → **Add Environment Variable** → isi **4 variabel**:

| Key | Value | Keterangan |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `123456:AAE...` | Token **bot 1** (laporan) |
| `TELEGRAM_CHAT_ID` | `7967286917` | Chat ID kamu (tujuan laporan) |
| `SNIFF_BOT_TOKEN` | `881285:AAF...` | Token **bot 2** (sniff) — ⚠️ **wajib, jangan lupa!** |
| `SNIFF_BOT` | `1` | Saklar bot (`0` = matikan bot, web doang) |

> 💡 Bot otomatis nyala kalau `SNIFF_BOT_TOKEN` terisi. Lupa isi ini = bot diam total (penyebab paling sering!).

### Langkah 4 — Deploy & Verifikasi
1. Klik **Create Web Service** → tunggu build (± 2-4 menit)
2. Tunggu status **"Deploy live"** di tab Events
3. Cek:
   - `https://nama-app.onrender.com/` → homepage nongol
   - `https://nama-app.onrender.com/api/botstatus` → harus `{"started": true, "token_present": true}`
4. Chat bot 2 → `/start` → harus dibales welcome 🐴

### Langkah 5 — Setup Bot di BotFather
1. `/mybots` → pilih bot 2 → **Bot Settings** → **Group Privacy** → **Turn off**
   (biar bot bisa baca file yang dilempar di grup)
2. `/setuserpic` → pasang foto profil
3. `/setdescription` + `/setabouttext` → isi bio
4. `/setmenubutton` → default (tombol ☰ menu di bawah chat)

### Arsitektur (kenapa 1 service cukup)
```
┌────────────────────── RENDER FREE TIER ──────────────────────┐
│                                                               │
│  gunicorn server:app                                          │
│   ├── Flask web  ──► homepage, /api/decrypt, /api/stats       │
│   └── thread bot ──► long-polling Telegram (bot 2)            │
│         └── laporan ──► bot 1 ──► chat owner                  │
│                                                               │
│  keepalive thread: ping self tiap 8 menit (anti-sleep)        │
└───────────────────────────────────────────────────────────────┘
```

## 💻 Run Lokal (VPS/komputer sendiri)

```bash
git clone https://github.com/FachriHdyt139/sniffconfig && cd sniffconfig
python3 -m venv venv && venv/bin/pip install -r requirements.txt

# buat .env
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=token_bot1
TELEGRAM_CHAT_ID=chatid_kamu
SNIFF_BOT_TOKEN=token_bot2
SNIFF_BOT=0          # bot lokal mati (biar nggak dobel sama Render)
EOF

venv/bin/python server.py     # http://localhost:3000
```

## 🔌 API

| Endpoint | Method | Keterangan |
|---|---|---|
| `/` | GET | Homepage |
| `/api/decrypt` | POST | multipart `file` → `{ok, format, filename, result, watermark}` |
| `/api/stats` | GET | `{total, success, failed}` |
| `/api/botstatus` | GET | Status bot + versi kode |
| `/robots.txt` `/sitemap.xml` | GET | SEO |

## 🛠️ Troubleshooting

| Gejala | Penyebab & Solusi |
|---|---|
| Bot diam total | `SNIFF_BOT_TOKEN` belum di Environment Render → isi & redeploy |
| Bot sempat bales lalu diam | Token di-revoke di BotFather → generate baru → update env Render |
| Tag HTML mentah di pesan | Sudah difix di v1.5.2 (parse_mode + fallback) — pastikan deploy terbaru |
| Web "Rendering..." lama | Cold start free tier — keepalive thread sudah meminimalkan |
| Bot bales obrolan grup | Sudah difix di v2.1 (diam kecuali perintah/file) — pastikan versi `v2.1-grupdiam` via `/api/botstatus` |
| Gagal sniff | Config dikunci versi baru → lapor format ke [@BleackCoderr](https://t.me/BleackCoderr) |

> ℹ️ **Catatan v6:** fitur 🔓 UNLOCK .HC sudah DIHAPUS (app HTTP Custom terbaru memverifikasi
> signature anti-tamper pada config terkunci, jadi file hasil unlock selalu ditolak app).
> Bot tetap bisa MEMBACA/men-sniff semua format seperti biasa.

## 📁 Struktur Project

```
sniffconfig/
├── server.py            # Flask app + API + start bot thread
├── sniffbot.py          # Bot Telegram v2 (bot 2) — jalan di proses yang sama
├── engine/              # 5 modul decrypt per format
│   ├── HTTPCUSTOM.py    ├── HTTPINJECTOR.py   ├── SSCCUSTOM.py
│   ├── NPVTUNNEL.py     └── DARKTUNNEL.py
├── templates/index.html # frontend neo-brutalist, dual theme
├── static/style.css
├── stats.json           # statistik sniff (auto-generated)
├── sniffers.json        # leaderboard (auto-generated)
├── render.yaml          # Blueprint Render
├── Procfile             # start command
├── .env                 # token lokal (JANGAN di-push! sudah di .gitignore)
└── requirements.txt
```

## 🔐 Keamanan

- ✅ Security headers: CSP, X-Frame-Options, nosniff, Referrer-Policy
- ✅ Rate limiting: web 20 req/menit per IP, bot 3 menit per user
- ✅ File maks 5MB, diproses di memori, tanpa logging isi
- ✅ Token hanya via environment variables — tidak pernah masuk repo
- ✅ Tidak ada `eval`/`exec` — parser murni kriptografi

## ⚠️ Disclaimer

Tool ini untuk **audit config milik sendiri**, edukasi struktur payload, dan konversi antar-aplikasi.
Gunakan secara bijak & bertanggung jawab. Kamu tidak berhak membongkar config milik orang lain tanpa izin.

---

<div align="center">

**© 2026 @BleackCoderr**

[🌐 Website](https://sniffconfig.onrender.com) · [🤖 Bot](https://t.me/snifferBC_Bot) · [👤 Contact](https://t.me/BleackCoderr)

*Engine decrypt: [ENIGMATIC-MAN/DECRYPTION_SCRIPTS](https://github.com/ENIGMATIC-MAN/DECRYPTION_SCRIPTS) (MIT)*

</div>
