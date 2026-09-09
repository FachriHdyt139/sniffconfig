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

## 🚀 Deploy ke Render (Free Plan) — Panduan Mandiri

> Total biaya: **$0**. Satu service menjalankan web + bot Telegram sekaligus.
> Panduan ini dibuat supaya bisa dikerjakan **tanpa bantuan siapa pun** — ikutin urut, jangan loncat.

### Prasyarat (siapkan ini dulu, baru buka Render)
- [ ] Akun GitHub, repo ini bisa di-fork/clone
- [ ] Akun [render.com](https://render.com) — **sign in pakai GitHub** biar langsung keliatan repo sendiri
- [ ] **2 bot Telegram** dari [@BotFather](https://t.me/BotFather) (menu `/newbot`):
  - **Bot 1** = bot laporan (DM notifikasi aktivitas ke owner) → catet token-nya
  - **Bot 2** = bot sniff publik (yang dipakai user) → catet token-nya
- [ ] Chat ID Telegram kamu (DM [@userinfobot](https://t.me/userinfobot), dia bales angka)
- [ ] ID bot 2 (angka, bukan username) — kirim `/start` ke bot 2, lalu buka
      `https://api.telegram.org/bot<SNIFF_BOT_TOKEN>/getUpdates` di browser,
      cari `"chat":{"id":...}` → itu `BOT2_ID`

### Langkah 1 — Kode di GitHub
```bash
git clone https://github.com/FachriHdyt139/sniffconfig
cd sniffconfig
# kalau mau pindah ke akun sendiri:
git remote set-url origin https://github.com/USERNAME_KAMU/sniffconfig
git push -u origin main
```
> `.env` lokal TIDAK ikut ke repo (ada di `.gitignore`) — itu disengaja.
> Token TIDAK ADA di mana pun di kode; satu-satunya tempat token adalah
> Environment Variables di dashboard Render (Langkah 3). Jangan nunggu `.env` jalan di Render, nggak akan.

### Langkah 2 — Buat Web Service di Render
1. render.com → **New +** → **Web Service** → pilih repo
2. Isi form:
   | Field | Nilai |
   |---|---|
   | Name | `sniffconfig` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
   | Instance Type | `Free` |

⚠️ **Start Command di dashboard OVERRIDE `Procfile`/`render.yaml`.**
Kode di repo boleh berubah, tapi yang jalan di Render adalah yang tertulis di dashboard.
Sebelum klik Create, cek lagi field Start Command — jangan cuma percaya "ada Procfile kok".
(`Procfile` sengaja dipasang `SNIFF_BOT=1 gunicorn ...` sebagai cadangan kalau lupa set env.)

### Langkah 3 — Environment Variables (WAJIB SEMUA, ⚠️ PENYEBAB #1 BOT MATI)
Tab **Environment** → **Add Environment Variable**:

| Key | Contoh Value | Wajib? | Keterangan |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `123456:AAE...` | ✅ | Token bot 1 (laporan) |
| `TELEGRAM_CHAT_ID` | `7967286917` | ✅ | Chat ID owner (tujuan laporan) |
| `SNIFF_BOT_TOKEN` | `881285:AAF...` | ✅ | Token bot 2 (sniff). **Kosong = bot diam total** |
| `SNIFF_BOT` | `1` | ✅ | Saklar bot (`0` = web doang, bot mati) |
| `BOT2_ID` | `881285` | ✅ | Angka ID bot 2 — dipakai buat event anggota baru masuk grup |
| `SNIFF_GROUP_ID` | `@SNIFF_lD` | opsional | Grup gerbang; default sudah `@SNIFF_lD` di kode. **Bot 2 harus jadi ADMIN grup ini** |
| `SNIFF_GATE` | `1` | opsional | `1`/kosong = user harus join grup dulu sebelum bisa sniff; `0` = gerbang terbuka (tombol darurat) |
| `SELF_PING_URL` | `https://nama-app.onrender.com/api/stats` | opsional | Overrid keepalive; default sudah URL app sendiri |

> 💡 Urutan aman: create service dulu → Render kasih URL `nama-app.onrender.com` → isi semua env → **Manual Deploy → Build and deploy image**.

### Langkah 4 — Deploy & Verifikasi (jangan skip verifikasi)
1. Tunggu build selesai (± 2-4 menit), status **"Deploy live"** di tab Events
2. Cek satu-satu, **ketik manual di browser:**
   - `https://nama-app.onrender.com/` → homepage nongol
   - `https://nama-app.onrender.com/api/botstatus` → **harus** `{"started": true, "token_present": true}`
     - `token_present: false` → `SNIFF_BOT_TOKEN` salah/kosong
     - `started: false` → `SNIFF_BOT` bukan `1`
3. Chat bot 2 → `/start` → harus dibales. Kalo diem padahal botstatus hijau:
   token kemungkinan di-revoke BotFather → buat token baru → update env → redeploy

### Langkah 5 — Setup Bot di BotFather (cuma bisa kamu yang kerjain)
1. `/mybots` → bot 2 → **Bot Settings** → **Group Privacy** → **Turn OFF**
   (kalo ON, bot gak bisa baca file yang dilempar di grup)
2. Jadikan bot 2 **ADMIN** di grup `SNIFF_lD` (buat gerbang membership)
3. `/setuserpic`, `/setdescription`, `/setabouttext` → branding
4. `/setmenubutton` → tombol ☰ menu
5. `/setcommands` → biar menu perintah rapi

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

# buat .env (sama kayak env var Render, bedanya di sini lewat file)
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=token_bot1
TELEGRAM_CHAT_ID=chatid_kamu
SNIFF_BOT_TOKEN=token_bot2
SNIFF_BOT=0          # bot lokal mati (biar nggak dobel sama Render)
BOT2_ID=id_angka_bot2
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
| Bot diam total | `SNIFF_BOT_TOKEN` / `SNIFF_BOT=1` belum di Environment Render → isi & redeploy. Cek `/api/botstatus` dulu sebelum nebak |
| Web hidup tapi bot mati doang | Env `SNIFF_BOT` lupa diisi `1` — bukan salah kode |
| Event join grup gak kebaca / error | `BOT2_ID` belum diisi di env (harus angka ID bot, bukan token) |
| Semua user dikunci tombol JOIN terus | Bot 2 belum jadi ADMIN di `SNIFF_GROUP_ID`, atau belum keluar dari daftar member — cek grup; darurat: set `SNIFF_GATE=0` |
| Bot sempat bales lalu diam | Token di-revoke di BotFather → generate baru → update env Render |
| Web "Rendering..." lama tiap mau dipakai | Cold start free tier — keepalive thread sudah meminimalkan, tapi tetap bisa kena |
| Build gagal | Python version / requirements berubah — lihat log Build di tab Events, baca baris `ERROR:` paling bawah |
| Gagal sniff | Config dikunci versi baru → lapor format |

### 🔁 Alur Kalau Lu Deploy Ulang dari Nol (worldwide, tanpa gue)
```bash
# 1. clone + push ke repo sendiri
git clone https://github.com/FachriHdyt139/sniffconfig && cd sniffconfig

# 2. siapin 8 env var (salin & isi) — ini checklist, tempel satu-satu di dashboard Render
#    TELEGRAM_BOT_TOKEN=...  TELEGRAM_CHAT_ID=...
#    SNIFF_BOT_TOKEN=...     SNIFF_BOT=1
#    BOT2_ID=...             SNIFF_GROUP_ID=@SNIFF_lD
#    SNIFF_GATE=1            SELF_PING_URL=https://nama-app.onrender.com/api/stats

# 3. di Render: New Web Service → repo → isi form Langkah 2 → paste 8 env → Create
# 4. tunggu live → cek https://nama-app.onrender.com/api/botstatus
#    harus: {"started": true, "token_present": true}
# 5. BotFather: Group Privacy OFF + bot 2 jadi ADMIN grup
```
> ⚠️ Data user/statistik di Render itu file `botdata.json` yang hilang saat cold start
> kalau tidak pakai persistent disk. Cooldown & leaderboard balik nol — itu normal, bukan bug.

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
