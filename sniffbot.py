# Sniff Bot v3.2 — animasi proses, admin bebas cooldown, cache PERSISTEN (pinned-file DB),
# hasil ekstrak pakai bubble <code> (tap 1x = tersalin), NGUNYAH auto-hapus,
# semua output reply ke file asli, waktu proses di caption.
import os, sys, json, time, hashlib, socket, random, threading, urllib.request, urllib.parse, base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

BOT2_TOKEN = os.environ.get("SNIFF_BOT_TOKEN", "")
OWNER_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
COOLDOWN = 180
STARTED = False
BOT_VERSION = "v4-plaintext-surgical"
WATERMARK = "\n\n🐴 SNIFF CONFIG — diolah oleh @BleackCoderr ✦\n🌐 https://sniffconfig.onrender.com"
WEB_URL = "https://sniffconfig.onrender.com"

EMOJI = {"HC": "🐴", "EHI": "💉", "SSC": "🔐", "NPVT": "🛰️", "DARK": "🌑"}
FACTS = [
    "💡 Config yang dikunci HWID cuma bisa dibuka di device asalnya.",
    "💡 Format .ehi & .hc beda aplikasi tapi isinya mirip trik.",
    "💡 Kalau gagal terus, kemungkinan key-nya versi baru — lapor @BleackCoderr!",
    "💡 Web-nya juga bisa nge-sniff: sniffconfig.onrender.com",
    "💡 Share bot ini ke grup — makin rame makin semangat 🔥",
    "💡 Cek akun SSH lu: /cek user:pass@host:port",
]
SPIN = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
TOOLS_ROW = [[{"text": "🌐 BUKA WEB", "url": WEB_URL},
              {"text": "👤 CHAT OWNER", "url": "https://t.me/BleackCoderr"},
              {"text": "📢 SHARE BOT", "url": "https://t.me/share/url?url=https://t.me/snifferBC_Bot&text=Sniff%20config%20online%20-%20gratis%20dan%20cepet%20%F0%9F%90%B4"}]]

BASE_DIR = os.path.dirname(__file__)
def _f(name): return os.path.join(BASE_DIR, name)

# ══════════ PERSISTEN DB (Render filesystem ephemeral!) ══════════
# Semua state disimpan di 1 file botdata.json, di-backup ke chat owner (pesan PINNED).
# Startup: restore dari pesan pinned. Tiap perubahan: tulis lokal + sync cloud (debounce).
DB = {"sniffers": {}, "file_cache": {}, "extract_cache": {}, "subscribers": [], "events": [], "pin_id": None}
_db_timer = None

def _load_db():
    """1) coba file lokal 2) coba pinned message di chat owner."""
    global DB
    local = _f("botdata.json")
    try:
        DB.update(json.load(open(local))); print("db: restore dari file lokal", flush=True)
    except Exception:
        pass
    try:
        if OWNER_TOKEN and OWNER_CHAT:
            info = _api(OWNER_TOKEN, "getChat", chat_id=OWNER_CHAT)
            pm = info.get("result", {}).get("pinned_message")
            if pm and pm.get("document") and "#db:botdata" in (pm.get("caption") or ""):
                fid = pm["document"]["file_id"]
                fp = _api(OWNER_TOKEN, "getFile", file_id=fid)["result"]["file_path"]
                cloud = json.loads(urllib.request.urlopen(
                    f"https://api.telegram.org/file/bot{OWNER_TOKEN}/{fp}", timeout=35).read())
                for k, v in cloud.items(): DB[k] = v
                print("db: restore dari pinned cloud ✅", flush=True)
    except Exception as e:
        print("db: restore cloud skip:", e, flush=True)

