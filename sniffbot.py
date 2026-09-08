# ═══════════════════════════════════════════════════════════════
# SNIFF CONFIG BOT v7 — perombakan total (@BleackCoderr)
# Rapi menyeluruh + fitur baru:
#  • HTML-escape semua input user (bug lama: nama file dgn & < > bikin pesan gagal)
#  • /profile — kartu anggota: level, progress bar, badge per format, peringkat
#  • /checkin — absen harian, bonus skor
#  • /ref — sistem referral (ajak teman → bonus saat dia pertama sniff sukses)
#  • /history — 8 sniff terakhir si user
#  • Tombol 📩 KIRIM KE PV — di grup, hasil bisa dikirim diam-diam ke pribadi
#  • Milestone 🎉 (5/10/25/50/100/200 sniff) + toast callback
#  • /pool — admin nyimpen config gratis (pakai file_id, hemat DB)
#  • Grup: /perintah@namabot jalan, welcome member baru, cooldown bar cantik
#  • /about + uptime, watermark & separator konsisten di SEMUA output
# Engine lama (server.py + engine/) TIDAK disentuh — unlock .HC tetap dihapus (v6).
# ═══════════════════════════════════════════════════════════════
import os, sys, json, time, hashlib, socket, random, threading, urllib.request, urllib.parse, base64
from html import escape as _h

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))

BOT2_TOKEN = os.environ.get("SNIFF_BOT_TOKEN", "")
OWNER_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
COOLDOWN = 180
STARTED = False
BOOT_TIME = time.time()
BOT_VERSION = "v7-rapi"
WEB_URL = "https://sniffconfig.onrender.com"
OWNER_TG = "https://t.me/BleackCoderr"
BOT_LINK = "https://t.me/snifferBC_Bot"

# ── gaya visual konsisten ──────────────────────────────────────
WATERMARK = ("\n\n🐴 <b>SNIFF CONFIG</b> — diolah oleh @BleackCoderr ✦\n"
             f"🌐 {WEB_URL}")
SEP = "───── • ─────"
EMOJI = {"HC": "🐴", "EHI": "💉", "SSC": "🔐", "NPVT": "🛰️", "DARK": "🌑", "NPV": "🛰️"}
FACTS = [
    "💡 Config yang dikunci HWID cuma bisa dibuka di device asalnya.",
    "💡 Format .ehi & .hc beda aplikasi tapi isinya mirip trik.",
    "💡 Kalau gagal terus, kemungkinan key-nya versi baru — lapor @BleackCoderr!",
    "💡 Web-nya juga bisa nge-sniff: sniffconfig.onrender.com",
    "💡 Share bot ini ke grup — makin rame makin semangat 🔥",
    "💡 Cek akun SSH: /cek user:pass@host:port",
    "💡 Rajin /checkin biar streak 🔥 nambah tiap hari!",
    "💡 Ajak teman pake /ref — kalian dua-duanya dapat bonus.",
]
SPIN = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
MILESTONES = {5: "🎉 Sniff ke-5! Lu resmi kecanduan.",
              10: "🔥 10x! Badge <b>Sniffer</b> terpasang di dada.",
              25: "⚡ 25x! Setengah jalan menuju Master.",
              50: "👑 50x! Lu sekarang <b>Master</b> — hormat!",
              100: "💎 100x! <b>LEGEND</b>. Jarang ada yang sampai sini.",
              200: "🏆 200x?! Mesinnya aja capek liat lu. Top 1 sejagat!"}
TOOLS_ROW = [[{"text": "🌐 BUKA WEB", "url": WEB_URL},
              {"text": "👤 CHAT OWNER", "url": OWNER_TG},
              {"text": "📢 SHARE BOT",
               "url": "https://t.me/share/url?url=" + urllib.parse.quote(BOT_LINK) +
                      "&text=" + urllib.parse.quote("Sniff config online - gratis dan cepet 🐴")}]]

BASE_DIR = os.path.dirname(__file__)
def _f(name): return os.path.join(BASE_DIR, name)

# ══════════════ PERSISTEN DB (Render filesystem ephemeral!) ══════════════
# Semua state di 1 file botdata.json, di-backup ke pesan PINNED di chat owner.
DB = {"sniffers": {}, "extract_cache": {}, "subscribers": [], "events": [],
      "pin_id": None, "stats": {"total": 0, "success": 0, "failed": 0}}
_db_timer = None

def _load_db():
    """1) file lokal 2) pinned message di chat owner."""
    global DB
    try:
        DB.update(json.load(open(_f("botdata.json")))); print("db: restore dari file lokal", flush=True)
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
    if not (OWNER_TOKEN and OWNER_CHAT): return
    try:
        data = json.dumps(DB, ensure_ascii=False).encode()
        mid = _send_doc(OWNER_TOKEN, OWNER_CHAT, "botdata.json", data, "#db:botdata")
        if not mid: return
        old = DB.get("pin_id")
        if old:
            try: _api(OWNER_TOKEN, "unpinChatMessage", chat_id=OWNER_CHAT, message_id=old)
            except Exception: pass
        try: _api(OWNER_TOKEN, "pinChatMessage", chat_id=OWNER_CHAT, message_id=mid)
        except Exception: pass
        DB["pin_id"] = mid
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

# ══════════════ Telegram API ══════════════
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

