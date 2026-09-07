# HC Unlocker — re-encrypt hasil decrypt ke file .hc yang bisa di-import HTTP Custom
# Cara: ganti field proteksi jadi terbuka -> pakai ulang struktur JSON asli (xy/uv) -> encrypt ChaCha20 + XOR header
import base64, json
from Crypto.Cipher import ChaCha20

sys_key_index = 5
ENC_KEYS = None  # diisi dari HTTPCUSTOM biar satu sumber

def _init():
    global ENC_KEYS
    if ENC_KEYS is None:
        import HTTPCUSTOM as HC
        ENC_KEYS = HC.HCConstants.CHACHA_KEYS
    return ENC_KEYS

STATIC_NONCE = b'\xdb' * 8
XOR_HEADER = "e382e4b8adc386f09f9293"

def _abc_encrypt(plaintext: str, key: bytes, nonce: bytes = STATIC_NONCE) -> str:
    data = plaintext.encode()
    cipher = ChaCha20.new(key=key, nonce=nonce)
    cipher.seek(64)
    return (cipher.encrypt(data) + bytes(16)).hex()

def _rst_encrypt(hex_cipher: str) -> str:
    """Balikan _rst_decrypt: XOR dgn RST_XOR_KEY lalu base64 (varian v2.8+)."""
    import HTTPCUSTOM as HC
    data = bytes.fromhex(hex_cipher)
    out = bytes(b ^ HC.HCConstants.RST_XOR_KEY[i % len(HC.HCConstants.RST_XOR_KEY)]
                for i, b in enumerate(data))
    return base64.b64encode(out).decode()

def _unlock_cfg(config: dict) -> dict:
    """Buka semua proteksi di objek Config hasil decrypt."""
    c = dict(config)
    for k in ("lockAllConfig", "blockedByRoot", "blockedByHwid",
              "blockedByPassword", "mobileDataAndLockProvider",
              "unlockUserAndPass", "unlockUserAndPass2", "blockArea"):
        if k in c: c[k] = "false"
    if "expiryTime" in c: c["expiryTime"] = "lifeTime"
    if "notes" in c:
        c["notes"] = ("🐴 UNLOCKED by @BleackCoderr\n"
                      "https://sniffconfig.onrender.com")
    if "noteEnabled" in c: c["noteEnabled"] = "true"
    return c

def _tokens_from_config(config: dict):
    """Susun kembali daftar token urut TOKEN_MAP -> dipisah [splitConfig]."""
    import HTTPCUSTOM as HC
    tmap = HC.HCConstants.TOKEN_MAP
    inv = {v: k for k, v in tmap.items()}
    tokens = {}
    for name, val in config.items():
        if name in inv and val not in (None, ""):
            if isinstance(val, (dict, list)):
                try: val = json.dumps(val, ensure_ascii=False)
                except Exception: continue
            tokens[inv[name]] = str(val)
    return [tokens.get(i, "") for i in range(max(tokens.keys(), default=-1) + 1)]

