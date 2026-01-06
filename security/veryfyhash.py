"""Funkcje do weryfikacji skrótów ``bcrypt``."""


import os #biblioteka OS do obsługi plików na komputerze 

import bcrypt #biblioteka na bcrypt odpowiedzialna za hashowanie

from .hashing import _load_salt #   


def verify_password( # weryfikuje haslo uzytkownika wzgledem hasha bcrypt
    password: str,
    hashed: bytes,
    *,
    key_file: str | os.PathLike[str] | None = None,
) -> bool:
    """Sprawdza zgodność hasła w postaci jawnej ze skrótem ``bcrypt``."""

    try:
        salt = _load_salt(key_file)
        password_bytes = password.encode("utf-8")
        mixed_password = password_bytes + b":" + salt
        if bcrypt.checkpw(mixed_password, hashed):
            return True
        # Zgodnosc wsteczna dla haszy utworzonych bez dodatkowego mieszania soli.
        return bcrypt.checkpw(password_bytes, hashed)
    except (ValueError, FileNotFoundError):
        return False
