"""Logika generowania hasel losowych dla uzytkownika.

Zawiera funkcje:
- generate_password(): Generuje haslo o zadanej dlugosci z bezpiecznego zestawu znakow.
"""

import random # losowy wybor znakow
import string # zestaw liter i cyfr


def generate_password(length: int = 16) -> str: # generuje losowe haslo o zadanej dlugosci
    """Generuje losowe haslo o zadanej dlugosci.

    Dlugosc jest ograniczana do bezpiecznego zakresu, aby uniknac bledow
    przy nieprawidlowych danych z interfejsu.
    """

    try:
        normalized_length = int(length)
    except (TypeError, ValueError):
        normalized_length = 16

    normalized_length = max(4, min(normalized_length, 128))

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_-+=[]{}"
    return "".join(random.choice(alphabet) for _ in range(normalized_length))
