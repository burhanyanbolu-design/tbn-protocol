"""Generate a THROWAWAY local test signing key for the Hardin Chat prototype.
This is NOT the production Hardin Filter key -- that lives only on the server.
Only used so the prototype can run end-to-end locally for testing."""
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

HF_DIR = "data/hardin_filter"
os.makedirs(HF_DIR, exist_ok=True)

priv_path = f"{HF_DIR}/hardin_filter_signing_key.pem"
pub_path = f"{HF_DIR}/hardin_filter_signing_public.pem"

if os.path.exists(priv_path):
    print("test key already exists, skipping")
else:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(priv_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(pub_path, "wb") as f:
        f.write(key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))
    print("generated throwaway local test key at", priv_path)
