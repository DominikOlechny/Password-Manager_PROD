"""Pomocnicze funkcje do tworzenia skrótów haseł użytkowników."""

from __future__ import annotations

import os 
from pathlib import Path

import bcrypt

from .encrypt import KEY_FILE, _ensure_json_key


def _load_salt(key_file: str | os.PathLike[str] | None = None) -> bytes: # pobiera sol z key.json
    """Zwraca 32-bajtową sól z pliku ``key.json``.

    Plik klucza jest współdzielony z mechanizmami szyfrowania. W przypadku
    braku pliku zostanie zgłoszony ``FileNotFoundError``.
    """

    key_path = Path(key_file) if key_file is not None else KEY_FILE
    key = _ensure_json_key(key_path, create=False)
    if len(key) < 16:
        raise ValueError("Klucz w key.json jest zbyt krótki do wykorzystania jako sól.")
    return key


def hash_password( # tworzy hash hasla bcrypt
    password: str,
    *,
    key_file: str | os.PathLike[str] | None = None,
    rounds: int = 15,
) -> bytes:
    """Tworzy skrót hasła użytkownika z wykorzystaniem algorytmu ``bcrypt``.

    Parametry
    ---------
    password:
        Hasło w formie jawnej przekazane przez użytkownika.
    key_file:
        Opcjonalna ścieżka do niestandardowego pliku ``key.json`` z solą.
    rounds:
        Liczba rund użytych do generowania soli bcrypt.
    """

    salt = _load_salt(key_file) 
    password_bytes = password.encode("utf-8")
    mixed_password = password_bytes + b":" + salt
    bcrypt_salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(mixed_password, bcrypt_salt)