def _send(chat_id, text, buttons=None, reply_to=None, silent=False):
    if not BOT2_TOKEN: return None
    kw = {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    if buttons: kw["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    if reply_to: kw["reply_to_message_id"] = reply_to
    if silent: kw["disable_notification"] = "true"
    try:
        r = _api(BOT2_TOKEN, "sendMessage", parse_mode="HTML", **kw)
        return r["result"]["message_id"]
    except Exception:
        try:  # HTML rusak? buang tag, kirim polos — pesan NGGAK akan pernah hilang
            import re
            clean = re.sub(r"</?(b|i|code|a|u|s|pre)[^>]*>", "", text)
            kw2 = dict(kw); kw2["text"] = clean
            r = _api(BOT2_TOKEN, "sendMessage", **kw2)
            return r["result"]["message_id"]
        except Exception:
            return None

def _edit(chat_id, message_id, text):
    try: _api(BOT2_TOKEN, "editMessageText", chat_id=chat_id, message_id=message_id,
              text=text, parse_mode="HTML")
    except Exception: pass

def _delete(chat_id, message_id):
    try: _api(BOT2_TOKEN, "deleteMessage", chat_id=chat_id, message_id=message_id)
    except Exception: pass

def _typing(chat_id):
    try: _api(BOT2_TOKEN, "sendChatAction", chat_id=chat_id, action="typing")
    except Exception: pass

def _toast(cb_id, text="", alert=False):
    try: _api(BOT2_TOKEN, "answerCallbackQuery", callback_query_id=cb_id,
              text=text[:190], show_alert="true" if alert else "")
    except Exception: pass

def _report_owner(text):
    if not (OWNER_TOKEN and OWNER_CHAT): return
    try: _api(OWNER_TOKEN, "sendMessage", chat_id=OWNER_CHAT, text=text, disable_web_page_preview="true")
    except Exception: pass

def _is_owner(uid): return bool(OWNER_CHAT) and str(uid) == str(OWNER_CHAT)

# ══════════════ level / user / stat / event ══════════════
def _stats(): return DB.get("stats", {"total": 0, "success": 0, "failed": 0})
def _save_stats(s): _save("stats", s)

LEVELS = [(0, "🐣 Rooki"), (5, "🔥 Sniffer"), (15, "⚡ Pro"), (30, "👑 Master"), (60, "💎 Legend")]
def _level(n):
    name = LEVELS[0][1]
    for need, nm in LEVELS:
        if n >= need: name = nm
    return name

def _next_level(n):
    """(nama_level_berikutnya, sisa_puan) — None kalau sudah puncak."""
    for need, nm in LEVELS:
        if n < need: return nm, need - n
    return None, 0

def _bar(cur, total, width=8):
    if total <= 0: return "█" * width
    filled = max(0, min(width, int(round(width * cur / total))))
    return "█" * filled + "░" * (width - filled)

def _user(uid, name=None):
    e = (DB.get("sniffers", {}) or {}).get(str(uid)) or {}
    if name: e["name"] = name
    e.setdefault("count", 0); e.setdefault("streak", 0); e.setdefault("last", "")
    e.setdefault("fmt", {}); e.setdefault("first", int(time.time()))
    return e

def _board_add(uid, name, fmt=None, bonus=0):
    b = DB.get("sniffers", {})
    e = b.get(str(uid)) or _user(uid, name)
    e["name"] = name
    today = time.strftime("%Y-%m-%d")
    if e.get("last") != today:
        e["streak"] = e["streak"] + 1 if e.get("last") == time.strftime(
            "%Y-%m-%d", time.localtime(time.time() - 86400)) else 1
        e["last"] = today
    e["count"] = e.get("count", 0) + 1 + bonus
    if fmt:
        e.setdefault("fmt", {})
        e["fmt"][fmt] = e["fmt"].get(fmt, 0) + 1
    b[str(uid)] = e
    _save("sniffers", b)
    return e

def _rank_of(uid):
    b = sorted(DB.get("sniffers", {}).items(), key=lambda x: -x[1].get("count", 0))
    for i, (k, _) in enumerate(b):
        if str(k) == str(uid): return i + 1, len(b)
    return None, len(b)

def _hist_add(uid, fmt, fname):
    h = DB.get("hist", {})
    rows = h.get(str(uid), [])
    rows.append({"f": fmt, "n": fname[:70], "t": int(time.time())})
    h[str(uid)] = rows[-8:]
    _save("hist", h)

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
    if _is_owner(uid): return None      # admin bebas jeda — testing 😄
    now = time.time()
    left = COOLDOWN - (now - _last.get(uid, -COOLDOWN))
    if left > 0:
        m, s = divmod(int(left), 60)
        pct = int(100 * (COOLDOWN - left) / COOLDOWN)
        return ("⏳ <b>MESIN MASIH KECAP-KECAP</b>\n" + SEP + "\n"
                f"{'▓' * (pct // 10)}{'░' * (10 - pct // 10)} <b>{m}m {s:02d}d</b> lagi\n\n"
                f"Sambil nunggu, isi sama:\n• /cek user:pass@host:port — tes server SSH\n"
                "• /top — lihat siapa sniffer tergarang\n• /checkin — klaim bonus harian")
    _last[uid] = now
    return None

# ══════════════ deteksi pintar & ekstrak ══════════════
import re as _re
def _smart(result):
    tips = []
    try:
        m = _re.search(r"\{.*\}", result, _re.S)
        if m:
            j = json.loads(m.group(0))
            cfg = j.get("Config", j)
            if str(cfg.get("blockedByHwid", "")).lower() == "true":
                tips.append("🔐 Config ini DIKUNCI HWID")
            if str(cfg.get("lockAllConfig", "")).lower() == "true":
                tips.append("🔒 Semua bagian config dikunci")
            exp = str(cfg.get("expiryTime", ""))
            if exp and exp != "lifeTime" and exp.replace(".", "").isdigit():
                try:
                    days = (float(exp) / 1000 - time.time()) / 86400
                    tips.append(f"⏰ Sisa masa aktif: ~{int(days)} hari" if days > 0
                                else "☠️ Masa aktif config: SUDAH HABIS")
                except Exception: pass
            elif exp == "lifeTime":
                tips.append("♾️ Masa aktif: LIFE TIME")
            ssh = cfg.get("sshField", "") or cfg.get("ssh", "")
            if ssh and "@" in ssh:
                tips.append("🖥️ Akun SSH ketemu — cek: /cek " +
                            ssh.split("@")[-1].split(":443")[0].split(":80")[0].split(":8")[0] + " (host:port)")
    except Exception:
        pass
    if not tips:
        tips.append("💡 Config terbuka (nggak dikunci) — bebas dipelajari")
    return "\n".join(tips[:3])

def _extract(result, as_bubbles=True):
    """Field penting dalam bubble <code> — tap 1x = tersalin."""
    rows = []
    try:
        m = _re.search(r"\{.*\}", result, _re.S)
        j = json.loads(m.group(0)); cfg = j.get("Config", j)
        for k, v in [("Payload", cfg.get("payload")), ("Proxy/SNI", cfg.get("proxy") or cfg.get("sni")),
                     ("SSH", cfg.get("sshField") or cfg.get("ssh")),
                     ("Mode", cfg.get("connectionMode")), ("SNI", cfg.get("sni"))]:
            if v:
                s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                rows.append((k, _h(s[:700])))
    except Exception:
        pass
    if not rows:
        return "📋 Field inti nggak ketemu — ekstrak manual dari hasil sniff."
    if as_bubbles:
        lines = [f"<b>{k}</b> — tap buat salin:\n<code>{v}</code>" for k, v in rows]
    else:
        lines = [f"▸ {k}: {v}" for k, v in rows]
    return ("📋 <b>DATA EKSTRAK</b> — tap tiap kotak = langsung tersalin ✅\n" + SEP + "\n\n" +
            "\n\n".join(lines))

# ══════════════ PNG hasil (gaya terminal rapi) ══════════════
def _render_png(text, fmt=""):
    try:
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO
        font = None
        for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                  "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
                  "/System/Library/Fonts/Menlo.ttc"):
            if os.path.exists(p):
                try: font = ImageFont.truetype(p, 13); break
                except Exception: pass
        lines = []
        for ln in text.split("\n")[:80]:
            while len(ln) > 74:
                lines.append(ln[:74]); ln = ln[74:]
            lines.append(ln)
        lines = lines[:90]
        W, LH, HEAD = 800, 18, 46
        H = HEAD + len(lines) * LH + 34
        img = Image.new("RGB", (W, H), (11, 15, 21))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, HEAD - 10], fill=(18, 24, 33))
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([14 + i * 20, 10, 26 + i * 20, 22], fill=c)
        ttl = f"SNIFF CONFIG TERMINAL — @BleackCoderr{('  |  ' + fmt) if fmt else ''}"
        d.text((86, 8), ttl, fill=(148, 163, 184), font=font)
        d.line([0, HEAD - 10, W, HEAD - 10], fill=(240, 190, 60))
        y = HEAD
        for ln in lines:
            col = (240, 190, 60) if ln.startswith("=") else (200, 247, 160) if not ln.startswith("-") else (120, 135, 150)
            d.text((14, y), ln, fill=col, font=font)
            y += LH
        d.text((14, H - 24), f"⏱ {time.strftime('%d-%m-%Y %H:%M')}  •  {BOT_VERSION}",
               fill=(90, 100, 120), font=font)
        buf = BytesIO(); img.save(buf, "PNG"); return buf.getvalue()
    except Exception:
        return None

