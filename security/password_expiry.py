"""Logika sprawdzania wygasniecia hasel.
Zawiera funkcje:
- is_password_expired(): Sprawdza czy data wygasniecia juz minela.
"""


from datetime import datetime


def is_password_expired(expire_date: datetime | None) -> bool: # sprawdza czy haslo wygaslo
    if expire_date is None:
        return False

    now = datetime.now(expire_date.tzinfo) if expire_date.tzinfo else datetime.now()
    return now.date() > expire_date.date()