def _sync_cloud():
    """Kirim botdata.json ke owner chat + pin. Gagal = diam-diam (lokal tetap ada)."""
    if not (OWNER_TOKEN and OWNER_CHAT): return
    try:
        data = json.dumps(DB, ensure_ascii=False).encode()
        mid = _send_doc(OWNER_TOKEN, OWNER_CHAT, "botdata.json", data, "#db:botdata")
        if not mid: return
        new_pin = mid
        old = DB.get("pin_id")
        if old:
            try: _api(OWNER_TOKEN, "unpinChatMessage", chat_id=OWNER_CHAT, message_id=old)
            except Exception: pass
        try: _api(OWNER_TOKEN, "pinChatMessage", chat_id=OWNER_CHAT, message_id=new_pin)
        except Exception: pass
        DB["pin_id"] = new_pin
    except Exception:
        pass

def _schedule_sync():
    global _db_timer
    try:
        if _db_timer: _db_timer.cancel()
    except Exception: pass
    _db_timer = threading.Timer(8.0, _sync_cloud)
    _db_timer.daemon = True
    _db_timer.start()

def _save(name, data):
    DB[name] = data
    try: json.dump(DB, open(_f("botdata.json"), "w"))
    except Exception: pass
    _schedule_sync()

def _load(name, default):
    return DB.get(name, default)

# ══════════ Telegram API ══════════
def _api(token, method, **kw):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(kw).encode(), method="POST")
    return json.load(urllib.request.urlopen(req, timeout=35))

def _send_doc(token, chat_id, fname, fdata, caption=""):
    """Kirim document via token mana pun. Return message_id atau None."""
    try:
        b = "----db" + str(int(time.time() * 1000))
        body = f"--{b}\r\nContent-Disposition: form-data; name=chat_id\r\n\r\n{chat_id}\r\n".encode()
        if caption:
            body += f"--{b}\r\nContent-Disposition: form-data; name=caption\r\n\r\n{caption}\r\n".encode()
        body += (f"--{b}\r\nContent-Disposition: form-data; name=document; "
                 f"filename={fname}\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
        body += fdata + f"\r\n--{b}--\r\n".encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendDocument",
                                     data=body, method="POST",
                                     headers={"Content-Type": f"multipart/form-data; boundary={b}"})
        r = json.load(urllib.request.urlopen(req, timeout=35))
        return r["result"]["message_id"]
    except Exception:
        return None

def _multipart(method, fields, fname, fdata, ffield="document", ctype="text/plain", reply_to=None):
    b = "----sniffw" + str(int(time.time() * 1000))
    body = b""
    for k, v in fields.items():
        body += f"--{b}\r\nContent-Disposition: form-data; name={k}\r\n\r\n{v}\r\n".encode()
    if reply_to:
        body += f"--{b}\r\nContent-Disposition: form-data; name=reply_to_message_id\r\n\r\n{reply_to}\r\n".encode()
    body += (f"--{b}\r\nContent-Disposition: form-data; name={ffield}; "
             f"filename={fname}\r\nContent-Type: {ctype}\r\n\r\n").encode()
    body += fdata + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{BOT2_TOKEN}/{method}",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=35))

