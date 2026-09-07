# Sniff Bot v2 — fitur lengkap: inline buttons, leaderboard, fun facts, reply, typing,
# cooldown per-user 3 menit | watermark @BleackCoderr | laporan ke bot 1 (owner)
import os, sys, json, time, hashlib, threading, urllib.request, urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

BOT2_TOKEN = os.environ.get("SNIFF_BOT_TOKEN", "")
OWNER_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
COOLDOWN = 180
BOT_VERSION = "v2.1-grupdiam"
STARTED = False
WATERMARK = "\n\n🐴 SNIFF CONFIG — diolah oleh @BleackCoderr ✦\n🌐 https://sniffconfig.onrender.com"

EMOJI = {"HC": "🐴", "EHI": "💉", "SSC": "🔐", "NPVT": "🛰️", "DARK": "🌑"}
FACTS = [
    "💡 Tips: config yang dikunci HWID cuma bisa dibuka di device asalnya.",
    "💡 Tahu gak? Format .ehi & .hc beda aplikasi tapi isinya mirip trik.",
    "💡 Kalau gagal terus, kemungkinan key-nya versi baru — lapor @BleackCoderr!",
    "💡 Web-nya juga bisa nge-sniff: sniffconfig.onrender.com",
    "💡 Share bot ini ke grup — makin rame makin semangat gue ngoding 🔥",
    "💡 Config lama sering masih jalan — cek masa aktif SSH-nya dulu.",
]
TOOLS_ROW = [[{"text": "🌐 BUKA WEB", "url": "https://sniffconfig.onrender.com"},
              {"text": "👤 CHAT OWNER", "url": "https://t.me/BleackCoderr"}]]

def _api(token, method, **kw):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(kw).encode(), method="POST")
    return json.load(urllib.request.urlopen(req, timeout=35))

def _multipart(method, fields, fname, fdata):
    b = "----sniffw" + str(int(time.time() * 1000))
    body = b""
    for k, v in fields.items():
        body += f"--{b}\r\nContent-Disposition: form-data; name={k}\r\n\r\n{v}\r\n".encode()
    body += (f"--{b}\r\nContent-Disposition: form-data; name=document; "
             f"filename={fname}\r\nContent-Type: text/plain\r\n\r\n").encode()
    body += fdata + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{BOT2_TOKEN}/{method}",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=35))

