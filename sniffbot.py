# Sniff Bot v3 — full kreatif: convert/ekstrak, /cek ssh, deteksi pintar, /random pool,
# hasil PNG, level user, streak harian, progress bar, /admin, broadcast, tombol share,
# welcome personal. Setiap fitur punya fallback — bot nggak akan mati gara-gara satu fitur.
import os, sys, json, time, hashlib, socket, random, threading, urllib.request, urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

BOT2_TOKEN = os.environ.get("SNIFF_BOT_TOKEN", "")
OWNER_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
COOLDOWN = 180
STARTED = False
BOT_VERSION = "v3-satset"
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
TOOLS_ROW = [[{"text": "🌐 BUKA WEB", "url": WEB_URL},
              {"text": "👤 CHAT OWNER", "url": "https://t.me/BleackCoderr"},
              {"text": "📢 SHARE BOT", "url": "https://t.me/share/url?url=https://t.me/snifferBC_Bot&text=Sniff%20config%20online%20-%20gratis%20dan%20cepet%20%F0%9F%90%B4"}]]

BASE_DIR = os.path.dirname(__file__)
def _f(name): return os.path.join(BASE_DIR, name)

def _load(name, default):
    try: return json.load(open(_f(name)))
    except Exception: return default
def _save(name, data):
    try: json.dump(data, open(_f(name), "w"))
    except Exception: pass

# ---------- Telegram API ----------
def _api(token, method, **kw):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(kw).encode(), method="POST")
    return json.load(urllib.request.urlopen(req, timeout=35))

def _multipart(method, fields, fname, fdata, ffield="document", ctype="text/plain"):
    b = "----sniffw" + str(int(time.time() * 1000))
    body = b""
    for k, v in fields.items():
        body += f"--{b}\r\nContent-Disposition: form-data; name={k}\r\n\r\n{v}\r\n".encode()
    body += (f"--{b}\r\nContent-Disposition: form-data; name={ffield}; "
             f"filename={fname}\r\nContent-Type: {ctype}\r\n\r\n").encode()
    body += fdata + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{BOT2_TOKEN}/{method}",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=35))

def _send(chat_id, text, buttons=None, reply_to=None):
    """Balas pesan. Return message_id kalau sukses (buat progress edit)."""
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

def _typing(chat_id):
    try: _api(BOT2_TOKEN, "sendChatAction", chat_id=chat_id, action="typing")
    except Exception: pass

def _report_owner(text):
    if not (OWNER_TOKEN and OWNER_CHAT): return
    try: _api(OWNER_TOKEN, "sendMessage", chat_id=OWNER_CHAT, text=text, disable_web_page_preview="true")
    except Exception: pass

# ---------- statistik & user ----------
def _stats(): return _load("stats.json", {"total": 0, "success": 0, "failed": 0})
def _save_stats(s): _save("stats.json", s)

LEVELS = [(0, "🐣 Rooki"), (5, "🔥 Sniffer"), (15, "⚡ Pro"), (30, "👑 Master"), (60, "💎 Legend")]
def _level(n):
    name = LEVELS[0][1]
    for need, nm in LEVELS:
        if n >= need: name = nm
    return name

def _board(): return _load("sniffers.json", {})
def _user(uid, name):
    b = _board()
    e = b.get(str(uid)) or {"name": name, "count": 0, "streak": 0, "last": ""}
    e["name"] = name
    return e, b
def _board_add(uid, name):
    e, b = _user(uid, name)
    today = time.strftime("%Y-%m-%d")
    if e.get("last") != today:
        e["streak"] = e["streak"] + 1 if e.get("last") == time.strftime(
            "%Y-%m-%d", time.localtime(time.time() - 86400)) else 1
        e["last"] = today
    e["count"] = e.get("count", 0) + 1
    b[str(uid)] = e
    _save("sniffers.json", b)
    return e
def _sub(uid):
    s = _load("subscribers.json", [])
    if uid not in s:
        s.append(uid); _save("subscribers.json", s)