def _send(chat_id, text, buttons=None, reply_to=None):
    if not BOT2_TOKEN: return None
    kw = {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    if buttons: kw["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    if reply_to: kw["reply_to_message_id"] = reply_to
    try:
        r = _api(BOT2_TOKEN, "sendMessage", parse_mode="HTML", **kw)
        return r["result"]["message_id"]
    except Exception:
        try:
            import re
            clean = re.sub(r"</?(b|i|code|a|u|s)[^>]*>", "", text)
            kw2 = {"chat_id": chat_id, "text": clean, "disable_web_page_preview": "true"}
            if buttons: kw2["reply_markup"] = kw["reply_markup"]
            if reply_to: kw2["reply_to_message_id"] = reply_to
            r = _api(BOT2_TOKEN, "sendMessage", **kw2)
            return r["result"]["message_id"]
        except Exception:
            return None

def _edit(chat_id, message_id, text):
    try: _api(BOT2_TOKEN, "editMessageText", chat_id=chat_id, message_id=message_id, text=text)
    except Exception: pass

def _delete(chat_id, message_id):
    try: _api(BOT2_TOKEN, "deleteMessage", chat_id=chat_id, message_id=message_id)
    except Exception: pass

def _typing(chat_id):
    try: _api(BOT2_TOKEN, "sendChatAction", chat_id=chat_id, action="typing")
    except Exception: pass

def _report_owner(text):
    if not (OWNER_TOKEN and OWNER_CHAT): return
    try: _api(OWNER_TOKEN, "sendMessage", chat_id=OWNER_CHAT, text=text, disable_web_page_preview="true")
    except Exception: pass

# ══════════ level / user / event ══════════
def _stats(): return DB.get("stats", {"total": 0, "success": 0, "failed": 0})
def _save_stats(s): _save("stats", s)

LEVELS = [(0, "🐣 Rooki"), (5, "🔥 Sniffer"), (15, "⚡ Pro"), (30, "👑 Master"), (60, "💎 Legend")]
def _level(n):
    name = LEVELS[0][1]
    for need, nm in LEVELS:
        if n >= need: name = nm
    return name

def _user(uid, name):
    b = DB.get("sniffers", {})
    e = b.get(str(uid)) or {"name": name, "count": 0, "streak": 0, "last": ""}
    e["name"] = name
    return e

def _board_add(uid, name):
    e = _user(uid, name)
    b = DB.get("sniffers", {})
    today = time.strftime("%Y-%m-%d")
    if e.get("last") != today:
        e["streak"] = e["streak"] + 1 if e.get("last") == time.strftime(
            "%Y-%m-%d", time.localtime(time.time() - 86400)) else 1
        e["last"] = today
    e["count"] = e.get("count", 0) + 1
    b[str(uid)] = e
    _save("sniffers", b)
    return e

def _sub(chat_id):
    s = DB.get("subscribers", [])
    if chat_id not in s:
        s.append(chat_id); _save("subscribers", s)

def _event(uid, fmt, where):
    ev = DB.get("events", [])
    ev.append({"t": int(time.time()), "u": str(uid), "f": fmt, "w": where})
    _save("events", ev[-5000:])

_last = {}
def _cool(uid):
    # admin (owner) bebas jeda — butuh testing bebas 😄
    if OWNER_CHAT and str(uid) == str(OWNER_CHAT): return None
    now = time.time()
    left = COOLDOWN - (now - _last.get(uid, -COOLDOWN))
    if left > 0:
        m, s = divmod(int(left), 60)
        return f"⏳ TUNGGU {m} MENIT {s} DETIK LAGI, SOBRIS!\nJeda 3 menit per orang biar mesinnya nggak ngos-ngosan 😤"
    _last[uid] = now
    return None

# ══════════ deteksi pintar & ekstrak ══════════
import re as _re
def _smart(result):
    tips = []
    try:
        m = _re.search(r"\{.*\}", result, _re.S)
        if m:
            j = json.loads(m.group(0))
            cfg = j.get("Config", j)
            if str(cfg.get("blockedByHwid", "")).lower() == "true":
                tips.append("🔐 Config ini DIKUNCI HWID — unlock dengan tombol 🔓 UNLOCK .HC")
            if str(cfg.get("lockAllConfig", "")).lower() == "true":
                tips.append("🔒 Semua bagian config dikunci — unlock dengan tombol 🔓")
            exp = str(cfg.get("expiryTime", ""))
            if exp and exp != "lifeTime" and exp.replace(".", "").isdigit():
                try:
                    days = (float(exp) / 1000 - time.time()) / 86400
                    tips.append(f"⏰ Masa aktif config: ~{int(days)} hari lagi" if days > 0
                                else "☠️ Masa aktif config: SUDAH HABIS")
                except Exception: pass
            elif exp == "lifeTime":
                tips.append("♾️ Masa aktif: LIFE TIME")
            ssh = cfg.get("sshField", "") or cfg.get("ssh", "")
            if ssh and "@" in ssh:
                tips.append("🖥️ Akun SSH terdeteksi — cek: /cek " +
                            ssh.split("@")[-1].split(":443")[0].split(":80")[0].split(":8")[0] + " (host:port)")
    except Exception:
        pass
    if not tips:
        tips.append("💡 Config terbuka (nggak dikunci) — bebas dipelajari")
    return "\n".join(tips[:3])

def _extract(result, as_bubbles=True):
    """Field penting dalam bubble <code> — di Telegram, tap 1x = langsung tersalin."""
    rows = []
    try:
        m = _re.search(r"\{.*\}", result, _re.S)
        j = json.loads(m.group(0)); cfg = j.get("Config", j)
        for k, v in [("Payload", cfg.get("payload")), ("Proxy/SNI", cfg.get("proxy") or cfg.get("sni")),
                     ("SSH", cfg.get("sshField") or cfg.get("ssh")),
                     ("Mode", cfg.get("connectionMode")), ("SNI", cfg.get("sni"))]:
            if v:
                s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                rows.append((k, s[:700]))
    except Exception:
        pass
    if not rows:
        return "📋 Field inti nggak ketemu — ekstrak manual dari hasil sniff."
    if as_bubbles:
        lines = [f"<b>{k}</b> — tap buat salin:\n<code>{v}</code>" for k, v in rows]
    else:
        lines = [f"▸ {k}: {v}" for k, v in rows]
    return "📋 DATA EKSTRAK — tap tiap kotak = langsung tersalin ✅\n" + "─" * 28 + "\n" + "\n\n".join(lines)

# ══════════ PNG ══════════
def _render_png(text):
    try:
        from PIL import Image, ImageDraw
        from io import BytesIO
        lines = text.split("\n")
        wrapped = []
        for ln in lines[:60]:
            while len(ln) > 70:
                wrapped.append(ln[:70]); ln = ln[70:]
            wrapped.append(ln)
        wrapped = wrapped[:70]
        W, H = 760, 40 + len(wrapped) * 16 + 30
        img = Image.new("RGB", (W, H), (13, 17, 23))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 30], fill=(22, 27, 34))
        d.text((10, 8), "SNIFF CONFIG TERMINAL — @BleackCoderr", fill=(240, 190, 60))
        d.text((10, 40), "\n".join(wrapped), fill=(200, 247, 160))
        buf = BytesIO(); img.save(buf, "PNG"); return buf.getvalue()
    except Exception:
        return None

