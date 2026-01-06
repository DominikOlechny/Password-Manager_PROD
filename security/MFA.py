"""Obsługa mechanizmu TOTP MFA dla użytkowników.

Wykorzystuje biblioteki ``pyotp`` do generowania i weryfikacji kodów
oraz istniejące funkcje szyfrujące aplikacji do bezpiecznego
przechowywania sekretów w bazie danych.
"""

import pyotp

from .decrypt import decrypt_with_user_secret
from .encrypt import encrypt_with_user_secret


def generate_mfa_secret() -> str: # generuje sekret MFA
    """Zwraca nowy sekret Base32 do konfiguracji aplikacji TOTP."""

    return pyotp.random_base32()


def build_provisioning_uri(login: str, secret: str, *, issuer: str = "Password Manager") -> str: # buduje URI provisioning
    """Tworzy URI w formacie zgodnym z Google Authenticator."""

    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=login, issuer_name=issuer)


def encrypt_mfa_secret(secret: str, user_secret: str) -> bytes: # szyfruje sekret MFA
    """Szyfruje sekret MFA wykorzystując hasło użytkownika."""

    encrypted = encrypt_with_user_secret(secret, user_secret)
    return encrypted.encode("ascii")


def decrypt_mfa_secret(encrypted_secret: bytes, user_secret: str) -> str: # odszyfrowuje sekret MFA
    """Deszyfruje sekret MFA zapisany w bazie."""

    if isinstance(encrypted_secret, memoryview):
        encrypted_secret = encrypted_secret.tobytes()
    if isinstance(encrypted_secret, bytearray):
        encrypted_secret = bytes(encrypted_secret)
    token = encrypted_secret.decode("ascii") if isinstance(encrypted_secret, bytes) else str(encrypted_secret)
    return decrypt_with_user_secret(token, user_secret).decode("utf-8")


def verify_mfa_code(secret: str, code: str) -> bool: # weryfikuje kod MFA
    """Sprawdza, czy kod TOTP jest prawidłowy z niewielkim oknem tolerancji."""

    normalized = code.strip()
    if not normalized:
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(normalized, valid_window=1))