# ══════════════ /cek ssh ══════════════
def _cek(arg):
    m = _re.match(r"^(?:([^:@\s]+)(?::[^\s@]*)?)?@?([a-zA-Z0-9.\-]+):(\d{1,5})$", arg.strip())
    if not m:
        return ("❌ Format salah.\nPakai: /cek user:pass@host:port\n"
                "Contoh: /cek fastssh.com-samarata@uk.sshws.net:443")
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
        out = ("🏓 <b>CEK AKUN SSH</b>\n" + SEP + "\n"
               f"🖥️ <code>{_h(host)}:{port}</code> → <code>{_h(ip)}</code>\n" +
               (f"👤 <code>{_h(user)}</code>\n" if user else "") +
               f"✅ PORT TERBUKA — server hidup\n⚡ Respons: {ms} ms")
        if banner: out += f"\n📡 Banner: <code>{_h(banner)}</code>"
        return out + "\n\nℹ️ Cek koneksi doang, bukan login password."
    except Exception:
        return f"❌ <code>{_h(host)}:{port}</code> TIDAK merespons — port tertutup/server mati/IP diblokir."

# ══════════════ pesan tetap ══════════════
WELCOME = (
    "🐴 <b>SNIFF CONFIG BOT v7</b>\n" + SEP + "\n\n"
    "Lempar file config → isi aslinya langsung muncul.\n"
    "Didukung: <code>.HC .EHI .SSC .NPV .NPVT .DARK</code>\n\n"
    "⚡ <b>PERINTAH DASAR</b>\n"
    "/help — panduan lengkap          /stats — statistik mesin\n"
    "/cek — tes server SSH            /random — config gratis 🎁\n"
    "/ping — cek mesin                /about — soal bot\n\n"
    "🎮 <b>SERU-SERUAN</b>\n"
    "/profile — kartu anggota lu      /top — leaderboard 🏆\n"
    "/checkin — absen + bonus 🔥      /history — sniff terakhir\n"
    "/ref — ajak teman, duo bonus 🤝\n\n"
    "⏳ Jeda 3 menit per orang (di grup bebas spam dikit)\n"
    "🔒 File diproses lalu dibuang • 📩 di grup bisa minta hasil ke PV"
)
RULES = ("📜 <b>ATURAN GRUP</b>\n" + SEP + "\n\n"
         "1️⃣ Satu file per 3 menit per orang — mesinnya manusia juga 😤\n"
         "2️⃣ Jangan lempar config orang lain buat dicuri — banned dari fitur\n"
         "3️⃣ Hasil panjang? Tekan 📩 KIRIM KE PV biar grup nggak banjir\n"
         "4️⃣ Gagal terus? Itu kemungkinan key versi baru, lapor @BleackCoderr\n"
         "5️⃣ Dilarang judi-judi & jualan di sini — admin yang nendang, bukan gue 🖕")

