# HC Unlocker v3 — STRATEGI BARU: "SURGICAL EDIT"
# Jangan decrypt-reencrypt semua token. File asli = sumber kebenaran struktur.
# Cuma: 1) decrypt xy lama utk baca field, 2) matikan proteksi, 3) RE-ENCRYPT CUMA FIELD
# YANG BERUBAH, sisanya token MENTAH ASLI — posisi & jumlah token persis file asli.
import base64, json

STATIC_NONCE = b'\xdb' * 8
XOR_HEADER = "e382e4b8adc386f09f9293"
MAGIC = "88a05e8772eac3e5703e0cd26c6e6f23de72fb09f7ee5a43283d1681f19d"

def _abc_encrypt(plaintext: str, key: bytes, nonce: bytes = STATIC_NONCE) -> str:
    from Crypto.Cipher import ChaCha20
    cipher = ChaCha20.new(key=key, nonce=nonce)
    cipher.seek(64)
    return (cipher.encrypt(plaintext.encode()) + bytes(16)).hex()

def _jkl_encrypt(plaintext: str) -> str:
    inner = base64.b64encode(plaintext.encode()).decode()
    data = bytearray(inner.encode())
    import HTTPCUSTOM as HC
    key = HC.HCConstants.JKL_KEY_OLD
    f = lambda x: ((x ^ 0xff) & 0xca) | (x & 0x35)
    out = bytearray()
    for i, dd in enumerate(data):
        k = key[i % 20]
        out.append(f(dd) ^ f(k))
    return base64.b64encode(bytes(out)).decode()

def _rst_encrypt(hex_cipher: str) -> str:
    import HTTPCUSTOM as HC
    data = bytes.fromhex(hex_cipher)
    out = bytes(b ^ HC.HCConstants.RST_XOR_KEY[i % len(HC.HCConstants.RST_XOR_KEY)]
                for i, b in enumerate(data))
    return base64.b64encode(out).decode()

# field (index) yang kita ubah saat unlock + nilai barunya
UNLOCK_VALUES = {
    2:  "false",        # lockAllConfig
    3:  "false",        # blockedByRoot
    15: "false",        # blockedByHwid
    21: "false",        # blockedByPassword
    19: "false",        # blockArea
    8:  "false",        # mobileDataAndLockProvider
    4:  "lifeTime",     # expiryTime
    5:  "true",         # noteEnabled
    6:  "🐴 UNLOCKED by @BleackCoderr\nhttps://sniffconfig.onrender.com",  # notes
}

def unlock_hc(original_file: bytes) -> bytes:
    """Surgical: struktur & token asli dipertahankan, cuma field proteksi di-encrypt ulang."""
    import HTTPCUSTOM as HC
    d = HC.HCDecryptor

    hex_payload = d._extract_initial_payload(original_file, XOR_HEADER)
    if not hex_payload: raise ValueError("header file bukan .hc")
    outer = d._abc_decrypt(hex_payload, HC.HCConstants.CHACHA_KEYS[5])
    if not outer.startswith("{"): raise ValueError("decrypt luar gagal")
    j = json.loads(outer)

    cfg_obj = j.get("cfg", {})
    is_new = isinstance(cfg_obj, dict) and "content" in cfg_obj
    a = j.get("a") if isinstance(j.get("a"), dict) else {}
    target = cfg_obj.get("content") if is_new else (a.get("xy") if "xy" in a else j.get("xy"))
    split = cfg_obj.get("split") if is_new else (a.get("uv") if "uv" in a else j.get("uv"))
    if not target or not split: raise ValueError("struktur file nggak dikenal")

    # nonce dinamis dari meta asli
    meta = {}
    if is_new:
        for k, name in {'b': 'hwid', 'f': 'area'}.items():
            if val := str(j.get(k) or cfg_obj.get(k) or ""): meta[name] = val
    else:
        for k, name in {'bb': 'hwid', 'e': 'password', 'fe': 'area', 'ed': 'provider'}.items():
            val = j.get(k) if k == 'e' else a.get(k)
            if val:
                dec = d._abc_decrypt(str(val), HC.HCConstants.CHACHA_KEYS[7])
                if dec: meta[name] = dec
    to_hex = lambda s: s.encode().hex() if s else ""
    h, p, pr, ar = meta.get('hwid'), meta.get('password'), meta.get('provider'), meta.get('area')
    derived = (to_hex(h) * 2) if h and not any((p, pr, ar)) else (to_hex(p) + to_hex(h) + to_hex(pr) + to_hex(ar))
    nonce = bytearray(STATIC_NONCE)
    if derived:
        try:
            for i, b in enumerate(bytes.fromhex(derived)[:8]): nonce[i] = b
        except Exception: pass
    dyn = bytes(nonce)

    # decrypt xy utk tahu field mana yang berubah (dan nama labelnya)
    if is_new:
        xy_dec = d._rst_decrypt(str(target))
        if not xy_dec:
            for key in HC.HCConstants.CHACHA_KEYS:
                if (t := d._abc_decrypt(str(target), key)) and str(split) in t:
                    xy_dec = t; break
    else:
        xy_dec = d._abc_decrypt(str(target), HC.HCConstants.CHACHA_KEYS[1])
    if not xy_dec: raise ValueError("isi config nggak ke-decrypt")
    tokens = xy_dec.split(str(split))

    # SURGICAL: ubah cuma field target; re-encrypt dgn jalur yg SAMA dgn decrypt-nya
    changed = 0
    for i, tok in enumerate(tokens):
        if i not in UNLOCK_VALUES: continue
        new_plain = UNLOCK_VALUES[i]
        if is_new:
            tokens[i] = d._encrypt_field(new_plain, dyn) if hasattr(d, "_encrypt_field") else \
                        _abc_encrypt(new_plain, HC.HCConstants.CHACHA_KEYS[7], dyn)
        else:
            tokens[i] = _abc_encrypt(_jkl_encrypt(new_plain), HC.HCConstants.CHACHA_KEYS[7], dyn)
        changed += 1
    if not changed: raise ValueError("field proteksi nggak ketemu")

    new_xy = str(split).join(tokens)

    if is_new:
        cfg_obj["content"] = _rst_encrypt(_abc_encrypt(new_xy, HC.HCConstants.CHACHA_KEYS[7], dyn))
        j["cfg"] = cfg_obj
    else:
        if "xy" in a:
            a["xy"] = _abc_encrypt(new_xy, HC.HCConstants.CHACHA_KEYS[1])
        elif "xy" in j:
            j["xy"] = _abc_encrypt(new_xy, HC.HCConstants.CHACHA_KEYS[1])
        else:
            raise ValueError("posisi xy nggak ketemu")

    outer_json = json.dumps(j, ensure_ascii=False, separators=(",", ":"))
    hex_outer = _abc_encrypt(outer_json, HC.HCConstants.CHACHA_KEYS[5])
    key_bytes = bytes.fromhex(XOR_HEADER)
    # FORMAT FILE HC (terverifikasi roundtrip dgn file asli):
    # file = utf8( latin1( XOR(hexstr) ) )  -> mojibake latin-1 -> utf-8 (2 byte utk char >0x7F)
    xored = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(hex_outer.encode("utf-8")))
    return xored.decode("latin-1").encode("utf-8")