def _event(uid, fmt, where):
    ev = _load("events.json", [])
    ev.append({"t": int(time.time()), "u": str(uid), "f": fmt, "w": where})
    _save("events.json", ev[-5000:])
_last = {}
def _cool(uid):
    now = time.time()
    left = COOLDOWN - (now - _last.get(uid, -COOLDOWN))
    if left > 0:
        m, s = divmod(int(left), 60)
        return f"⏳ TUNGGU {m} MENIT {s} DETIK LAGI, SOBRIS!\nJeda 3 menit per orang biar mesinnya nggak ngos-ngosan 😤"
    _last[uid] = now
    return None

# ---------- deteksi pintar (feature 3) ----------
import re as _re
def _smart(result):
    """Highlight otomatis dari isi config decrypted."""
    tips = []
    try:
        m = _re.search(r"\{.*\}", result, _re.S)
        if m:
            j = json.loads(m.group(0))
            cfg = j.get("Config", j)
            if str(cfg.get("blockedByHwid", "")).lower() == "true":
                tips.append("🔐 Config ini DIKUNCI HWID — cuma jalan di device asal")
            if str(cfg.get("lockAllConfig", "")).lower() == "true":
                tips.append("🔒 Semua bagian config dikunci oleh pembuatnya")
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
                tips.append("🖥️ Akun SSH terdeteksi — cek: /cek " + ssh.split("@")[-1].split(":443")[0].split(":80")[0] + " (host:port)")
    except Exception:
        pass
    if not tips:
        tips.append("💡 Config terbuka (nggak dikunci) — bebas dipelajari")
    return "\n".join(tips[:3])

def _extract(result):
    """Feature 1: ekstrak field penting buat pindah aplikasi."""
    try:
        m = _re.search(r"\{.*\}", result, _re.S)
        j = json.loads(m.group(0)); cfg = j.get("Config", j)
        rows = [("Payload", cfg.get("payload")), ("Proxy/SNI", cfg.get("proxy") or cfg.get("sni")),
                ("SSH", cfg.get("sshField") or cfg.get("ssh")), ("SSL/SNI", cfg.get("sni")),
                ("Mode", cfg.get("connectionMode"))]
        out = [f"▸ {k}: {v}" for k, v in rows if v]
        if not out:
            # fallback: tampilkan field string apa pun yang ada
            for k, v in list(cfg.items())[:6]:
                if isinstance(v, str) and len(v) < 300:
                    out.append(f"▸ {k}: {v}")
        return "📋 DATA EKSTRAK — tinggal copy ke aplikasi lain\n" + "─"*28 + "\n" + "\n".join(out) if out else \
               "📋 Field inti nggak ketemu di config ini."
    except Exception:
        return "📋 Config ini nggak punya field JSON standar — ekstrak manual dari hasil."

# ---------- PNG (feature 5) ----------
def _render_png(text):
    try:
        from PIL import Image, ImageDraw
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
        from io import BytesIO
        buf = BytesIO(); img.save(buf, "PNG"); return buf.getvalue()
    except Exception:
        return None

# ---------- /cek ssh (feature 2) ----------
def _cek(arg):
    m = _re.match(r"^(?:([^:@]+)(?::[^@]*)?)?@?([a-zA-Z0-9.\-]+):(\d{1,5})$", arg.strip())
    if not m:
        return "❌ Format salah. Pakai: /cek user:pass@host:port\nContoh: /cek fastssh.com-samarata@uk.sshws.net:443"
    user, host, port = m.group(1), m.group(2), int(m.group(3))
    try:
        ip = socket.gethostbyname(host)
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
        out = (f"🏓 CEK AKUN SSH\n─" * 1 + "─"*27 + f"\n🖥️ {host}:{port} → {ip}\n"
               f"{'👤 ' + user + chr(10) if user else ''}"
               f"✅ PORT TERBUKA — server hidup\n⚡ Respons: {ms} ms")
        if banner: out += f"\n📡 Banner: {banner}"
        out += "\n\nℹ️ Cek koneksi doang, bukan login password."
        return out
    except Exception:
        return f"❌ {host}:{port} TIDAK merespons — port tertutup/server mati/IP diblokir."

