"""Logika pomocnicza do zmiany daty waznosci oraz wypisywania listy hasel.

Zawiera funkcje:
- parse_expire(): Parsuje date waznosci w kilku formatach lub zwraca None.
- build_password_rows(): Buduje liste PasswordRow na potrzeby GUI.
"""
from datetime import datetime # do parsowania dat

from gui.models import PasswordRow # model wiersza hasla do GUI
from security.password_expiry import is_password_expired # sprawdza, czy haslo jest wygasle


def parse_expire(raw: str) -> datetime | None: # parsuje date waznosci z kilku formatow
    raw = raw.strip() # usuwa biale znaki z wejscia
    if not raw: # puste wejscie oznacza brak daty
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"): # dozwolone formaty daty
        try:
            return datetime.strptime(raw, fmt) # konwersja na datetime
        except ValueError:
            continue
    raise ValueError("Nieprawidlowy format daty waznosci.") # informuje o blednym formacie


def build_password_rows(entries: list[tuple]) -> list[PasswordRow]: # mapuje rekordy bazy na obiekty PasswordRow
    return [
        PasswordRow(
            entry_id=e[0], # id wpisu
            service=str(e[1] or ""), # nazwa uslugi
            login=str(e[2] or ""), # login uzytkownika
            password_text="********", # maska hasla
            revealed=False, # domyslnie ukryte
            expired=is_password_expired(e[4]), # flaga wygasniecia
        )
        for e in entries
    ]