def _personal(uid, name):
    e = _user(uid, name)
    if not e.get("count"):
        return "\n\n🆕 <b>Selamat datang, newbie!</b> Lempar file .hc buat mulai — gratis."
    flame = " 🔥" * min(e.get("streak", 0), 5)
    nxt, need = _next_level(e["count"])
    prog = ""
    if nxt:
        floor_n = max(n for n, _ in LEVELS if e["count"] >= n)
        span = need + e["count"] - floor_n  # jarak level saat ini -> berikutnya
        prog = f"\n📈 {_bar(e['count'] - floor_n, span)} menuju {nxt} (sisa {need}x)"
    return (f"\n👋 Halo <b>{_h(e['name'])}</b>! Sniff ke-<b>{e['count'] + 1}</b> lu\n"
            f"🏅 Level: {_level(e['count'])}{flame}{prog}")

# ══════════════ ANIMASI NGUNYAH ══════════════
_anim = {}
def _animate(uid, chat_id, mid, fname):
    i = 0
    try:
        for step in range(8):   # maks ~6 detik
            if _anim.get(uid, {}).get("stop").is_set(): return
            pct = min(15 + step * 10, 90)
            bar = "▓" * (pct // 12) + "░" * (8 - pct // 12)
            _edit(chat_id, mid,
                  f"{SPIN[i % len(SPIN)]} MESIN NGUNYAH <code>{_h(fname)}</code>\n{bar} {pct}%")
            i += 1
            time.sleep(0.7)
    except Exception:
        pass

def _stop_anim(uid):
    e = _anim.pop(uid, None)
    if e: e["stop"].set()
    return e

# ══════════════ kartu profil ══════════════
def _profile(uid, name):
    e = _user(uid, name)
    if not e.get("count"):
        return "🪪 Belum ada data — sniff dulu satu file, baru ganteng di sini 😎"
    rank, total_u = _rank_of(uid)
    nxt, need = _next_level(e["count"])
    badges = "  ".join(f"{EMOJI.get(k, '🏷️')}{v}" for k, v in sorted(e.get("fmt", {}).items(), key=lambda x: -x[1])) or "—"
    days_old = max(1, int((time.time() - e.get("first", time.time())) / 86400) + 1)
    out = (f"🪪 <b>KARTU ANGGOTA</b>\n{SEP}\n\n"
           f"👤 <b>{_h(e['name'])}</b>\n"
           f"🏅 Level: <b>{_level(e['count'])}</b>\n"
           f"📊 Total sniff: <b>{e['count']}x</b> • streak {e.get('streak', 0)} hari {'🔥' * min(e.get('streak', 0), 3)}\n"
           f"🏆 Peringkat: <b>#{rank or '-'}</b> dari {total_u} sniffer\n"
           f"🎖️ Badge: {badges}\n"
           f"📅 Bergabung: {days_old} hari lalu\n")
    if nxt:
        cur = e["count"] - max(n for n, _ in LEVELS if e["count"] >= n)
        out += f"\n📈 {_bar(cur, need)} {need}x lagi → {nxt}"
    else:
        out += "\n💎 Lu udah di puncak. Ajarin yang di bawah."
    return out

# ══════════════ HANDLER UTAMA ══════════════
def _handle(msg):
    chat_id = msg["chat"]["id"]
    where = "pribadi" if msg["chat"].get("type") == "private" else "grup"
    user = msg.get("from", {})
    uid, uname = user.get("id", chat_id), user.get("username")
    label = ("@" + uname) if uname else (user.get("first_name") or str(chat_id))
    text = (msg.get("text") or "").strip()
    if where == "pribadi" and uid: _sub(chat_id)
    orig_mid = msg.get("message_id")

    # ── grup: /perintah@Namabot → buang @-nya ──
    if text.startswith("/") and "@" in text.split(" ")[0]:
        text = text.split(" ")[0].split("@", 1)[0] + " " + " ".join(text.split(" ")[1:])
        text = text.strip()

    # ── member baru gabung / bot ditambahkan ──
    if msg.get("new_chat_members"):
        bot_added = any(m.get("username", "").lower().endswith("bot") and
                        str(m.get("id")) == str(os.environ.get("BOT2_ID", ""))
                        for m in msg["new_chat_members"])
        names = ", ".join(_h(m.get("first_name") or "newbie") for m in msg["new_chat_members"]
                          if not m.get("username", "").lower().endswith("bot") or str(m.get("id")) != str(os.environ.get("BOT2_ID", "")))
        if names:
            _send(chat_id, f"👋 Welcome <b>{names}</b>!\nLempar file <code>.hc .ehi .ssc .npv .npvt .dark</code> "
                  f"ke sini buat nge-sniff. Detail: /help • aturan: /rules")
        return
    if msg.get("left_chat_member"):
        return

    # ── perintah ──
    if text.startswith("/start"):
        arg = text[len("/start"):].strip()
        if arg.startswith("ref-") and arg[4:].lstrip("-").isdigit():
            _handle_referral(uid, label, int(arg[4:]))
        _send(chat_id, WELCOME + _personal(uid, label), TOOLS_ROW); return
    if text.startswith("/help"):
        _send(chat_id, "📖 <b>PANDUAN</b>\n" + SEP + "\n\n"
              "📄 Kirim file config (dokumen) → hasil otomatis\n"
              "📋 Tombol EKSTRAK DATA → tap kotak = tersalin\n"
              "📩 Tombol KIRIM KE PV → hasil meluncur diam-diam ke pribadi\n"
              "🏓 <code>/cek user:pass@host:port</code> → cek server SSH\n"
              "🎁 /random → config gratis • 🪪 /profile → kartu lu\n"
              "🔥 /checkin → bonus harian • 🤝 /ref → ajak teman\n\n"
              "Level: 🐣 0 → 🔥 5 → ⚡ 15 → 👑 30 → 💎 60 sniff", TOOLS_ROW); return
    if text.startswith("/rules"):
        _send(chat_id, RULES + WATERMARK); return
    if text.startswith("/about"):
        up = time.time() - BOOT_TIME
        d, rem = divmod(int(up), 86400); h, m = divmod(rem, 3600); m //= 60
        s = _stats()
        _send(chat_id, f"🤖 <b>SNIFF CONFIG BOT</b> [{BOT_VERSION}]\n{SEP}\n\n"
              f"👨‍💻 Dev: @BleackCoderr • 🌐 {WEB_URL}\n"
              f"⚙️ Mesin nyala: {d}h {h}j {m}m\n"
              f"🔢 Diproses total: {s['total']} sniff • {len(DB.get('sniffers', {}))} sniffer terdaftar\n\n"
              "Bebas dipakai, jangan dijual. 🐴", TOOLS_ROW); return
    if text.startswith("/stats"):
        s = _stats()
        rate = int(100 * s["success"] / s["total"]) if s["total"] else 0
        _send(chat_id, f"📊 <b>STATISTIK MESIN</b>\n{SEP}\n\n"
              f"🔢 Total: <b>{s['total']}</b>\n"
              f"✔ Berhasil: <b>{s['success']}</b>\n"
              f"✘ Gagal: <b>{s['failed']}</b>\n"
              f"🎯 Success rate: <b>{rate}%</b> {_bar(s['success'], max(s['total'], 1))}\n"
              f"👥 Sniffer unik: <b>{len(DB.get('sniffers', {}))}</b>" + WATERMARK, TOOLS_ROW); return
    if text.startswith("/top"):
        b = sorted(DB.get("sniffers", {}).items(), key=lambda x: -x[1].get("count", 0))[:5]
        if not b:
            _send(chat_id, "🏆 BELUM ADA SKOR — jadi sniff pertama!"); return
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        rows = "\n".join(f"{medal[i]} <b>{_h(e['name'])[:24]}</b> — {e['count']}x  {_level(e['count'])}"
                         f"{'  🔥' + str(e.get('streak', 0)) + 'd' if e.get('streak', 0) > 1 else ''}"
                         for i, (_, e) in enumerate(b))
        me, _t = _rank_of(uid)
        you = f"\n\n📍 Posisi lu: <b>#{me or '-'}</b> dari {_t}" if str(uid) in DB.get("sniffers", {}) else \
              "\n\n🫥 Lu belum main. Lempar satu file, masuk papan."
        _send(chat_id, f"🏆 <b>TOP SNIFFERS</b>\n{SEP}\n\n{rows}{you}" + WATERMARK); return
    if text.startswith("/profile"):
        _send(chat_id, _profile(uid, label) + WATERMARK); return
    if text.startswith("/history"):
        rows = DB.get("hist", {}).get(str(uid), [])
        if not rows:
            _send(chat_id, "🗂 Belum ada riwayat. Snack pertamamu menunggu 🐴"); return
        lines = "\n".join(f"{EMOJI.get(r['f'], '🏷️')} <code>{_h(r['n'])}</code>\n    ⏱ {time.strftime('%d-%m %H:%M', time.localtime(r['t']))} • {r['f']}"
                          for r in reversed(rows))
        _send(chat_id, f"🗂 <b>8 SNIFF TERAKHIRMU</b>\n{SEP}\n\n{lines}" + WATERMARK); return
    if text.startswith("/checkin"):
        ci = DB.get("checkin", {})
        today = time.strftime("%Y-%m-%d")
        if ci.get(str(uid)) == today:
            e = _user(uid, label)
            _send(chat_id, f"📅 Udah absen hari ini, {label}.\n"
                  f"Balik lagi besok — streak 🔥 lu {e.get('streak', 0)} hari.\n"
                  f"<i>Bonus +2 skor nunggu 24 jam lagi.</i>"); return
        ci[str(uid)] = today; _save("checkin", ci)
        e = _board_add(uid, label, bonus=2)
        _send(chat_id, f"✅ <b>ABSEN HARI INI: BERES</b>\n{SEP}\n\n"
              f"🎁 Bonus: <b>+2 skor</b>!\n🔥 Streak: <b>{e.get('streak', 1)}</b> hari\n"
              f"🏅 Level: {_level(e['count'])} ({e['count']}x sniff)\n\n"
              "Besok jangan lupa lagi — yang rajin naik Legend 💎" + WATERMARK); return
    if text.startswith("/ref"):
        link = f"{BOT_LINK}?start=ref-{uid}"
        _send(chat_id, f"🤝 <b>AJAK TEMAN, DUO BONUS</b>\n{SEP}\n\n"
              f"Sebarkan link ini:\n<code>{link}</code>\n\n"
              f"Yang daftar lewat link lu + sniff sukses pertama →\n"
              f"lu dapat <b>+5 skor</b>, dia dapat sambutan jagoan 💪\n\n"
              f"Sudah direferensikan: <b>{len([v for v in DB.get('referrals', {}).values() if v == str(uid)])} orang</b>",
              [[{"text": "📢 SHARE SEKARANG", "url": "https://t.me/share/url?url=" +
                 urllib.parse.quote(link) + "&text=" + urllib.parse.quote("Nge-sniff config gratisan, cek nih bot 🐴")}]]); return
    if text.startswith("/ping"):
        t0 = time.time(); _typing(chat_id)
        up = time.time() - BOOT_TIME
        _send(chat_id, f"🏓 <b>PONG!</b> Mesin ngebut — {int((time.time()-t0)*1000)} ms\n"
              f"⚙️ [{BOT_VERSION}] • uptime {int(up // 3600)}j {int(up % 3600 // 60)}m ✅"); return
    if text.startswith("/cek"):
        arg = text[4:].strip()
        if not arg:
            _send(chat_id, "🏓 Format: <code>/cek user:pass@host:port</code>\n"
                  "Contoh: <code>/cek fastssh.com-samarata@uk.sshws.net:443</code>"); return
        _typing(chat_id)
        _send(chat_id, _cek(arg) + WATERMARK); return
    if text.startswith("/random"):
        pool = DB.get("pool", [])
        if not pool:
            _send(chat_id, "🎁 Pool config gratis masih KOSONG.\n"
                  "Owner belum nyimpen config publik — coba lagi nanti atau ke @BleackCoderr"); return
        try:
            pick = random.choice(pool)
            name = pick.get("name", "free.config.hc")
            if pick.get("fid"):
                _api(BOT2_TOKEN, "sendDocument", chat_id=chat_id, document=pick["fid"],
                     caption="🎁 <b>Config gratis hari ini</b>\n" + SEP + "\n@BleackCoderr 🐴")
            else:
                data = base64.b64decode(pick.get("b64", ""))
                _multipart("sendDocument", {"chat_id": chat_id,
                           "caption": "🎁 Config gratis hari ini — @BleackCoderr"}, name, data)
        except Exception:
            _send(chat_id, "❌ Pool rusak — lapor @BleackCoderr"); return
        return
    # ── admin ──
    if text.startswith("/broadcast"):
        if not _is_owner(uid): return
        body = text[len("/broadcast"):].strip()
        if not body:
            _send(chat_id, "Format: <code>/broadcast &lt;pesan&gt;</code> — ke semua subscriber"); return
        subs = DB.get("subscribers", [])
        ok = 0
        for c in subs:
            if _send(c, "📢 <b>PENGUMUMAN</b>\n" + SEP + "\n\n" + body + WATERMARK): ok += 1
            time.sleep(0.06)
        _send(chat_id, f"✅ Broadcast terkirim ke {ok}/{len(subs)} user"); return
    if text.startswith("/pool"):
        if not _is_owner(uid): return
        doc = msg.get("document") or {}
        cmd = text.split(" ")[0]
        rest = text[len(cmd):].strip()
        if doc.get("file_id") and rest == "add":
            pool = DB.get("pool", [])
            pool.append({"name": doc.get("file_name", "free.hc"), "fid": doc["file_id"]})
            _save("pool", pool[-50:])
            _send(chat_id, f"➕ Masuk pool ({len(pool)} config). Caption file: <code>/pool add</code>"); return
        if rest == "clear":
            _save("pool", []); _send(chat_id, "🧹 Pool dikosongkan."); return
        pool = DB.get("pool", [])
        names = "\n".join(f"• {p['name']}" for p in pool[-15:]) or "— kosong —"
        _send(chat_id, f"🗃 <b>POOL CONFIG GRATIS</b> ({len(pool)})\n{SEP}\n{names}\n\n"
              "Tambah: reply file dgn caption <code>/pool add</code> • Hapus semua: <code>/pool clear</code>"); return
    if text.startswith("/admin"):
        if not _is_owner(uid): return
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
        _send(chat_id, f"🕵️ <b>ADMIN DASHBOARD</b>\n{SEP}\n\n"
              f"📅 Hari ini: {len(today)} sniff | 👥 user unik: "
              f"{len(set(e['u'] for e in today))}\n⏰ Jam tersibuk: {busy}:00\n"
              f"🏷️ Format terpopuler: {', '.join(f'{k} ({v})' for k, v in fmt_top) or '-'}\n\n{bar}\n\n"
              f"📮 Subscriber broadcast: {len(DB.get('subscribers', []))}\n"
              f"🎁 Pool gratis: {len(DB.get('pool', []))} • 🤝 Referral aktif: {len(DB.get('referrals', {}))}\n"
              f"💾 Cache hasil: {len(DB.get('extract_cache', {}))} | DB cloud: {'✅' if DB.get('pin_id') else 'belum'}"); return
    if text.startswith("/"):
        return

    # ── file masuk → proses ──
    doc = msg.get("document")
    if not doc:
        if where == "private":
            _send(chat_id, "🤔 Kirim <b>file config</b> ya — bukan teks.\n"
                  "Format: <code>.hc .ehi .ssc .npv .npvt .dark</code>\n"
                  "Bingung? /help dulu, Bro."); return
        return
    wait = _cool(uid)
    if wait: _send(chat_id, wait, reply_to=orig_mid); return
    fname, fsize = doc.get("file_name", "config.bin"), doc.get("file_size", 0)
    if fsize > 5 * 1024 * 1024:
        _send(chat_id, "❌ File maks 5MB, Bro. Yang lebih gede kemungkinan bukan config.", reply_to=orig_mid); return

    _typing(chat_id)
    mid = _send(chat_id, f"{SPIN[0]} MESIN NGUNYAH <code>{_h(fname)}</code>\n▓░░░░░░░ 12%", reply_to=orig_mid)
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
        _send(chat_id, "❌ Gagal unduh file — coba kirim lagi.", reply_to=orig_mid); return

    import server
    hint = server.detect_by_ext(fname)
    order = ([p for p in server.PARSERS if p[0] == hint] + [p for p in server.PARSERS if p[0] != hint])
    fmt, result = "", None
    for f, fn in order:
        try: r = fn(data)
        except Exception: r = None
        if r: fmt, result = f, r; break
    elapsed = time.time() - t_start

    _stop_anim(uid)
    if mid: _delete(chat_id, mid)   # chat bersih

    s = _stats(); s["total"] += 1
    smart = _smart(result) if result else ""
    timeinfo = f"⏱️ {elapsed:.1f} detik • {_h(str(round(fsize / 1024, 1)))} KB • {BOT_VERSION}"
    if result:
        s["success"] += 1; _save_stats(s)
        e = _board_add(uid, label, fmt); _event(uid, fmt, where); _sub(chat_id)
        _hist_add(uid, fmt, fname)
        _settle_referral(uid, label)   # bonus +5 buat yang ngajak, sekali seumur hidup
        fact = random.choice(FACTS)
        nxt_tip = ""
        nm, need = _next_level(e["count"])
        if nm and need <= 3:
            nxt_tip = f"\n📈 {need}x lagi naik ke {nm}!"
        ms = ""
        if e["count"] in MILESTONES:
            ms = f"\n🎉 {MILESTONES[e['count']]}"
        cap = (f"{EMOJI.get(fmt, '✅')} <b>BERHASIL</b> — {fmt} | 🏅 {_level(e['count'])}"
               f"{' | 🔥 streak ' + str(e['streak']) if e.get('streak', 0) > 1 else ''}\n"
               f"{smart}\n⏱️ Diproses {timeinfo}{nxt_tip}{ms}\n{fact}")
        body = (f"{EMOJI.get(fmt, '✅')} BERHASIL — format {fmt}\n📄 {fname}\n"
                f"🕐 {time.strftime('%d-%m-%Y %H:%M')}\n{SEP}\n\n{result}\n\n{smart}\n\n"
                "SNIFF CONFIG - diolah oleh @BleackCoderr\n" + WEB_URL)
        btns = [[{"text": "📋 EKSTRAK DATA", "callback_data": f"ex:{uid}"},
                 {"text": "🖼 LIHAT PNG", "callback_data": f"png:{uid}"}]]
        if where == "grup":
            btns.append([{"text": "📩 KIRIM KE PV (biar grup nggak banjir)", "callback_data": f"pv:{uid}"}])
        btns.append([{"text": "🌐 WEB", "url": WEB_URL}])
        png = _render_png(result, fmt)
        sent = False
        if png:
            try:
                _multipart("sendPhoto", {"chat_id": chat_id, "caption": cap[:950],
                          "reply_markup": json.dumps({"inline_keyboard": btns})},
                          "sniff_" + fmt.lower() + ".png", png, ffield="photo", ctype="image/png",
                          reply_to=orig_mid)
                sent = True
            except Exception:
                sent = False
        if not sent:
            try:
                _multipart("sendDocument",
                           {"chat_id": chat_id, "caption": cap[:950],
                            "reply_markup": json.dumps({"inline_keyboard": btns})},
                           fname + ".sniffed.txt", body.encode(), reply_to=orig_mid)
                sent = True
            except Exception:
                sent = False
        if not sent:
            _send(chat_id, _h(body[:3900]), reply_to=orig_mid)
        ec = DB.get("extract_cache", {})
        ec[str(uid)] = {"r": result[:20000], "t": time.time(), "mid": orig_mid,
                        "fid": doc.get("file_id"), "fname": fname, "body": body[:30000]}
        _save("extract_cache", {k: v for k, v in list(ec.items())[-100:]})
        _report_owner(f"🤖 BOT SNIFF ✔ [{BOT_VERSION}]\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n"
                      f"👤 {label} (id={uid})\n📄 {fname} ({len(data)} B)\n🏷️ {fmt}\n📍 {where}")
    else:
        s["failed"] += 1; _save_stats(s); _event(uid, None, where)
        sig = hashlib.sha256(data).hexdigest()[:12]
        _send(chat_id, "❌ <b>GAGAL</b> — format nggak dikenali / dikunci versi baru.\n" + SEP + "\n\n"
              f"🔖 Sidik jari file: <code>{sig}…</code>\n"
              "🧐 Kemungkinan: file rusak, format di luar daftar, atau key versi baru.\n"
              "🔁 Udah bener filenya? Kirim ulang aja 3 menit lagi.\n"
              "📮 Mau format baru didukung?REQUEST di " + '<a href="%s">@BleackCoderr</a>' % OWNER_TG,
              TOOLS_ROW, reply_to=orig_mid)
        _report_owner(f"🤖 BOT SNIFF ✘\n🕐 {time.strftime('%d-%m-%Y %H:%M')}\n👤 {label} (id={uid})\n📄 {fname} ({len(data)} B)\n🔖 {sig}…")

# ══════════════ referral ══════════════
def _handle_referral(new_uid, new_label, ref_uid):
    if str(new_uid) == str(ref_uid): return
    refs = DB.get("referrals", {})
    if str(new_uid) in refs: return          # udah pernah di-refer
    refs[str(new_uid)] = str(ref_uid)
    _save("referrals", refs)
    _send(ref_uid, f"🤝 <b>{_h(new_label)}</b> daftar lewat link referral lu!\n"
          f"Sesaat setelah dia sniff sukses pertama, <b>+5 skor</b> mendarat di kartu lu 💎")

def _settle_referral(uid, label):
    refs = DB.get("referrals", {})
    ref_uid = refs.get(str(uid), "done")
    if ref_uid in (None, "", "done"): return
    refs[str(uid)] = "done"; _save("referrals", refs)
    b = DB.get("sniffers", {})
    e = b.get(str(ref_uid)) or _user(ref_uid, "teman")
    e["count"] = e.get("count", 0) + 5
    b[str(ref_uid)] = e; _save("sniffers", b)
    _send(ref_uid, f"🎉 <b>REFERRAL BERES!</b> {_h(label)} udah sniff sukses.\n"
          f"🎁 Lu dapat <b>+5 skor</b> → total {e['count']}x. Level: {_level(e['count'])}", silent=True)

# ══════════════ callback buttons ══════════════
def _on_callback(cb):
    uid = cb.get("from", {}).get("id", "")
    data = cb.get("data", "")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    if data.startswith(("ex:", "png:", "pv:")):
        kind = data.split(":", 1)[0][2:]
        if str(uid) != data.split(":", 1)[1]:
            _toast(cb["id"], "Ini tombol punya orang lain, bro 🖕"); return
        hit = DB.get("extract_cache", {}).get(str(uid))
        if not hit:
            _toast(cb["id"], "⌛ Kedaluwarsa — kirim ulang file-nya ya", alert=True); return
        _toast(cb["id"])
        if kind == "ex":
            _send(chat_id, _extract(hit["r"]) + WATERMARK, reply_to=hit.get("mid"))
        elif kind == "png":
            png = _render_png(hit["r"], "")
            if png:
                try:
                    _multipart("sendPhoto", {"chat_id": chat_id,
                               "caption": "🖼 Hasil sniff (tap ➕ buat fullscreen)\n@BleackCoderr"},
                               "sniff_view.png", png, ffield="photo")
                except Exception: _send(chat_id, "❌ PNG-nya gagal dibuat, coba /start ulang.")
            else:
                _send(chat_id, "❌ PNG nggak tersedia — pakai 📋 EKSTRAK DATA aja.")
        elif kind == "pv":
            ok = False
            try:
                if hit.get("fid"):
                    _api(BOT2_TOKEN, "sendDocument", chat_id=uid, document=hit["fid"],
                         caption="📩 Hasil sniff dari grup — rahasia antara kita 🤫\n@BleackCoderr 🐴")
                    ok = True
            except Exception:
                ok = False
            if not ok:
                body = hit.get("body") or "Hasil nggak ketemu — kirim ulang file di PV ya."
                ok = _send(uid, _h(body[:3900]))
            if ok:
                _send(chat_id, "📩 Udah meluncur ke PV lu — grup tetep adem 🧊", reply_to=cb.get("message", {}).get("message_id"))
            else:
                _toast(cb["id"], "Klik /start di PV gue dulu ya, baru bisa dikirim", alert=True)

# ══════════════ loops ══════════════
def _poll_loop():
    offset = 0
    try:
        me = _api(BOT2_TOKEN, "getMe")["result"]
        os.environ["BOT2_ID"] = str(me["id"])
        try:
            cmds = [("start", "mulai"), ("help", "panduan"), ("rules", "aturan grup"),
                    ("stats", "statistik mesin"), ("top", "leaderboard"), ("profile", "kartu anggota"),
                    ("checkin", "absen bonus harian"), ("history", "riwayat sniff"), ("ref", "ajak teman"),
                    ("cek", "tes server SSH"), ("random", "config gratis"), ("ping", "cek mesin"),
                    ("about", "soal bot")]
            _api(BOT2_TOKEN, "setMyCommands",
                 commands=json.dumps([{"command": c, "description": d} for c, d in cmds]))
            _api(BOT2_TOKEN, "setMyDescription",
                 description="Nge-sniff file config .HC .EHI .SSC .NPV .NPVT .DARK — gratis, cepet, rapi.")
            _api(BOT2_TOKEN, "setMyShortDescription", short_description="Lempar config → isi aslinya muncul 🐴")
        except Exception as e: print("setMy*: ", e, flush=True)
    except Exception:
        pass
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
    _load_db()
    try:
        try: _api(BOT2_TOKEN, "deleteWebhook")
        except Exception: pass
    except Exception: pass
    threading.Thread(target=_keepalive_loop, daemon=True, name="keepalive").start()
    threading.Thread(target=_poll_loop, daemon=True, name="sniffbot").start()
    STARTED = True
    print(f"bot2: {BOT_VERSION} jalan ✅ (profile/checkin/ref/PV-button/milestone, db persisten)", flush=True)