def _send(chat_id, text, buttons=None, reply_to=None):
    if not BOT2_TOKEN: return
    kw = {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    if buttons: kw["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    if reply_to: kw["reply_to_message_id"] = reply_to
    try:
        _api(BOT2_TOKEN, "sendMessage", parse_mode="HTML", **kw)
    except Exception:
        try:
            import re
            _api(BOT2_TOKEN, "sendMessage",
                 chat_id=chat_id, text=re.sub(r"</?(b|i|code|a)[^>]*>", "", text),
                 disable_web_page_preview="true",
                 **({"reply_markup": kw["reply_markup"]} if buttons else {}))
        except Exception:
            pass

def _typing(chat_id):
    try: _api(BOT2_TOKEN, "sendChatAction", chat_id=chat_id, action="typing")
    except Exception: pass

def _report_owner(text):
    if not (OWNER_TOKEN and OWNER_CHAT): return
    try: _api(OWNER_TOKEN, "sendMessage", chat_id=OWNER_CHAT, text=text, disable_web_page_preview="true")
    except Exception: pass

# ---------- stat + leaderboard ----------
BASE_DIR = os.path.dirname(__file__)
def _stats():
    try: return json.load(open(os.path.join(BASE_DIR, "stats.json")))
    except Exception: return {"total": 0, "success": 0, "failed": 0}
def _save_stats(s):
    try: json.dump(s, open(os.path.join(BASE_DIR, "stats.json"), "w"))
    except Exception: pass
def _board():
    try: return json.load(open(os.path.join(BASE_DIR, "sniffers.json")))
    except Exception: return {}
def _board_add(uid, name):
    b = _board()
    e = b.get(str(uid), {"name": name, "count": 0})
    e["count"] += 1; e["name"] = name
    b[str(uid)] = e
    try: json.dump(b, open(os.path.join(BASE_DIR, "sniffers.json"), "w"))
    except Exception: pass

_last = {}
def _cool(uid):
    now = time.time()
    left = COOLDOWN - (now - _last.get(uid, -COOLDOWN))
    if left > 0:
        m, s = divmod(int(left), 60)
        return f"⏳ TUNGGU {m} MENIT {s} DETIK LAGI, SOBRIS!\nJeda 3 menit per orang biar mesinnya nggak ngos-ngosan 😤"
    _last[uid] = now
    return None

WELCOME = (
    "🐴 <b>SNIFF CONFIG BOT v2</b>\n\n"
    "Lempar file config → isi aslinya langsung muncul.\n"
    "Didukung: <code>.HC .EHI .SSC .NPV .NPVT .DARK</code>\n\n"
    "⚡ <b>PERINTAH:</b>\n"
    "/start — mulai\n/help — panduan\n/stats — statistik bot\n"
    "/top — leaderboard sniffers 🏆\n/ping — cek mesin\n\n"
    "⏳ Jeda 3 menit per orang\n🔒 File diproses lalu dibuang\n"
    "👥 Bisa di-invite ke grup! (privacy mode OFF)"
)

def _handle(msg):
    chat_id = msg["chat"]["id"]
    user = msg.get("from", {})
    uid, uname = user.get("id", chat_id), user.get("username")
    label = ("@" + uname) if uname else (user.get("first_name") or str(chat_id))
    text = (msg.get("text") or "").strip()

    if text.startswith("/start"):
        _send(chat_id, WELCOME, TOOLS_ROW); return
    if text.startswith("/help"):
        _send(chat_id, "📖 <b>PANDUAN SNIFF BOT</b>\n\n1. Kirim/lempar file config (dokumen)\n"
              "2. Mesin auto-detect format-nya\n3. Hasil datang sebagai file .txt\n\n"
              "Buat grup: invite bot + matikan privacy mode lewat BotFather.", TOOLS_ROW); return
    if text.startswith("/stats"):
        s = _stats()
        _send(chat_id, f"📊 <b>STATISTIK MESIN</b>\n\n🔢 Total: <b>{s['total']}</b>\n"
              f"✔ Berhasil: <b>{s['success']}</b>\n✘ Gagal: <b>{s['failed']}</b>\n"
              f"👥 Sniffer unik: <b>{len(_board())}</b>" + WATERMARK, TOOLS_ROW); return
    if text.startswith("/top"):
        b = sorted(_board().items(), key=lambda x: -x[1]["count"])[:5]
        if not b:
            _send(chat_id, "🏆 BELUM ADA YANG PUNYA SKOR — jadi sniff pertama!"); return
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        rows = "\n".join(f"{medal[i]} {e['name']} — <b>{e['count']}x</b>" for i, (_, e) in enumerate(b))
        _send(chat_id, f"🏆 <b>TOP SNIFFERS</b>\n\n{rows}" + WATERMARK); return
    if text.startswith("/ping"):
        t0 = time.time(); _typing(chat_id)
        _send(chat_id, f"🏓 PONG! Mesin ngebut — latensi {int((time.time()-t0)*1000)} ms ✅"); return
    if text.startswith("/"):
        return

    doc = msg.get("document")
    if not doc:
        # di GRUP: text biasa -> diam aja (sopan, nggak ganggu obrolan)
        # chat PRIBADI: kasih petunjuk
        if msg["chat"].get("type") == "private":
            _send(chat_id, "🤔 Kirim <b>file config</b> ya — bukan teks.\nFormat: .hc .ehi .ssc .npv .npvt .dark"); return
        return

    wait = _cool(uid)
    if wait:
        _send(chat_id, wait); return

    fname, fsize = doc.get("file_name", "config.bin"), doc.get("file_size", 0)
    if fsize > 5 * 1024 * 1024:
        _send(chat_id, "❌ File maks 5MB, Bro."); return

    _typing(chat_id)
    _send(chat_id, f"🔎 NGUNYAH <code>{fname}</code> …", reply_to=msg.get("message_id"))
    try:
        fp = _api(BOT2_TOKEN, "getFile", file_id=doc["file_id"])["result"]["file_path"]
        data = urllib.request.urlopen(f"https://api.telegram.org/file/bot{BOT2_TOKEN}/{fp}", timeout=35).read()
    except Exception:
        _send(chat_id, "❌ Gagal unduh file — coba lagi."); return

    import server
    hint = server.detect_by_ext(fname)
    order = ([p for p in server.PARSERS if p[0] == hint] + [p for p in server.PARSERS if p[0] != hint])
    fmt = result = None
    for f, fn in order:
        try: r = fn(data)
        except Exception: r = None
        if r: fmt, result = f, r; break

    s = _stats(); s["total"] += 1
    if result:
        s["success"] += 1; _save_stats(s); _board_add(uid, label)
        fact = FACTS[int(time.time()) % len(FACTS)]
        body = (f"{EMOJI.get(fmt, '✅')} <b>BERHASIL</b> — format {fmt}\n📄 {fname}\n"
                f"🕐 {time.strftime('%d-%m-%Y %H:%M')}\n{'─'*30}\n\n{result}" + WATERMARK)
        try:
            _multipart("sendDocument", {"chat_id": chat_id,
                       "caption": f"{EMOJI.get(fmt,'')} {fmt} ✔ @BleackCoderr — {fact}"},
                       fname + ".sniffed.txt", body.encode())
        except Exception:
            for i in range(0, len(body), 3900): _send(chat_id, body[i:i+3900])
        _report_owner(f"🤖 BOT SNIFF ✔\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n👤 {label} (id={uid})\n"
                      f"📄 {fname} ({len(data)} B)\n🏷️ {fmt}\n📍 {'grup' if chat_id != uid else 'pribadi'}")
    else:
        s["failed"] += 1; _save_stats(s)
        sig = hashlib.sha256(data).hexdigest()[:12]
        _send(chat_id, "❌ GAGAL — format nggak dikenali / dikunci versi baru.\n"
              f"🔖 SHA256: <code>{sig}…</code>\nRequest dukungan: @BleackCoderr", TOOLS_ROW)
        _report_owner(f"🤖 BOT SNIFF ✘\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n👤 {label} (id={uid})\n📄 {fname} ({len(data)} B)\n🔖 {sig}…")

def _poll_loop():
    offset = 0
    try: _api(BOT2_TOKEN, "deleteWebhook")
    except Exception: pass
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
    url = os.environ.get("SELF_PING_URL", "https://sniffconfig.onrender.com/api/stats")
    while True:
        time.sleep(480)
        try: urllib.request.urlopen(url, timeout=15).read()
        except Exception: pass

def start():
    global STARTED
    if not BOT2_TOKEN:
        print("bot2: SNIFF_BOT_TOKEN kosong — dilewati", flush=True); return
    threading.Thread(target=_keepalive_loop, daemon=True, name="keepalive").start()
    threading.Thread(target=_poll_loop, daemon=True, name="sniffbot").start()
    STARTED = True
    print("bot2: v2 jalan ✅ (buttons, leaderboard, facts, grup-ready)", flush=True)
