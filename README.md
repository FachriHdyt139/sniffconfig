# 🐴 Sniff Config — @BleackCoderr

Web tool untuk menganalisis / sniff file konfigurasi tunnel.
Upload file → format terdeteksi otomatis → hasil tampil ala terminal hacker.

## Format didukung
| Ekstensi | Aplikasi |
|---|---|
| `.hc` | HTTP Custom |
| `.ehi` | HTTP Injector |
| `.ssc` / `ssc://` | SSC Custom |
| `.npv` / `.npvt` (NPVT1, NPVTSUB1) | NPV Tunnel |
| `.dark` / `darktunnel://` | Dark Tunnel |

## Stack
- **Backend**: Python + Flask (+ gunicorn untuk production)
- **Engine decrypt**: modul dari [ENIGMATIC-MAN/DECRYPTION_SCRIPTS](https://github.com/ENIGMATIC-MAN/DECRYPTION_SCRIPTS) (MIT)
- **Frontend**: HTML/CSS/JS vanilla, tema terminal
- **Stats**: persisten ke `stats.json` (total / berhasil / gagal)

## Run lokal
```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python server.py        # http://localhost:3000
```

## Deploy ke Render (free plan)
1. Push repo ini ke GitHub
2. render.com → **New → Web Service** → connect repo
3. Render auto-baca `render.yaml`:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn server:app --bind 0.0.0.0:$PORT --timeout 120`
4. Done — site live di `https://sniffconfig.onrender.com`

> Catatan free plan: service **tidur** setelah 15 menit sepi, bangun lagi ~30-50 detik saat ada yang akses.

## Struktur
```
server.py          # Flask app + API
engine/            # 5 modul decrypt per format
templates/index.html
static/style.css
render.yaml        # Blueprint Render
Procfile           # fallback start command
```

## API
- `POST /api/decrypt` (multipart `file`) → `{ok, format, filename, result, watermark}`
- `GET /api/stats` → `{total, success, failed}`

---
© 2026 **@BleackCoderr** — https://t.me/BleackCoderr
