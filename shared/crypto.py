"""Hybrid cryptography utilities – AES‑256‑GCM payload, RSA‑2048‑OAEP key wrap."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Dict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AES_KEY_BYTES = 32  # 256‑bit key
RSA_BITS = 2048
NONCE_BYTES = 12  # per AES‑GCM spec


# ---------------------------------------------------------------------------
# Key management helpers
# ---------------------------------------------------------------------------

def generate_rsa_keypair(out_dir: Path, overwrite: bool = False) -> None:
    """Create *private.pem* & *public.pem* in *out_dir* (if not already present)."""

    out_dir.mkdir(parents=True, exist_ok=True)
    priv_path, pub_path = out_dir / "private.pem", out_dir / "public.pem"

    if not overwrite and (priv_path.exists() or pub_path.exists()):
        raise FileExistsError("Key files already exist; use overwrite=True to replace.")

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=RSA_BITS)

    priv_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pub_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    print(f"✅  Generated {priv_path} and {pub_path}")


# ---------------------------------------------------------------------------
# Hybrid encrypt / decrypt
# ---------------------------------------------------------------------------

def encrypt_data(plaintext: bytes, rsa_public_pem: bytes) -> Dict[str, str]:
    """Return JSON‑serialisable dict with wrapped AES key + ciphertext."""

    aes_key = os.urandom(AES_KEY_BYTES)
    nonce = os.urandom(NONCE_BYTES)

    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)

    public_key = serialization.load_pem_public_key(rsa_public_pem)
    wrapped_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return {
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "wrapped_key": base64.b64encode(wrapped_key).decode(),
    }


def decrypt_data(bundle: Dict[str, str], rsa_private_pem: bytes) -> bytes:
    private_key = serialization.load_pem_private_key(rsa_private_pem, password=None)

    aes_key = private_key.decrypt(
        base64.b64decode(bundle["wrapped_key"]),
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(
        base64.b64decode(bundle["nonce"]),
        base64.b64decode(bundle["ciphertext"]),
        associated_data=None,
    )