# ══════════ /cek ssh ══════════
def _cek(arg):
    m = _re.match(r"^(?:([^:@]+)(?::[^@]*)?)?@?([a-zA-Z0-9.\-]+):(\d{1,5})$", arg.strip())
    if not m:
        return "❌ Format salah. Pakai: /cek user:pass@host:port\nContoh: /cek fastssh.com-samarata@uk.sshws.net:443"
    user, host, port = m.group(1), m.group(2), int(m.group(3))
    try: ip = socket.gethostbyname(host)
    except Exception:
        return f"❌ Host {host} nggak bisa di-resolve — domain mati/typo."
    t0 = time.time()
    try:
        s = socket.create_connection((host, port), timeout=6)
        s.settimeout(4)
        try: banner = s.recv(128).decode(errors="ignore").strip()[:60]
        except Exception: banner = ""
        s.close()
        ms = int((time.time() - t0) * 1000)
        out = ("🏓 CEK AKUN SSH\n" + "─" * 28 +
               f"\n🖥️ {host}:{port} → {ip}\n" +
               (f"👤 {user}\n" if user else "") +
               f"✅ PORT TERBUKA — server hidup\n⚡ Respons: {ms} ms")
        if banner: out += f"\n📡 Banner: {banner}"
        return out + "\n\nℹ️ Cek koneksi doang, bukan login password."
    except Exception:
        return f"❌ {host}:{port} TIDAK merespons — port tertutup/server mati/IP diblokir."

