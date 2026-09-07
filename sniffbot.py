# Sniff Bot Telegram (bot 2) — jalan sebagai thread di dalam app web (hemat 1 service Render)
# Jeda 3 menit per chat | watermark @BleackCoderr | laporan ke bot 1 (owner)
import os, sys, json, time, hashlib, threading, urllib.request, urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

BOT2_TOKEN = os.environ.get("SNIFF_BOT_TOKEN", "")
OWNER_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")   # bot 1 = laporan
OWNER_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
COOLDOWN = 180  # 3 menit per chat id
STARTED = False

WATERMARK = "\n\n🐴 SNIFF CONFIG — dioléh oléh @BleackCoderr ✦\n🌐 https://sniffconfig.onrender.com"

def _api(token, method, **kw):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(kw).encode(), method="POST")
    return json.load(urllib.request.urlopen(req, timeout=35))

def _multipart(token, method, fields, fname, fdata):
    b = "----sniffw" + str(int(time.time() * 1000))
    body = b""
    for k, v in fields.items():
        body += f"--{b}\r\nContent-Disposition: form-data; name={k}\r\n\r\n{v}\r\n".encode()
    body += (f"--{b}\r\nContent-Disposition: form-data; name=document; "
             f"filename={fname}\r\nContent-Type: text/plain\r\n\r\n").encode()
    body += fdata + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=35))

def _send(chat_id, text):
    if not BOT2_TOKEN: return
    try:
        try:
            _api(BOT2_TOKEN, "sendMessage", chat_id=chat_id, text=text,
                 parse_mode="HTML", disable_web_page_preview="true")
        except Exception:
            # HTML rusak / nggak valid — kirim polos aja
            import re
            _api(BOT2_TOKEN, "sendMessage", chat_id=chat_id,
                 text=re.sub(r"</?(b|i|code|a)[^>]*>", "", text),
                 disable_web_page_preview="true")
    except Exception:
        pass

def _report_owner(text):
    """Info pemakaian bot 2 -> bot 1 (laporan), gagal diam-diam."""
    if not (OWNER_TOKEN and OWNER_CHAT): return
    try:
        _api(OWNER_TOKEN, "sendMessage", chat_id=OWNER_CHAT, text=text,
             disable_web_page_preview="true")
    except Exception:
        pass

_last = {}  # chat_id -> ts sniff terakhir
def _cool(chat_id):
    now = time.time()
    left = COOLDOWN - (now - _last.get(chat_id, -COOLDOWN))
    if left > 0:
        m, s = divmod(int(left), 60)
        return f"⏳ TUNGGU {m} MENIT {s} DETIK LAGI, SOBRIS!\nJeda 3 menit per orang biar mesinnya nggak ngos-ngosan 😤"
    _last[chat_id] = now
    return None

WELCOME = (
    "🐴 <b>SNIFF CONFIG BOT</b>\n\n"
    "Lempar file config ke sini → isi aslinya langsung muncul.\n"
    "Didukung: <code>.HC .EHI .SSC .NPV .NPVT .DARK</code>\n\n"
    "⏳ Jeda pakai: <b>3 menit</b> per orang\n"
    "🔒 File diproses lalu dibuang — nggak disimpan\n"
    "🌐 Versi web: https://sniffconfig.onrender.com\n"
    "👤 @BleackCoderr"
)

def _stats():
    try:
        return json.load(open(os.path.join(os.path.dirname(__file__), "stats.json")))
    except Exception:
        return {"total": 0, "success": 0, "failed": 0}