def unlock_hc(original_file: bytes, magic_footer: str = "88a05e8772eac3e5703e0cd26c6e6f23de72fb09f7ee5a43283d1681f19d") -> bytes:
    """
    Input: file .hc asli. Output: file .hc unlocked (semua proteksi mati, expiry lifeTime).
    Jalur: decrypt penuh -> modifikasi Config -> encrypt balik pakai struktur asli.
    """
    _init()
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
    target = cfg_obj.get("content") if is_new else (j.get("xy") or a.get("xy"))
    split = cfg_obj.get("split") if is_new else (j.get("uv") or a.get("uv"))
    if not target or not split: raise ValueError("struktur file nggak dikenal")

    # decrypt field2 buat dapat Config lengkap (pakai jalur yang sama dgn engine)
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

    if is_new:
        xy_dec = d._rst_decrypt(str(target))
        if not xy_dec:
            for key in HC.HCConstants.CHACHA_KEYS:
                if (t := d._abc_decrypt(str(target), key)) and str(split) in t:
                    xy_dec = t; break
    else:
        xy_dec = d._abc_decrypt(str(target), HC.HCConstants.CHACHA_KEYS[1])
    if not xy_dec: raise ValueError("isi config nggak ke-decrypt")

    # token -> Config dict -> unlock -> token balik
    config = {}
    for i, token in enumerate(xy_dec.split(str(split))):
        if i in {22, 24}: continue
        label = HC.HCConstants.TOKEN_MAP.get(i, f"field_{i}")
        out = token
        if is_new:
            out = d._decrypt_field(token, bytes(nonce))
        else:
            if d._is_hex(token):
                out = d._abc_decrypt(token, HC.HCConstants.CHACHA_KEYS[7], bytes(nonce))
            out = d._jkl_decrypt(out, is_new=False)
        if i == 7: out = d._process_credentials(out, is_ssh=True)
        elif i == 11: out = d._process_credentials(out, is_ssh=False)
        if out:
            if isinstance(out, str):
                out = out.replace(magic_footer, "")
                try:
                    if out.startswith(("{", "[")): out = json.loads(out)
                except Exception: pass
            if not (isinstance(out, str) and d._is_hex(out)):
                config[label] = out

    unlocked = _unlock_cfg(config)
    tokens = _tokens_from_config(unlocked)
    new_xy = str(split).join(tokens)

    # re-encrypt dengan jalur yang sama (simetris)
    if is_new:
        content_enc = _rst_encrypt(d._abc_encrypt(new_xy, HC.HCConstants.CHACHA_KEYS[7], bytes(nonce)) if False else new_xy)
        # jalur baru: RST (xor+b64) langsung di atas plaintext hex-join
        cfg_obj["content"] = content_enc
        cfg_obj.pop("hwid", None); cfg_obj.pop("area", None)
        j["cfg"] = cfg_obj
        j.pop("b", None); j.pop("f", None)
    else:
        # jalur lama: token di-abc_encrypt per-field dgn key7+nonce, lalu xy di-encrypt key1
        enc_tokens = []
        for tok in tokens:
            t = tok.replace(magic_footer, "")
            t = _jkl_encrypt_if_needed(t, bytes(nonce))
            enc_tokens.append(t)
        new_xy2 = str(split).join(enc_tokens)
        j["xy"] = _abc_encrypt(new_xy2, HC.HCConstants.CHACHA_KEYS[1])
        if "a" in j and isinstance(j["a"], dict) and "xy" in j["a"]: j["a"]["xy"] = j["xy"]
        for k in ("bb", "e", "fe", "ed"):
            j.pop(k, None)
        if isinstance(j.get("a"), dict):
            for k in ("bb", "e", "fe", "ed"): j["a"].pop(k, None)

    outer_json = json.dumps(j, ensure_ascii=False, separators=(",", ":"))
    hex_outer = _abc_encrypt(outer_json, HC.HCConstants.CHACHA_KEYS[5])
    key_bytes = bytes.fromhex(XOR_HEADER)
    xored = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(hex_outer.encode("utf-8")))
    # engine baca: file.decode('utf-8', ignore).encode('latin-1') — jadi kita tulis persis jalur itu
    try:
        text = xored.decode("utf-8")
        return text.encode("utf-8")
    except UnicodeDecodeError:
        # kalau nggak valid utf-8, tulis latin-1 (engine decode utf-8 ignore lalu latin-1)
        return xored.decode("latin-1").encode("utf-8", errors="ignore")

def _jkl_encrypt_if_needed(token: str, nonce: bytes) -> str:
    """Token yang semula hex-encrypted harus balik ke bentuk hex.
    Gunakan: abc_encrypt(token, key7, nonce) -> hex, karena decrypt path memang
    abc_decrypt(token, key7, nonce)."""
    import HTTPCUSTOM as HC
    if not token: return token
    return _abc_encrypt(token, HC.HCConstants.CHACHA_KEYS[7], nonce)

def unlock_hc_simple(original_file: bytes) -> bytes:
    """Versi aman: hanya bongkar level luar, replace xy dgn token plaintext yang
    di-encrypt satu per satu, proteksi dimatikan di level Config."""
    return unlock_hc(original_file)
