"""Kriptografi katmanı.

- Her cihazın kalıcı bir X25519 kimlik anahtarı vardır.
- Mesajlar, gönderen ve alıcının statik anahtarlarından ECDH + HKDF ile
  türetilen anahtarla AES-256-GCM kullanılarak uçtan uca şifrelenir.
- Her mesajda rastgele salt + nonce kullanılır (anahtar tekrar kullanımı yok).
- Eşleştirme, PIN ile doğrulanan anahtar onayı (HMAC) içerir; PIN'i
  bilmeyen bir cihaz eşleşemez.
"""
import base64
import hashlib
import hmac
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

PAIRING_SALT = b"guvenli-pano-pairing-v1"
HKDF_INFO = b"guvenli-pano-mesaj-v1"


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode()


def b64d(text: str) -> bytes:
    return base64.b64decode(text)


class Identity:
    """Cihazın kalıcı kimlik anahtarı (diske kaydedilir)."""

    def __init__(self, path: Path):
        self.path = path
        if path.exists():
            self.private = X25519PrivateKey.from_private_bytes(path.read_bytes())
        else:
            self.private = X25519PrivateKey.generate()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(
                self.private.private_bytes(
                    serialization.Encoding.Raw,
                    serialization.PrivateFormat.Raw,
                    serialization.NoEncryption(),
                )
            )
            try:
                os.chmod(path, 0o600)  # sadece kullanıcı okuyabilsin
            except OSError:
                pass
        self.public_bytes = self.private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )

    @property
    def fingerprint(self) -> str:
        """Cihazın kısa parmak izi (kullanıcıya gösterilir)."""
        return hashlib.sha256(self.public_bytes).hexdigest()[:16]


def derive_key(private: X25519PrivateKey, peer_public: bytes, salt: bytes) -> bytes:
    """İki cihazın statik anahtarlarından 256 bit mesaj anahtarı türetir."""
    peer = X25519PublicKey.from_public_bytes(peer_public)
    secret = private.exchange(peer)
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=salt, info=HKDF_INFO
    ).derive(secret)


def encrypt(private: X25519PrivateKey, peer_public: bytes,
            plaintext: bytes, aad: bytes):
    """Uçtan uca şifrele. (salt, nonce, ciphertext) döndürür."""
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_key(private, peer_public, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    return salt, nonce, ciphertext


def decrypt(private: X25519PrivateKey, peer_public: bytes,
            salt: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes:
    """Şifreyi çöz. Anahtar veya AAD uyuşmazsa InvalidTag fırlatır."""
    key = derive_key(private, peer_public, salt)
    return AESGCM(key).decrypt(nonce, ciphertext, aad)


def pairing_tag(private: X25519PrivateKey, peer_public: bytes,
                pin: str, role: str) -> str:
    """PIN doğrulamalı eşleştirme etiketi.

    İki taraf da aynı ECDH anahtarını türetir; etiket PIN'i içerdiği için
    PIN'i bilmeyen (örn. araya giren) bir cihaz geçerli etiket üretemez.
    """
    key = derive_key(private, peer_public, PAIRING_SALT)
    msg = f"pin-confirm:{role}:{pin}".encode()
    return b64e(hmac.new(key, msg, hashlib.sha256).digest())


def verify_tag(expected: str, received: str) -> bool:
    return hmac.compare_digest(expected, received)


def aead_encrypt(key: bytes, plaintext: bytes, aad: bytes):
    """Hazır simetrik anahtarla (örn. SPAKE2 çıktısı) şifrele."""
    nonce = os.urandom(12)
    return nonce, AESGCM(key).encrypt(nonce, plaintext, aad)


def aead_decrypt(key: bytes, nonce: bytes, ciphertext: bytes,
                 aad: bytes) -> bytes:
    """Hazır simetrik anahtarla şifre çöz (doğrulama başarısızsa InvalidTag)."""
    return AESGCM(key).decrypt(nonce, ciphertext, aad)