WELCOME = (
    "🐴 <b>SNIFF CONFIG BOT v3</b>\n\n"
    "Lempar file config → isi aslinya langsung muncul.\n"
    "Didukung: <code>.HC .EHI .SSC .NPV .NPVT .DARK</code>\n\n"
    "⚡ <b>PERINTAH:</b>\n"
    "/start — mulai\n/help — panduan\n/stats — statistik\n"
    "/top — leaderboard 🏆\n/ping — cek mesin\n/cek user:pass@host:port — cek akun SSH\n"
    "/random — config gratis harian 🎁\n\n"
    "⏳ Jeda 3 menit per orang\n🔒 File diproses lalu dibuang\n👥 Grup-friendly"
)

def _personal(uid, name):
    e, _ = _user(uid, name)
    if not e.get("count"): return ""
    flame = " 🔥" * min(e.get("streak", 0), 5)
    return (f"\n👋 Halo {e['name']}! Sniff ke-<b>{e['count'] + 1}</b> lu\n"
            f"🏅 Level: {_level(e['count'])}{flame}")

def _handle(msg):
    chat_id = msg["chat"]["id"]
    where = "pribadi" if msg["chat"].get("type") == "private" else "grup"
    user = msg.get("from", {})
    uid, uname = user.get("id", chat_id), user.get("username")
    label = ("@" + uname) if uname else (user.get("first_name") or str(chat_id))
    text = (msg.get("text") or "").strip()
    if where == "pribadi" and uid: _sub(chat_id)

    if text.startswith("/start"):
        _send(chat_id, WELCOME + _personal(uid, label), TOOLS_ROW); return
    if text.startswith("/help"):
        _send(chat_id, "📖 <b>PANDUAN</b>\n\n📄 Kirim file config (dokumen) → hasil .txt\n"
              "🔓 Tombol EKSTRAK DATA di hasil → pindah aplikasi\n"
              "🏓 /cek user:pass@host:port → cek server SSH\n"
              "🎁 /random → config gratis\n👥 Di grup: bot cuma bales perintah & file", TOOLS_ROW); return
    if text.startswith("/stats"):
        s = _stats()
        _send(chat_id, f"📊 <b>STATISTIK MESIN</b>\n\n🔢 Total: <b>{s['total']}</b>\n"
              f"✔ Berhasil: <b>{s['success']}</b>\n✘ Gagal: <b>{s['failed']}</b>\n"
              f"👥 Sniffer unik: <b>{len(_board())}</b>" + WATERMARK, TOOLS_ROW); return
    if text.startswith("/top"):
        b = sorted(_board().items(), key=lambda x: -x[1].get("count", 0))[:5]
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
        pool = _load("pool.json", [])
        if not pool:
            _send(chat_id, "🎁 Pool config gratis masih KOSONG.\nOwner belum nyimpen config publik. "
                  "Coba lagi nanti atau ke @BleackCoderr"); return
        try:
            import base64 as b64
            pick = random.choice(pool)
            data = b64.b64decode(pick.get("b64", "")) if isinstance(pick, dict) else b64.b64decode(pick)
            _multipart("sendDocument", {"chat_id": chat_id,
                       "caption": "🎁 Config gratis hari ini — @BleackCoderr"},
                       pick.get("name", "free.config.hc") if isinstance(pick, dict) else "free.config.hc",
                       data)
        except Exception:
            _send(chat_id, "❌ Pool rusak — lapor @BleackCoderr"); return
        return
    if text.startswith("/broadcast"):
        if str(uid) != str(OWNER_CHAT or "x"):
            return
        body = text[len("/broadcast"):].strip()
        if not body:
            _send(chat_id, "Format: /broadcast <pesan> — dikirim ke semua subscriber"); return
        subs = _load("subscribers.json", [])
        ok = 0
        for c in subs:
            if _send(c, "📢 <b>PENGUMUMAN</b>\n\n" + body + WATERMARK): ok += 1
            time.sleep(0.06)
        _send(chat_id, f"✅ Broadcast terkirim ke {ok}/{len(subs)} user"); return
    if text.startswith("/admin"):
        if str(uid) != str(OWNER_CHAT or "x"): return
        s = _stats(); ev = _load("events.json", [])
        day0 = time.strftime("%Y-%m-%d")
        today = [e for e in ev if time.strftime("%Y-%m-%d", time.localtime(e["t"])) == day0]
        hours = {}
        for e in today: hours[time.strftime("%H", time.localtime(e["t"]))] = hours.get(time.strftime("%H", time.localtime(e["t"])), 0) + 1
        busy = max(hours, key=hours.get) if hours else "-"
        fmts = {}
        for e in ev:
            if e["f"]: fmts[e["f"]] = fmts.get(e["f"], 0) + 1
        fmt_top = sorted(fmts.items(), key=lambda x: -x[1])[:3]
        mx = max(hours.values()) if hours else 1
        bar = "\n".join(f"{h}:00 {'█'*int(10*c/mx)} {c}" for h, c in sorted(hours.items())[-8:])
        _send(chat_id, f"🕵️ <b>ADMIN DASHBOARD</b>\n\n📅 Hari ini: {len(today)} sniff | 👥 user unik: "
              f"{len(set(e['u'] for e in today))}\n⏰ Jam tersibuk: {busy}:00\n"
              f"🏷️ Format terpopuler: {', '.join(f'{k} ({v})' for k,v in fmt_top) or '-'}\n\n{bar}\n\n"
              f"📮 Subscriber broadcast: {len(_load('subscribers.json', []))}"); return
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
    mid = _send(chat_id, f"🔎 NGUNYAH <code>{fname}</code> ▓░░░░░ 20%", reply_to=msg.get("message_id"))
    try:
        fp = _api(BOT2_TOKEN, "getFile", file_id=doc["file_id"])["result"]["file_path"]
        data = urllib.request.urlopen(f"https://api.telegram.org/file/bot{BOT2_TOKEN}/{fp}", timeout=35).read()
    except Exception:
        _send(chat_id, "❌ Gagal unduh file — coba lagi."); return
    if mid: _edit(chat_id, mid, f"🔎 NGUNYAH <code>{fname}</code> ▓▓▓░░░ 60%")

    import server
    hint = server.detect_by_ext(fname)
    order = ([p for p in server.PARSERS if p[0] == hint] + [p for p in server.PARSERS if p[0] != hint])
    fmt = result = None
    for f, fn in order:
        try: r = fn(data)
        except Exception: r = None
        if r: fmt, result = f, r; break
    if mid: _edit(chat_id, mid, f"🔎 NGUNYAH <code>{fname}</code> ▓▓▓▓▓▓ 100%")

    s = _stats(); s["total"] += 1
    smart = _smart(result) if result else ""
    if result:
        s["success"] += 1; _save_stats(s)
        e = _board_add(uid, label); _event(uid, fmt, where); _sub(chat_id)
        fact = FACTS[int(time.time()) % len(FACTS)]
        cap = (f"{EMOJI.get(fmt,'✅')} <b>BERHASIL</b> — {fmt} | 🏅 {_level(e['count'])}"
               f"{' 🔥streak ' + str(e['streak']) if e.get('streak', 0) > 1 else ''}\n"
               f"{smart}\n{fact}")
        body = (f"{EMOJI.get(fmt, '✅')} <b>BERHASIL</b> — format {fmt}\n📄 {fname}\n"
                f"🕐 {time.strftime('%d-%m-%Y %H:%M')}\n{'─'*30}\n\n{result}\n\n{smart}" + WATERMARK)
        png = _render_png(result)
        sent = False
        if png:
            try:
                _multipart("sendPhoto", {"chat_id": chat_id, "caption": cap[:1000],
                          "reply_markup": json.dumps({"inline_keyboard": [[
                              {"text": "📋 EKSTRAK DATA", "callback_data": f"ex:{uid}:{int(time.time())}"},
                              {"text": "🔓 UNLOCK .HC", "callback_data": f"ul:{uid}:{int(time.time())}"},
                              {"text": "🌐 WEB", "url": WEB_URL}]]})},
                          fname + ".sniff.png", png, ffield="photo", ctype="image/png")
                sent = True
            except Exception:
                sent = False
        if not sent:
            try:
                _multipart("sendDocument",
                           {"chat_id": chat_id, "caption": cap[:1000],
                            "reply_markup": json.dumps({"inline_keyboard": [[
                                {"text": "📋 EKSTRAK DATA", "callback_data": f"ex:{uid}:{int(time.time())}"},
                                {"text": "🔓 UNLOCK .HC", "callback_data": f"ul:{uid}:{int(time.time())}"},
                                {"text": "🌐 WEB", "url": WEB_URL}]]})},
                           fname + ".sniffed.txt", body.encode())
            except Exception:
                for i in range(0, len(body), 3900): _send(chat_id, body[i:i+3900])
        # simpen hasil terakhir buat tombol EKSTRAK (cache 100)
        cache = _load("extract_cache.json", {})
        cache[str(uid)] = {"r": result[:20000], "t": time.time()}
        _save("extract_cache.json", {k: v for k, v in list(cache.items())[-100:]})
        if fmt == "HC":
            fc = _load("file_cache.json", {})
            fc[str(uid)] = {"b64": base64.b64encode(data).decode(), "name": fname, "t": time.time()}
            _save("file_cache.json", {k: v for k, v in list(fc.items())[-100:]})
        _report_owner(f"🤖 BOT SNIFF ✔ [{BOT_VERSION}]\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n"
                      f"👤 {label} (id={uid})\n📄 {fname} ({len(data)} B)\n🏷️ {fmt}\n📍 {where}")
    else:
        s["failed"] += 1; _save_stats(s); _event(uid, None, where)
        sig = hashlib.sha256(data).hexdigest()[:12]
        _send(chat_id, "❌ GAGAL — format nggak dikenali / dikunci versi baru.\n"
              f"🔖 SHA256: <code>{sig}…</code>\nRequest dukungan: @BleackCoderr", TOOLS_ROW)
        _report_owner(f"🤖 BOT SNIFF ✘\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n👤 {label} (id={uid})\n📄 {fname} ({len(data)} B)\n🔖 {sig}…")