WELCOME = (
    "🐴 <b>SNIFF CONFIG BOT v3.2</b>\n\n"
    "Lempar file config → isi aslinya langsung muncul.\n"
    "Didukung: <code>.HC .EHI .SSC .NPV .NPVT .DARK</code>\n\n"
    "⚡ <b>PERINTAH:</b>\n"
    "/start — mulai\n/help — panduan\n/stats — statistik\n"
    "/top — leaderboard 🏆\n/ping — cek mesin\n/cek user:pass@host:port — cek SSH\n"
    "/random — config gratis 🎁\n\n"
    "⏳ Jeda 3 menit per orang\n🔒 File diproses lalu dibuang\n👥 Grup-friendly"
)

def _personal(uid, name):
    e = _user(uid, name)
    if not e.get("count"): return ""
    flame = " 🔥" * min(e.get("streak", 0), 5)
    return (f"\n👋 Halo {e['name']}! Sniff ke-<b>{e['count'] + 1}</b> lu\n"
            f"🏅 Level: {_level(e['count'])}{flame}")

# ══════════ ANIMASI NGUNYAH ══════════
_anim = {}   # uid -> {"chat":, "mid":, "stop": Event}
def _animate(uid, chat_id, mid, fname):
    i = 0
    try:
        for step in range(8):   # max ~6 detik, jangan kepanjangan
            if _anim.get(uid, {}).get("stop").is_set(): return
            pct = min(15 + step * 10, 90)
            bar = "▓" * (pct // 12) + "░" * (8 - pct // 12)
            _edit(chat_id, mid,
                  f"{SPIN[i % len(SPIN)]} MESIN NGUNYAH <code>{fname}</code>\n{bar} {pct}%")
            i += 1
            time.sleep(0.7)
    except Exception:
        pass

def _stop_anim(uid):
    e = _anim.pop(uid, None)
    if e: e["stop"].set()
    return e

# ══════════ HANDLER UTAMA ══════════
def _handle(msg):
    chat_id = msg["chat"]["id"]
    where = "pribadi" if msg["chat"].get("type") == "private" else "grup"
    user = msg.get("from", {})
    uid, uname = user.get("id", chat_id), user.get("username")
    label = ("@" + uname) if uname else (user.get("first_name") or str(chat_id))
    text = (msg.get("text") or "").strip()
    if where == "pribadi" and uid: _sub(chat_id)
    orig_mid = msg.get("message_id")

    if text.startswith("/start"):
        _send(chat_id, WELCOME + _personal(uid, label), TOOLS_ROW); return
    if text.startswith("/help"):
        _send(chat_id, "📖 <b>PANDUAN</b>\n\n📄 Kirim file config (dokumen) → hasil otomatis\n"
              "📋 Tombol EKSTRAK DATA → tap kotak = tersalin\n"
              "🔓 Tombol UNLOCK .HC → file .hc bebas proteksi\n"
              "🏓 /cek user:pass@host:port → cek server SSH\n"
              "🎁 /random → config gratis\n👥 Di grup: hasil reply ke file kamu", TOOLS_ROW); return
    if text.startswith("/stats"):
        s = _stats()
        _send(chat_id, f"📊 <b>STATISTIK MESIN</b>\n\n🔢 Total: <b>{s['total']}</b>\n"
              f"✔ Berhasil: <b>{s['success']}</b>\n✘ Gagal: <b>{s['failed']}</b>\n"
              f"👥 Sniffer unik: <b>{len(DB.get('sniffers', {}))}</b>" + WATERMARK, TOOLS_ROW); return
    if text.startswith("/top"):
        b = sorted(DB.get("sniffers", {}).items(), key=lambda x: -x[1].get("count", 0))[:5]
        if not b:
            _send(chat_id, "🏆 BELUM ADA SKOR — jadi sniff pertama!"); return
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        rows = "\n".join(f"{medal[i]} {e['name']} — <b>{e['count']}x</b> ({_level(e['count'])})"
                         for i, (_, e) in enumerate(b))
        _send(chat_id, f"🏆 <b>TOP SNIFFERS</b>\n\n{rows}" + WATERMARK); return
    if text.startswith("/ping"):
        t0 = time.time(); _typing(chat_id)
        _send(chat_id, f"🏓 PONG! Mesin ngebut — {int((time.time()-t0)*1000)} ms ✅ [{BOT_VERSION}]"); return
    if text.startswith("/cek"):
        arg = text[4:].strip()
        if not arg:
            _send(chat_id, "Format: /cek user:pass@host:port"); return
        _typing(chat_id); _send(chat_id, "🏓 Ngecek server…")
        _send(chat_id, _cek(arg) + WATERMARK); return
    if text.startswith("/random"):
        pool = DB.get("pool", [])
        if not pool:
            _send(chat_id, "🎁 Pool config gratis masih KOSONG.\nOwner belum nyimpen config publik. "
                  "Coba lagi nanti atau ke @BleackCoderr"); return
        try:
            pick = random.choice(pool)
            data = base64.b64decode(pick.get("b64", "")) if isinstance(pick, dict) else base64.b64decode(pick)
            _multipart("sendDocument", {"chat_id": chat_id,
                       "caption": "🎁 Config gratis hari ini — @BleackCoderr"},
                       pick.get("name", "free.config.hc") if isinstance(pick, dict) else "free.config.hc",
                       data)
        except Exception:
            _send(chat_id, "❌ Pool rusak — lapor @BleackCoderr"); return
        return
    if text.startswith("/broadcast"):
        if str(uid) != str(OWNER_CHAT or "x"): return
        body = text[len("/broadcast"):].strip()
        if not body:
            _send(chat_id, "Format: /broadcast <pesan> — dikirim ke semua subscriber"); return
        subs = DB.get("subscribers", [])
        ok = 0
        for c in subs:
            if _send(c, "📢 <b>PENGUMUMAN</b>\n\n" + body + WATERMARK): ok += 1
            time.sleep(0.06)
        _send(chat_id, f"✅ Broadcast terkirim ke {ok}/{len(subs)} user"); return
    if text.startswith("/admin"):
        if str(uid) != str(OWNER_CHAT or "x"): return
        s = _stats(); ev = DB.get("events", [])
        day0 = time.strftime("%Y-%m-%d")
        today = [e for e in ev if time.strftime("%Y-%m-%d", time.localtime(e["t"])) == day0]
        hours = {}
        for e in today:
            h = time.strftime("%H", time.localtime(e["t"]))
            hours[h] = hours.get(h, 0) + 1
        busy = max(hours, key=hours.get) if hours else "-"
        fmts = {}
        for e in ev:
            if e["f"]: fmts[e["f"]] = fmts.get(e["f"], 0) + 1
        fmt_top = sorted(fmts.items(), key=lambda x: -x[1])[:3]
        mx = max(hours.values()) if hours else 1
        bar = "\n".join(f"{h}:00 {'█' * int(10 * c / mx)} {c}" for h, c in sorted(hours.items())[-8:])
        _send(chat_id, f"🕵️ <b>ADMIN DASHBOARD</b>\n\n📅 Hari ini: {len(today)} sniff | 👥 user unik: "
              f"{len(set(e['u'] for e in today))}\n⏰ Jam tersibuk: {busy}:00\n"
              f"🏷️ Format terpopuler: {', '.join(f'{k} ({v})' for k, v in fmt_top) or '-'}\n\n{bar}\n\n"
              f"📮 Subscriber broadcast: {len(DB.get('subscribers', []))}\n"
              f"💾 Cache file: {len(DB.get('file_cache', {}))} | DB cloud: {'✅' if DB.get('pin_id') else 'belum'}"); return
    if text.startswith("/"):
        return

    doc = msg.get("document")
    if not doc:
        if where == "private":
            _send(chat_id, "🤔 Kirim <b>file config</b> ya — bukan teks.\nFormat: .hc .ehi .ssc .npv .npvt .dark"); return
        return
    wait = _cool(uid)
    if wait: _send(chat_id, wait); return
    fname, fsize = doc.get("file_name", "config.bin"), doc.get("file_size", 0)
    if fsize > 5 * 1024 * 1024:
        _send(chat_id, "❌ File maks 5MB, Bro."); return

    _typing(chat_id)
    mid = _send(chat_id, f"{SPIN[0]} MESIN NGUNYAH <code>{fname}</code>\n▓░░░░░░░ 12%", reply_to=orig_mid)
    if mid:
        _anim[uid] = {"chat": chat_id, "mid": mid, "stop": threading.Event()}
        threading.Thread(target=_animate, args=(uid, chat_id, mid, fname), daemon=True).start()
    t_start = time.time()
    try:
        fp = _api(BOT2_TOKEN, "getFile", file_id=doc["file_id"])["result"]["file_path"]
        data = urllib.request.urlopen(f"https://api.telegram.org/file/bot{BOT2_TOKEN}/{fp}", timeout=35).read()
    except Exception:
        _stop_anim(uid)
        if mid: _delete(chat_id, mid)
        _send(chat_id, "❌ Gagal unduh file — coba lagi."); return

    import server
    hint = server.detect_by_ext(fname)
    order = ([p for p in server.PARSERS if p[0] == hint] + [p for p in server.PARSERS if p[0] != hint])
    fmt = result = None
    for f, fn in order:
        try: r = fn(data)
        except Exception: r = None
        if r: fmt, result = f, r; break
    elapsed = time.time() - t_start

    # animasi berhenti + pesan NGUNYAH DIHAPUS (chat bersih)
    _stop_anim(uid)
    if mid: _delete(chat_id, mid)

    s = _stats(); s["total"] += 1
    smart = _smart(result) if result else ""
    timeinfo = f"⏱️ Diproses {elapsed:.1f} detik • {BOT_VERSION}"
    if result:
        s["success"] += 1; _save_stats(s)
        e = _board_add(uid, label); _event(uid, fmt, where); _sub(chat_id)
        fact = FACTS[int(time.time()) % len(FACTS)]
        cap = (f"{EMOJI.get(fmt, '✅')} <b>BERHASIL</b> — {fmt} | 🏅 {_level(e['count'])}"
               f"{' 🔥streak ' + str(e['streak']) if e.get('streak', 0) > 1 else ''}\n"
               f"{smart}\n{fact}\n{timeinfo}")
        body = (f"{EMOJI.get(fmt, '✅')} <b>BERHASIL</b> — format {fmt}\n📄 {fname}\n"
                f"🕐 {time.strftime('%d-%m-%Y %H:%M')}\n{'─' * 30}\n\n{result}\n\n{smart}" + WATERMARK)
        btns = [[{"text": "📋 EKSTRAK DATA", "callback_data": f"ex:{uid}"},
                 {"text": "🔓 UNLOCK .HC", "callback_data": f"ul:{uid}"},
                 {"text": "🌐 WEB", "url": WEB_URL}]]
        # hasil reply ke file asli (orig_mid)
        png = _render_png(result)
        sent = False
        if png:
            try:
                _multipart("sendPhoto", {"chat_id": chat_id, "caption": cap[:1000],
                          "reply_markup": json.dumps({"inline_keyboard": btns})},
                          fname + ".sniff.png", png, ffield="photo", ctype="image/png",
                          reply_to=orig_mid)
                sent = True
            except Exception:
                sent = False
        if not sent:
            try:
                _multipart("sendDocument",
                           {"chat_id": chat_id, "caption": cap[:1000],
                            "reply_markup": json.dumps({"inline_keyboard": btns})},
                           fname + ".sniffed.txt", body.encode(), reply_to=orig_mid)
            except Exception:
                _send(chat_id, body[:3900], reply_to=orig_mid)
        # cache: file asli + message_id file (buat reply export) + hasil extract
        ec = DB.get("extract_cache", {})
        ec[str(uid)] = {"r": result[:20000], "t": time.time()}
        _save("extract_cache", {k: v for k, v in list(ec.items())[-100:]})
        if fmt == "HC":
            fc = DB.get("file_cache", {})
            fc[str(uid)] = {"b64": base64.b64encode(data).decode(), "name": fname,
                            "mid": orig_mid, "t": time.time()}
            _save("file_cache", {k: v for k, v in list(fc.items())[-100:]})
        _report_owner(f"🤖 BOT SNIFF ✔ [{BOT_VERSION}]\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n"
                      f"👤 {label} (id={uid})\n📄 {fname} ({len(data)} B)\n🏷️ {fmt}\n📍 {where}")
    else:
        s["failed"] += 1; _save_stats(s); _event(uid, None, where)
        sig = hashlib.sha256(data).hexdigest()[:12]
        _send(chat_id, "❌ GAGAL — format nggak dikenali / dikunci versi baru.\n"
              f"🔖 SHA256: <code>{sig}…</code>\nRequest dukungan: @BleackCoderr", TOOLS_ROW,
              reply_to=orig_mid)
        _report_owner(f"🤖 BOT SNIFF ✘\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n👤 {label} (id={uid})\n📄 {fname} ({len(data)} B)\n🔖 {sig}…")

def _on_callback(cb):
    uid = str(cb.get("from", {}).get("id", ""))
    data = cb.get("data", "")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    try: _api(BOT2_TOKEN, "answerCallbackQuery", callback_query_id=cb["id"])
    except Exception: pass
    if data.startswith("ul:") and chat_id:
        fc = DB.get("file_cache", {})
        hit = fc.get(uid)
        if not hit:
            _send(chat_id, "⌛ Cache file lu kedaluwarsa — kirim ulang file .hc-nya."); return
        try:
            import hcunlock
            raw = base64.b64decode(hit["b64"])
            out = hcunlock.unlock_hc_file(raw)
            name = hit["name"].rsplit(".", 1)[0] + ".unlocked.hc"
            _multipart("sendDocument",
                       {"chat_id": chat_id,
                        "caption": "🔓 UNLOCKED — proteksi mati, expiry lifeTime. Import langsung ke HTTP Custom.\n🐴 @BleackCoderr"},
                       name, out, reply_to=hit.get("mid"))   # reply ke file asli
            _report_owner(f"🔓 HC UNLOCKED\n👤 id={uid}\n📄 {hit['name']}")
        except Exception as e:
            _send(chat_id, f"❌ Unlock gagal: {e}\nCuma format .HC yang didukung saat ini."); return
        return
    if data.startswith("ex:") and chat_id:
        ec = DB.get("extract_cache", {})
        hit = ec.get(uid)
        if not hit:
            _send(chat_id, "⌛ Cache hasil lu kedaluwarsa — kirim ulang file-nya."); return
        _send(chat_id, _extract(hit["r"]) + WATERMARK, reply_to=hit.get("mid"))

def _poll_loop():
    offset = 0
    try: _api(BOT2_TOKEN, "deleteWebhook")
    except Exception: pass
    while True:
        try:
            ups = _api(BOT2_TOKEN, "getUpdates", offset=offset, timeout=25)["result"]
            for u in ups:
                offset = max(offset, u["update_id"] + 1)
                if u.get("callback_query"):
                    try: _on_callback(u["callback_query"])
                    except Exception as e: print("bot2 cb:", e, flush=True)
                    continue
                m = u.get("message") or u.get("edited_message")
                if m:
                    try: _handle(m)
                    except Exception as e: print("bot2 handle:", e, flush=True)
        except Exception:
            time.sleep(5)

def _keepalive_loop():
    url = os.environ.get("SELF_PING_URL", WEB_URL + "/api/stats")
    while True:
        time.sleep(480)
        try: urllib.request.urlopen(url, timeout=15).read()
        except Exception: pass

def start():
    global STARTED
    if not BOT2_TOKEN:
        print("bot2: SNIFF_BOT_TOKEN kosong — dilewati", flush=True); return
    _load_db()   # restore cache dari pinned cloud (cache nggak hilang lagi!)
    threading.Thread(target=_keepalive_loop, daemon=True, name="keepalive").start()
    threading.Thread(target=_poll_loop, daemon=True, name="sniffbot").start()
    STARTED = True
    print(f"bot2: {BOT_VERSION} jalan ✅ (animasi, admin-bebas-cooldown, db persisten)", flush=True)
