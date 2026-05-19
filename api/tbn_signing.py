"""
TBN Protocol — Response Signing (Cryptographically Verifiable Identity)
Provides RSA signatures on verification responses so downstream systems
can prove the response came from TBN (provenance, not just integrity).

Public key is published at /api/signing/public-key

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0. Trace: HRD-RS-6a4e2d9c
"""

import os
import json
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

SIGNING_KEY_PATH = "data/tbn_signing_key.pem"
PUBLIC_KEY_PATH = "data/tbn_signing_public.pem"


def _load_or_generate_keys():
    """Load existing signing keys or generate new ones."""
    if os.path.exists(SIGNING_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        with open(SIGNING_KEY_PATH, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(PUBLIC_KEY_PATH, "rb") as f:
            public_key_pem = f.read()
        return private_key, public_key_pem

    # Generate new key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Save private key
    os.makedirs(os.path.dirname(SIGNING_KEY_PATH) or ".", exist_ok=True)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(SIGNING_KEY_PATH, "wb") as f:
        f.write(private_pem)

    # Save public key
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(public_key_pem)

    print("[TBN Signing] Generated new RSA-2048 signing key pair")
    return private_key, public_key_pem


# Load keys on import
_private_key, _public_key_pem = _load_or_generate_keys()


def sign_response(response_data: dict) -> str:
    """
    Sign a verification response with TBN's private key.
    Returns base64-encoded RSA signature.
    
    Downstream systems can verify this signature using TBN's public key
    (available at /api/signing/public-key) to prove the response
    came from TBN and hasn't been altered.
    """
    import base64

    # Create canonical JSON (sorted keys, no whitespace)
    canonical = json.dumps(response_data, sort_keys=True, separators=(",", ":"))

    # Sign with RSA-PSS
    signature = _private_key.sign(
        canonical.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode()


def get_public_key_pem() -> str:
    """Return the public key PEM for verification."""
    return _public_key_pem.decode()


def verify_signature(response_data: dict, signature_b64: str) -> bool:
    """
    Verify a TBN response signature.
    Used for testing / demonstration.
    """
    import base64

    try:
        canonical = json.dumps(response_data, sort_keys=True, separators=(",", ":"))
        signature = base64.b64decode(signature_b64)

        public_key = serialization.load_pem_public_key(_public_key_pem)
        public_key.verify(
            signature,
            canonical.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