def _handle(msg):
    chat_id = msg["chat"]["id"]
    user = msg.get("from", {})
    uname = user.get("username")
    label = ("@" + uname) if uname else (user.get("first_name") or str(chat_id))
    text = (msg.get("text") or "").strip()

    if text.startswith("/start") or text.startswith("/help"):
        _send(chat_id, WELCOME); return
    if text.startswith("/stats"):
        s = _stats()
        _send(chat_id, f"📊 TOTAL SNIFF: {s['total']} ✔ {s['success']} ✘ {s['failed']}" + WATERMARK)
        return

    doc = msg.get("document")
    if not doc:
        _send(chat_id, "🤔 Kirim <b>file config</b> ya — bukan teks.\n"
                       "Format: .hc .ehi .ssc .npv .npvt .dark\n/start buat info.")
        return

    wait = _cool(chat_id)
    if wait:
        _send(chat_id, wait); return

    fname = doc.get("file_name", "config.bin")
    fsize = doc.get("file_size", 0)
    if fsize > 5 * 1024 * 1024:
        _send(chat_id, "❌ File maks 5MB, Bro."); return

    _send(chat_id, f"🔎 MESIN NGUNYAH <code>{fname}</code> …")
    try:
        fp = _api(BOT2_TOKEN, "getFile", file_id=doc["file_id"])["result"]["file_path"]
        data = urllib.request.urlopen(
            f"https://api.telegram.org/file/bot{BOT2_TOKEN}/{fp}", timeout=30).read()
    except Exception:
        _send(chat_id, "❌ Gagal unduh file — coba lagi."); return

    # pakai parser yang sama dengan web
    import server
    hint = server.detect_by_ext(fname)
    order = ([p for p in server.PARSERS if p[0] == hint] +
             [p for p in server.PARSERS if p[0] != hint])
    fmt, result = None, None
    for f, fn in order:
        try:
            r = fn(data)
        except Exception:
            r = None
        if r:
            fmt, result = f, r; break

    s = _stats(); s["total"] += 1
    if result:
        s["success"] += 1
        try: json.dump(s, open(os.path.join(os.path.dirname(__file__), "stats.json"), "w"))
        except Exception: pass
        body = (f"✅ BERHASIL — format {fmt}\n📄 {fname}\n"
                f"🕐 {time.strftime('%d-%m-%Y %H:%M')}\n"
                f"{'─' * 30}\n\n{result}" + WATERMARK)
        try:
            _multipart(BOT2_TOKEN, "sendDocument",
                       {"chat_id": chat_id, "caption": f"🏷️ {fmt} ✔ @BleackCoderr"},
                       fname + ".sniffed.txt", body.encode())
        except Exception:
            for i in range(0, len(body), 3900):
                _send(chat_id, body[i:i + 3900])
        _report_owner(f"🤖 BOT SNIFF ✔\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n"
                      f"👤 {label} (id={chat_id})\n📄 {fname} ({len(data)} B)\n🏷️ {fmt}")
    else:
        s["failed"] += 1
        try: json.dump(s, open(os.path.join(os.path.dirname(__file__), "stats.json"), "w"))
        except Exception: pass
        sig = hashlib.sha256(data).hexdigest()[:12]
        _send(chat_id, "❌ GAGAL — format nggak dikenali / dikunci versi baru.\n"
                       f"🔖 SHA256: {sig}…\nRequest dukungan: @BleackCoderr")
        _report_owner(f"🤖 BOT SNIFF ✘\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n"
                      f"👤 {label} (id={chat_id})\n📄 {fname} ({len(data)} B)\n🔖 {sig}…")

def _poll_loop():
    offset = 0
    try:
        _api(BOT2_TOKEN, "deleteWebhook")
    except Exception:
        pass
    while True:
        try:
            ups = _api(BOT2_TOKEN, "getUpdates", offset=offset, timeout=25)["result"]
            for u in ups:
                offset = max(offset, u["update_id"] + 1)
                m = u.get("message") or u.get("edited_message")
                if m:
                    try: _handle(m)
                    except Exception as e: print("bot2 handle:", e, flush=True)
        except Exception:
            time.sleep(5)

def _keepalive_loop():
    """Render free tier tidur kalau 15 menit sepi -> bot ikut mati.
    Ngetok URL publik sendiri tiap 8 menit biar container selalu melek."""
    url = os.environ.get("SELF_PING_URL", "https://sniffconfig.onrender.com/api/stats")
    while True:
        time.sleep(480)
        try:
            urllib.request.urlopen(url, timeout=15).read()
        except Exception:
            pass

def start():
    """Panggil dari server.py. Diam-diam skip kalau token belum diisi."""
    if not BOT2_TOKEN:
        print("bot2: SNIFF_BOT_TOKEN kosong — dilewati", flush=True)
        return
    global STARTED
    threading.Thread(target=_keepalive_loop, daemon=True, name="keepalive").start()
    t = threading.Thread(target=_poll_loop, daemon=True, name="sniffbot")
    t.start()
    STARTED = True
    print("bot2: thread sniff bot + keepalive jalan ✅", flush=True)
