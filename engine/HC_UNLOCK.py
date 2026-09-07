# HC Unlocker v2 — re-encrypt hasil decrypt ke file .hc yang bisa di-import HTTP Custom
# Prinsip: STRUKTUR JSON ASLI TIDAK DIUBAH. Hanya nilai xy (cipher token) yang diganti,
# meta dibiarkan (nonce derivation app tetap konsisten), proteksi dimatikan di level token.
import base64, json

STATIC_NONCE = b'\xdb' * 8
XOR_HEADER = "e382e4b8adc386f09f9293"
MAGIC = "88a05e8772eac3e5703e0cd26c6e6f23de72fb09f7ee5a43283d1681f19d"

def _abc_encrypt(plaintext: str, key: bytes, nonce: bytes = STATIC_NONCE) -> str:
    from Crypto.Cipher import ChaCha20
    data = plaintext.encode()
    cipher = ChaCha20.new(key=key, nonce=nonce)
    cipher.seek(64)
    return (cipher.encrypt(data) + bytes(16)).hex()

def _jkl_encrypt(plaintext: str) -> str:
    """Kebalikan persis _jkl_decrypt(is_new=False): (roundtrip terverifikasi)."""
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
    """Balikan _rst_decrypt (varian v2.8+): XOR RST_XOR_KEY lalu base64."""
    import HTTPCUSTOM as HC
    data = bytes.fromhex(hex_cipher)
    out = bytes(b ^ HC.HCConstants.RST_XOR_KEY[i % len(HC.HCConstants.RST_XOR_KEY)]
                for i, b in enumerate(data))
    return base64.b64encode(out).decode()

def _unlock_cfg(config: dict) -> dict:
    """Matikan semua proteksi di objek Config hasil decrypt."""
    c = dict(config)
    for k in ("lockAllConfig", "blockedByRoot", "blockedByHwid",
              "blockedByPassword", "mobileDataAndLockProvider",
              "blockArea"):
        if k in c: c[k] = "false"
    if "expiryTime" in c: c["expiryTime"] = "lifeTime"
    c["notes"] = "🐴 UNLOCKED by @BleackCoderr\nhttps://sniffconfig.onrender.com"
    c["noteEnabled"] = "true"
    return c

def _tokens_from_config(config: dict):
    """Susun kembali daftar token urut TOKEN_MAP."""
    import HTTPCUSTOM as HC
    inv = {v: k for k, v in HC.HCConstants.TOKEN_MAP.items()}
    tokens = {}
    for name, val in config.items():
        if name in inv and val not in (None, ""):
            if isinstance(val, (dict, list)):
                try: val = json.dumps(val, ensure_ascii=False)
                except Exception: continue
            tokens[inv[name]] = str(val)
    return [tokens.get(i, "") for i in range(max(tokens.keys(), default=-1) + 1)]

def unlock_hc(original_file: bytes) -> bytes:
    """Input file .hc asli -> output .hc unlocked (import-able)."""
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

    # nonce dinamis dari meta ASLI (yang tidak kita sentuh)
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

    # decrypt token2 (jalur engine)
    if is_new:
        xy_dec = d._rst_decrypt(str(target))
        if not xy_dec:
            for key in HC.HCConstants.CHACHA_KEYS:
                if (t := d._abc_decrypt(str(target), key)) and str(split) in t:
                    xy_dec = t; break
    else:
        xy_dec = d._abc_decrypt(str(target), HC.HCConstants.CHACHA_KEYS[1])
    if not xy_dec: raise ValueError("isi config nggak ke-decrypt")

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
                out = out.replace(MAGIC, "")
                try:
                    if out.startswith(("{", "[")): out = json.loads(out)
                except Exception: pass
            if not (isinstance(out, str) and d._is_hex(out)):
                config[label] = out

    unlocked = _unlock_cfg(config)
    tokens = _tokens_from_config(unlocked)

    if is_new:
        # RST plaintext-nya hasil join token; lalu content di-encrypt abc(key7,nonce) -> rst
        plain = str(split).join(tokens)
        cfg_obj["content"] = _rst_encrypt(_abc_encrypt(plain, HC.HCConstants.CHACHA_KEYS[7], bytes(nonce)))
        j["cfg"] = cfg_obj
    else:
        # jalur lama: tiap token: plaintext -> jkl_encrypt -> abc_encrypt(key7, nonce)
        enc = []
        for tok in tokens:
            t = str(tok).replace(MAGIC, "")
            t = _abc_encrypt(_jkl_encrypt(t), HC.HCConstants.CHACHA_KEYS[7], bytes(nonce))
            enc.append(t)
        new_xy = str(split).join(enc)
        if "xy" in a:
            a["xy"] = _abc_encrypt(new_xy, HC.HCConstants.CHACHA_KEYS[1])
        elif "xy" in j:
            j["xy"] = _abc_encrypt(new_xy, HC.HCConstants.CHACHA_KEYS[1])
        else:
            raise ValueError("posisi xy nggak ketemu")

    # KUNCI FIX: struktur JSON SAMA PERSIS dgn asli (kunci tidak ditambah/dihapus/dipindah)
    outer_json = json.dumps(j, ensure_ascii=False, separators=(",", ":"))
    hex_outer = _abc_encrypt(outer_json, HC.HCConstants.CHACHA_KEYS[5])
    key_bytes = bytes.fromhex(XOR_HEADER)
    xored = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(hex_outer.encode("utf-8")))
    try:
        return xored.decode("utf-8").encode("utf-8")
    except UnicodeDecodeError:
        return xored.decode("latin-1").encode("utf-8", errors="ignore")
