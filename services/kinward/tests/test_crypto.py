from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from kinward.crypto import (
    TokenDecryptionFailed,
    TokenEncryptionNotConfigured,
    decrypt_token,
    encrypt_token,
)


def test_encrypt_then_decrypt_round_trips() -> None:
    key = Fernet.generate_key().decode()
    ciphertext = encrypt_token(key, "a-refresh-token")
    assert ciphertext != "a-refresh-token"
    assert decrypt_token(key, ciphertext) == "a-refresh-token"


def test_encrypt_without_a_key_raises() -> None:
    with pytest.raises(TokenEncryptionNotConfigured):
        encrypt_token(None, "a-refresh-token")


def test_decrypt_without_a_key_raises() -> None:
    with pytest.raises(TokenEncryptionNotConfigured):
        decrypt_token(None, "ciphertext")


def test_decrypt_with_the_wrong_key_raises() -> None:
    key_a = Fernet.generate_key().decode()
    key_b = Fernet.generate_key().decode()
    ciphertext = encrypt_token(key_a, "a-refresh-token")
    with pytest.raises(TokenDecryptionFailed):
        decrypt_token(key_b, ciphertext)
