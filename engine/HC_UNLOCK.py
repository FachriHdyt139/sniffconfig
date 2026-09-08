# HC Unlocker v5 — "TRUE AEAD" (2026-09-08)
# AKAR MASALAH FINAL (terbukti via pynacl/libsodium):
# Semua layer .hc = crypto_aead_chacha20poly1305 ORIGINAL (nonce 8 byte 0xdb*8),
# 16 byte terakhir = Poly1305 auth tag ASLI. Engine decrypt lama toleran (buang
# 16 byte tanpa verifikasi) makanya hasil unlock v3/v4 "kelihatan" valid tapi
# app HTTP Custom memverifikasi tag -> "Bukan file config yang valid".
# v5: re-encrypt pakai AEAD sungguhan -> tag valid -> app terima.
# Strategi tetap surgical: token polos diganti polos, token terenkripsi TIDAK disentuh.
import json, re

XOR_HEADER = "e382e4b8adc386f09f9293"

# posisi token -> nilai BARU (teks polos, gaya sama dgn aslinya)
UNLOCK_VALUES = {
    2:  "false",   # lockAllConfig
    3:  "false",   # blockedByRoot
    4:  "lifeTime",# expiryTime
    5:  "true",    # noteEnabled
    6:  "\U0001F434 UNLOCKED by @BleackCoderr\nhttps://sniffconfig.onrender.com",  # notes
    15: "false",   # blockedByHwid
    16: "false",   # cloudconfig
    19: "false",   # blockArea
    21: "false",   # blockedByPassword
}

def _aead_encrypt(plaintext: bytes, key: bytes, nonce: bytes) -> bytes:
    from nacl.bindings import crypto_aead_chacha20poly1305_encrypt
    return crypto_aead_chacha20poly1305_encrypt(plaintext, b"", nonce, key)

def _aead_decrypt(blob: bytes, key: bytes, nonce: bytes) -> bytes:
    from nacl.bindings import crypto_aead_chacha20poly1305_decrypt
    return crypto_aead_chacha20poly1305_decrypt(blob, b"", nonce, key)

def _clean_hex(s: str) -> str:
    c = re.sub(r'[^0-9a-fA-F]', '', s)
    return c if len(c) % 2 == 0 else '0' + c

def unlock_hc(original_file: bytes) -> bytes:
    """Unlock .hc dengan AEAD tag asli — importable ke HTTP Custom."""
    import HTTPCUSTOM as HC
    d = HC.HCDecryptor
    K = HC.HCConstants

    hex_payload = d._extract_initial_payload(original_file, XOR_HEADER)
    if not hex_payload:
        raise ValueError("header file bukan .hc")
    outer_bytes = _aead_decrypt(bytes.fromhex(_clean_hex(hex_payload)), K.CHACHA_KEYS[5], K.STATIC_NONCE)
    outer = outer_bytes.decode('utf-8')
    if not outer.startswith("{"):
        raise ValueError("decrypt luar gagal")
    j = json.loads(outer)

    a = j.get("a") if isinstance(j.get("a"), dict) else {}
    xy_cipher = a.get("xy") or j.get("xy")
    uv_cipher = a.get("uv") or j.get("uv")
    if not xy_cipher or not uv_cipher:
        raise ValueError("bukan format HC lama (a.xy/a.uv tidak ada)")

    # uuid/split delimiter = decrypt uv dengan key7
    uuid = _aead_decrypt(bytes.fromhex(_clean_hex(uv_cipher)), K.CHACHA_KEYS[7], K.STATIC_NONCE).decode()
    # delimiter di dalam xy = HEX dari ciphertext uv (persis gaya app HC)
    split = _clean_hex(uv_cipher)

    # decrypt xy (key1) -> token list
    xy_plain = _aead_decrypt(bytes.fromhex(_clean_hex(xy_cipher)), K.CHACHA_KEYS[1], K.STATIC_NONCE).decode('utf-8')
    tokens = xy_plain.split(split)
    if len(tokens) < 22:
        raise ValueError(f"jumlah token aneh ({len(tokens)}) — bukan HC standar")

    # guard: field yang mau diubah harus teks polos (bukan hex terenkripsi)
    for i in UNLOCK_VALUES:
        t = tokens[i] if i < len(tokens) else ""
        if t and re.fullmatch(r"[0-9a-fA-F]{32,}", t):
            raise ValueError(f"token posisi {i} terenkripsi — file varian berkunci, lapor @BleackCoderr")

    for i, new_val in UNLOCK_VALUES.items():
        if i < len(tokens):
            tokens[i] = new_val

    new_xy = split.join(tokens)
    # re-encrypt SEMUA layer dengan AEAD asli (tag beneran)
    a["xy"] = _aead_encrypt(new_xy.encode('utf-8'), K.CHACHA_KEYS[1], K.STATIC_NONCE).hex()
    outer_json = json.dumps(j, indent=2, ensure_ascii=False)
    hex_outer = _aead_encrypt(outer_json.encode('utf-8'), K.CHACHA_KEYS[5], K.STATIC_NONCE).hex()

    kb = bytes.fromhex(XOR_HEADER)
    xored = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(hex_outer.encode("utf-8")))
    return xored.decode("latin-1").encode("utf-8")