def _on_callback(cb):
    uid = str(cb.get("from", {}).get("id", ""))
    data = cb.get("data", "")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    try: _api(BOT2_TOKEN, "answerCallbackQuery", callback_query_id=cb["id"])
    except Exception: pass
    if data.startswith("ul:") and chat_id:
        fc = _load("file_cache.json", {})
        hit = fc.get(uid)
        if not hit:
            _send(chat_id, "⌛ Cache file lu kedaluwarsa — kirim ulang file .hc-nya."); return
        try:
            import hcunlock
            raw = base64.b64decode(hit["b64"])
            out = hcunlock.unlock_hc_file(raw)
            name = hit["name"].rsplit(".", 1)[0] + ".unlocked.hc"
            _multipart("sendDocument", {"chat_id": chat_id,
                       "caption": "🔓 UNLOCKED — proteksi mati, expiry lifeTime. Import langsung ke HTTP Custom.\n🐴 @BleackCoderr"},
                       name, out)
            _report_owner(f"🔓 HC UNLOCKED\n👤 id={uid}\n📄 {hit['name']}")
        except Exception as e:
            _send(chat_id, f"❌ Unlock gagal: {e}\nCuma format .HC yang didukung saat ini."); return
        return
    if data.startswith("ex:") and chat_id:
        cache = _load("extract_cache.json", {})
        hit = cache.get(uid)
        if not hit:
            _send(chat_id, "⌛ Cache hasil lu udah kedaluwarsa — kirim ulang file-nya."); return
        _send(chat_id, _extract(hit["r"]) + WATERMARK)

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
    threading.Thread(target=_keepalive_loop, daemon=True, name="keepalive").start()
    threading.Thread(target=_poll_loop, daemon=True, name="sniffbot").start()
    STARTED = True
    print(f"bot2: {BOT_VERSION} jalan ✅ (convert, cek, png, level, streak, admin, broadcast)", flush=True)
