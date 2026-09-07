# Sniff Config — web decryptor multi-format (HC/EHI/SSC/NPV/NPVT/DARK)
# Engine: ENIGMATIC-MAN/DECRYPTION_SCRIPTS (MIT) | Watermark: @BleackCoderr
import os, json, time, threading, urllib.request, urllib.parse
from flask import Flask, request, jsonify, render_template, send_from_directory

def load_env(path=None):
    """Baca .env sederhana (KEY=VALUE) tanpa dependency tambahan."""
    path = path or os.path.join(os.path.dirname(__file__), ".env")
    try:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    except FileNotFoundError:
        pass

load_env()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "")

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))
import HTTPCUSTOM, HTTPINJECTOR, NPVTUNNEL, SSCCUSTOM, DARKTUNNEL

app = Flask(__name__, static_folder="static")
STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")

# --- daftar parser per format (urut = prioritas deteksi) ---
PARSERS = [
    ("HC",   HTTPCUSTOM.run),
    ("EHI",  HTTPINJECTOR.run),
    ("NPVT", NPVTUNNEL.run),
    ("SSC",  SSCCUSTOM.run),
    ("DARK", DARKTUNNEL.run),
]

def load_stats():
    try:
        return json.load(open(STATS_FILE))
    except Exception:
        return {"total": 0, "success": 0, "failed": 0}

def save_stats(s):
    try:
        json.dump(s, open(STATS_FILE, "w"))
    except Exception:
        pass

# --- laporan Telegram (non-blocking, gagal diam-diam) ---
def tg_report(text):
    if not TG_TOKEN or not TG_CHAT:
        return
    def _send():
        try:
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data=urllib.parse.urlencode({"chat_id": TG_CHAT, "text": text,
                                             "disable_web_page_preview": "true"}).encode(),
                method="POST")
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

def visitor_info():
    ua = request.headers.get("User-Agent", "?")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()
    return ip, ua[:120]

# throttle: 1 laporan akses per IP per 30 menit biar nggak spam
_seen = {}
def should_report(ip):
    now = time.time()
    if now - _seen.get(ip, 0) < 1800:
        return False
    _seen[ip] = now
    return True

def detect_by_ext(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "hc": "HC", "ehi": "EHI",
        "npv": "NPVT", "npvt": "NPVT",
        "ssc": "SSC", "dark": "DARK",
    }.get(ext)

@app.after_request
def security_headers(resp):
    """Basic hardening: clickjacking, MIME-sniffing, referrer leak, XSS."""
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    return resp

# --- rate limiter sederhana (in-memory, per IP) ---
_hits = {}
def rate_limited(ip, limit=20, window=60):
    now = time.time()
    bucket = [t for t in _hits.get(ip, []) if now - t < window]
    if len(bucket) >= limit:
        _hits[ip] = bucket
        return True
    bucket.append(now)
    _hits[ip] = bucket
    return False

@app.route("/")
def home():
    ip, ua = visitor_info()
    if should_report(ip):
        tg_report(f"🌐 AKSES BARU\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n📍 IP: {ip}\n📱 {ua}")
    return render_template("index.html")

@app.route("/robots.txt")
def robots():
    host = request.host_url.rstrip("/")
    return f"User-agent: *\nAllow: /\nSitemap: {host}/sitemap.xml\n", 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap():
    host = request.host_url.rstrip("/")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{host}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
</urlset>""", 200, {"Content-Type": "application/xml"}

@app.route("/api/stats")
def stats():
    return jsonify(load_stats())

@app.route("/api/botstatus")
def botstatus():
    try:
        import sniffbot as sb
        return jsonify({"token_present": bool(sb.BOT2_TOKEN),
                        "started": bool(getattr(sb, "STARTED", False)),
                        "active_cooldowns": len(sb._last)})
    except Exception as e:
        return jsonify({"token_present": False, "started": False, "err": str(e)[:80]})

@app.route("/api/decrypt", methods=["POST"])
def decrypt():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "No file selected."})

    ip, _ = visitor_info()
    if rate_limited(ip, limit=20, window=60):
        return jsonify({"ok": False, "error": "Terlalu banyak request — coba lagi 1 menit lagi."}), 429

    data = f.read()
    if len(data) == 0:
        return jsonify({"ok": False, "error": "File kosong."})
    if len(data) > 5 * 1024 * 1024:
        return jsonify({"ok": False, "error": "File terlalu besar (maks 5MB)."})

    stats = load_stats()
    stats["total"] += 1

    ip, ua = visitor_info()
    opt_in = request.form.get("send_file") == "1"   # pengunjung mencentang sendiri

    # 1) coba sesuai ekstensi dulu, 2) sisanya fallback auto-detect
    hint = detect_by_ext(f.filename)
    order = ([p for p in PARSERS if p[0] == hint] +
             [p for p in PARSERS if p[0] != hint])

    for fmt, fn in order:
        try:
            result = fn(data)
        except Exception:
            result = None
        if result:
            stats["success"] += 1
            save_stats(stats)
            tg_report(f"✅ SNIFF BERHASIL\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n📄 {f.filename} ({len(data)} B)\n🏷️ Format: {fmt}\n📍 IP: {ip}")
            if opt_in:
                tg_file(f, data)
            return jsonify({
                "ok": True,
                "format": fmt,
                "filename": f.filename,
                "result": result,
                "watermark": "@BleackCoderr",
                "tg": "https://t.me/BleackCoderr",
            })

    stats["failed"] += 1
    save_stats(stats)
    # Tanda kegagalan: hash (tak bisa dibalik) + ukuran + tahap gagal. TANPA isi file.
    import hashlib
    sig = hashlib.sha256(data).hexdigest()[:12]
    tried = ", ".join(fmt for fmt, _ in order)
    tg_report(f"❌ SNIFF GAGAL (kemungkinan key berubah)\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n📄 {f.filename} ({len(data)} B)\n🔖 SHA256: {sig}…\n🧪 Dicoba: {tried}\n📍 IP: {ip}")
    if opt_in:
        tg_file(f, data)
    return jsonify({"ok": False, "error": "Format tidak dikenali / config terkunci versi baru."})

def tg_file(f, data):
    """Kirim file HANYA kalau pengunjung mencentang opt-in (legal & etis)."""
    if not TG_TOKEN or not TG_CHAT:
        return
    def _send():
        try:
            import mimetypes
            boundary = "----sniffcfg" + str(int(time.time() * 1000))
            body = (
                f"--{boundary}\r\nContent-Disposition: form-data; name=chat_id\r\n\r\n{TG_CHAT}\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=caption\r\n\r\n"
                f"📎 Dikirim sukarela oleh pengunjung ({f.filename})\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=document; filename={f.filename}\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument",
                data=body, method="POST",
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            urllib.request.urlopen(req, timeout=15)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

# --- bot sniff Telegram (bot 2) jalan di proses yang sama: hemat 1 service Render ---
# Gunicorn cuma nge-set WEBLOGIC/SERVER_NAME di worker #1; kita pakai env var sendiri biar
# nggak dobel polling. Render: start command pakai SNIFF_BOT=1 cuma di worker yang sama.
if os.environ.get("SNIFF_BOT", "1") != "0":  # nyala otomatis kalau token ada; lokal matikan via .env (SNIFF_BOT=0)
    try:
        import sniffbot
        sniffbot.start()
    except Exception as e:
        print("bot2 gagal start:", e, flush=True)

if __name__ == "__main__":
    # Render ngasih port lewat env var PORT; lokal default 3000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
