from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class TokenEncryptionNotConfigured(RuntimeError):
    """Raised when a Google/Microsoft OAuth token needs encrypting or decrypting but
    ``KINWARD_ACCOUNT_TOKEN_ENCRYPTION_KEY`` is not set - callers must treat this the
    same as "provider not configured," never store plaintext as a fallback.
    """


class TokenDecryptionFailed(RuntimeError):
    """The stored ciphertext didn't decrypt under the configured key - either the key
    rotated or the row was tampered with. Callers should treat the account as needing
    reauthorization rather than crash the sync pass.
    """


def encrypt_token(key: str | None, plaintext: str) -> str:
    if not key:
        raise TokenEncryptionNotConfigured
    return Fernet(key.encode()).encrypt(plaintext.encode()).decode()


def decrypt_token(key: str | None, ciphertext: str) -> str:
    if not key:
        raise TokenEncryptionNotConfigured
    try:
        return Fernet(key.encode()).decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise TokenDecryptionFailed from exc
