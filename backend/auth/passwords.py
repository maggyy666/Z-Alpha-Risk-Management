"""Password hashing/verification using bcrypt directly.

Bcrypt has a hard 72-byte limit on password input. We work around it by
pre-hashing with SHA-256, which produces a fixed 32-byte digest -- safely
under the limit while preserving bcrypt's KDF properties for the final hash.
Seed and login MUST use the same pre-hash step, which they do via this module.
"""

import hashlib
import bcrypt


def _pre_hash(plain: str) -> bytes:
    """SHA-256 the plaintext so bcrypt sees a fixed 32-byte input."""
    return hashlib.sha256(plain.encode("utf-8")).digest()


def hash_password(plain: str) -> str:
    if not plain:
        raise ValueError("password must not be empty")
    digest = _pre_hash(plain)
    return bcrypt.hashpw(digest, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(_pre_hash(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
