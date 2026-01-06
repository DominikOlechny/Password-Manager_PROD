"""Logika wstawiania i weryfikacji użytkowników w tabeli dbo.users. W tym miejscu dodawani są nowi użytkownicy oraz weryfikowane są ich dane logowania. MFA jest również obsługiwane tutaj.

Zawiera funkcje kolejno:
- create_user: Tworzy nowego użytkownika w dbo.users i zwraca jego users_id.
- verify_user: Weryfikuje użytkownika po loginie i haśle w postaci jawnej.
- update_user_credentials: Aktualizuje login i/lub hasło głównego zalogowanego użytkownika.
- VerificationResult: Klasa opisująca wynik próby logowania.


Dodatkowo używa funkcji z db_connection.py do zarządzania połączeniami z bazą danych, z tableusers_creation.py do zapewnienia istnienia tabeli użytkowników oraz funkcji z tablepassword_creation.py do zapewnienia istnienia tabeli przechowywania haseł dla użytkownika.
oraz security dla operacji związanych z bezpieczeństwem, takich jak szyfrowanie, odszyfrowywanie, haszowanie i weryfikacja haseł oraz obsługa wieloskładnikowego uwierzytelniania (MFA).
"""

from datetime import datetime #importowanie klasy datetime z modułu datetime
from typing import Literal, NamedTuple #importowanie klas Literal i NamedTuple z modułu typing

import pyodbc #importowanie modułu pyodbc do obsługi połączeń z bazą danych

from .db_connection import connect, disconnect #importowanie funkcji connect i disconnect z pliku db_connection.py
from .tableusers_creation import ensure_users_table #importowanie funkcji ensure_users_table z pliku tableusers_creation.py
from .tablepassword_creation import ensure_password_store_for_user #importowanie funkcji ensure_password_store_for_user z pliku tablepassword_creation.py
from security.MFA import ( # obsługa wieloskładnikowego uwierzytelniania
    build_provisioning_uri, 
    decrypt_mfa_secret,
    encrypt_mfa_secret,
    generate_mfa_secret,
    verify_mfa_code,
)
from security.decrypt import decrypt_with_user_secret # importowanie funkcji odszyfrowujących
from security.encrypt import encrypt_with_user_secret # importowanie funkcji szyfrujących
from security.hashing import hash_password # importowanie funkcji haszujących
from security.veryfyhash import verify_password # importowanie funkcji weryfikujących hasła


class VerificationResult(NamedTuple): #klasa opisująca wynik próby logowania
    """Opisuje wynik próby logowania."""

    status: Literal["ok", "locked", "invalid", "mfa_required", "mfa_invalid"]
    user_id: int | None
    login: str | None
    check_mfa: bool


def create_user( #tworzy nowego użytkownika w dbo.users i zwraca jego users_id
    login: str,
    secured_pwd: bytes,
    *,
    config_path: str = "config/db_config.json",
) -> int:
    """
    Tworzy nowego użytkownika w dbo.users i zwraca jego users_id.

    Parametry
    ---------
    login:
        Login użytkownika.
    secured_pwd:
        Hasło w postaci zabezpieczonej jako bytes, gotowe do zapisania w VARBINARY.
    config_path:
        ścieżka do pliku konfiguracyjnego z parametrami połączenia.

    Zwraca
    -------
    int
        Identyfikator nowego użytkownika (users_id).
    """
    ensure_users_table(config_path=config_path) #upewnij się, że tabela użytkowników istnieje
    conn = connect(config_path) #nawiązanie połączenia z bazą danych
    try: 
        cur = conn.cursor()
        cur.execute("USE [password_manager]")

        # wstawienie użytkownika z domyślnymi flagami bezpieczeństwa
        cur.execute(
            """
            INSERT INTO dbo.users (
                login,
                secured_pwd,
                check_mfa,
                mfa_secret,
                is_locked,
                failed_attempts,
                created_at,
                updated_at
            )
            OUTPUT INSERTED.users_id
            VALUES (
                ?,
                CAST(? AS varbinary(60)),
                0,
                NULL,
                0,
                0,
                SYSUTCDATETIME(),
                SYSUTCDATETIME()
            )
            """,
            login,
            secured_pwd,
        )
        new_user_id = cur.fetchone()[0]

        # gwarancja istnienia wspólnej tabeli dbo.entries
        ensure_password_store_for_user(
            user_id=new_user_id,
            conn=conn,
            db_name="password_manager",
            config_path=config_path,
        )

        conn.commit() 
        cur.close()
        return int(new_user_id)
    except Exception:
        # nic nie commitujemy, ale dla spójności rollback i ponowne zgłoszenie
        conn.rollback()
        raise
    finally:
        disconnect(conn)


def verify_user( #weryfikuje użytkownika po loginie i haśle w postaci jawnej
    login: str,
    password: str,
    mfa_code: str | None = None,
    config_path: str = "config/db_config.json",
) -> VerificationResult:
    """
    Weryfikuje użytkownika po loginie i haśle w postaci jawnej.

    Parametry
    ---------
    login:
        Login użytkownika.
    password:
        Hasło w postaci czystego tekstu, które zostanie porównane po odszyfrowaniu
        wartości zapisanej w bazie.
    config_path:
        ścieżka do pliku konfiguracyjnego z parametrami połączenia.

    Zwraca
    -------
    VerificationResult
        status:
            - ``"ok"`` gdy dane są poprawne,
            - ``"locked"`` gdy konto jest zablokowane,
            - ``"mfa_required"`` gdy potrzebny jest kod jednorazowy,
            - ``"mfa_invalid"`` dla błędnego kodu,
            - ``"invalid"`` w pozostałych przypadkach.
        user_id/login są dostępne tylko w statusie ``"ok"``.
    """
    ensure_users_table(config_path=config_path)
    conn = connect(config_path)
    try:
        cur = conn.cursor()
        cur.execute("USE [password_manager]")
        cur.execute(
            """
            SELECT users_id, login, secured_pwd, is_locked, failed_attempts, check_mfa, mfa_secret
            FROM dbo.users
            WHERE login = ?
            """,
            login,
        )
        row = cur.fetchone()
        if row is None:
            cur.close()
            return VerificationResult(status="invalid", user_id=None, login=None, check_mfa=False)

        user_id = int(row[0])
        user_login = str(row[1])
        stored_encrypted = row[2]
        is_locked = bool(row[3])
        failed_attempts = int(row[4])
        check_mfa = bool(row[5])
        stored_mfa_secret = row[6]

        if is_locked:
            cur.close()
            return VerificationResult(
                status="locked", user_id=user_id, login=user_login, check_mfa=check_mfa
            )

        if stored_encrypted is None:
            cur.close()
            return VerificationResult(status="invalid", user_id=None, login=None, check_mfa=False)

        stored_hash = _ensure_bytes(stored_encrypted)
        if not verify_password(password, stored_hash):
            new_failed_attempts = failed_attempts + 1
            lock_account = new_failed_attempts > 5
            cur.execute(
                """
                UPDATE dbo.users
                SET failed_attempts = ?, is_locked = ?, updated_at = SYSUTCDATETIME()
                WHERE users_id = ?
                """,
                new_failed_attempts,
                int(lock_account),
                user_id,
            )
            conn.commit()
            cur.close()
            return VerificationResult(status="invalid", user_id=None, login=None, check_mfa=check_mfa)

        normalized_mfa_code = mfa_code.strip() if mfa_code else ""
        if check_mfa:
            if stored_mfa_secret is None:
                # Nie ma sensu blokować logowania, jeśli konfiguracja MFA jest niekompletna – wyłącz wymaganie.
                cur.execute(
                    """
                    UPDATE dbo.users
                    SET check_mfa = 0, mfa_secret = NULL, updated_at = SYSUTCDATETIME()
                    WHERE users_id = ?
                    """,
                    user_id,
                )
                conn.commit()
                check_mfa = False
            else:
                secret = decrypt_mfa_secret(_extract_ascii_text(stored_mfa_secret), password)
                if not normalized_mfa_code:
                    cur.close()
                    return VerificationResult(
                        status="mfa_required",
                        user_id=user_id,
                        login=user_login,
                        check_mfa=True,
                    )
                if not verify_mfa_code(secret, normalized_mfa_code):
                    new_failed_attempts = failed_attempts + 1
                    lock_account = new_failed_attempts > 5
                    cur.execute(
                        """
                        UPDATE dbo.users
                        SET failed_attempts = ?, is_locked = ?, updated_at = SYSUTCDATETIME()
                        WHERE users_id = ?
                        """,
                        new_failed_attempts,
                        int(lock_account),
                        user_id,
                    )
                    conn.commit()
                    cur.close()
                    return VerificationResult(
                        status="mfa_invalid",
                        user_id=None,
                        login=None,
                        check_mfa=True,
                    )

        if failed_attempts != 0:
            cur.execute(
                """
                UPDATE dbo.users
                SET failed_attempts = 0, updated_at = SYSUTCDATETIME()
                WHERE users_id = ?
                """,
                user_id,
            )
            conn.commit()
        else:
            conn.commit()

        cur.close()
        return VerificationResult(
            status="ok", user_id=user_id, login=user_login, check_mfa=check_mfa
        ) # zwrócenie identyfikatora użytkownika i loginu
    finally:
        disconnect(conn) #rozłączenie z bazą danych


def _extract_ascii_text(raw_value) -> str: # konwertuje wartosc na tekst ASCII
    """Zwraca wartość VARBINARY/str w postaci tekstu ASCII."""

    if isinstance(raw_value, memoryview):
        raw_value = raw_value.tobytes()
    elif isinstance(raw_value, bytearray):
        raw_value = bytes(raw_value)

    if isinstance(raw_value, bytes):
        return raw_value.decode("ascii")
    return str(raw_value)


def _ensure_bytes(value) -> bytes: # normalizuje wartosc do bytes
    """Zapewnia, że przekazana wartość jest typu ``bytes``."""

    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("ascii")
    return value


def update_user_credentials( # aktualizuje login i/lub haslo uzytkownika
    user_id: int,
    old_password: str,
    *,
    new_login: str | None = None,
    new_password: str | None = None,
    config_path: str = "config/db_config.json",
) -> tuple[str, bool, bool]:
    """Aktualizuje login i/lub hasło główne zalogowanego użytkownika.

    Zwraca krotkę (nowy_login, czy_hasło_zmienione, czy_login_zmieniony).
    """

    if not old_password:
        raise ValueError("Podaj bieżące hasło.")

    ensure_users_table(config_path=config_path)
    conn = connect(config_path)
    try:
        cur = conn.cursor()
        cur.execute("USE [password_manager]")
        cur.execute(
            "SELECT login, secured_pwd, check_mfa, mfa_secret FROM dbo.users WHERE users_id = ?",
            user_id,
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Nie znaleziono użytkownika do edycji.")

        current_login = str(row[0])
        stored_encrypted = _ensure_bytes(row[1])
        stored_mfa_secret = _ensure_bytes(row[3]) if row[3] is not None else None
        if not verify_password(old_password, stored_encrypted):
            raise ValueError("Nieprawidłowe bieżące hasło.")

        target_login = new_login.strip() if new_login else current_login
        if not target_login:
            raise ValueError("Login nie może być pusty.")

        password_changed = bool(new_password and new_password.strip())
        login_changed = target_login != current_login

        if not login_changed and not password_changed:
            return current_login, False, False

        # upewnij się, że tabela haseł istnieje przed ewentualnym przeniesieniem
        ensure_password_store_for_user(
            user_id=user_id,
            conn=conn,
            config_path=config_path,
        )

        safe_old_login = current_login.replace("]", "]]")
        safe_new_login = target_login.replace("]", "]]")
        old_table_name = f"dbo.[{safe_old_login} entries]"
        new_table_name = f"dbo.[{safe_new_login} entries]"
        new_table_plain = f"{target_login} entries"
        escaped_old_for_rename = old_table_name.replace("'", "''")
        escaped_new_for_rename = new_table_plain.replace("'", "''")

        if login_changed:
            cur.execute(
                "SELECT 1 FROM dbo.users WHERE login = ? AND users_id <> ?",
                target_login,
                user_id,
            )
            if cur.fetchone():
                raise ValueError("Użytkownik o podanym loginie już istnieje.")

            # sprawdź czy docelowa tabela już nie istnieje
            cur.execute(
                """
                SELECT 1
                FROM sys.tables t
                JOIN sys.schemas s ON s.schema_id = t.schema_id
                WHERE s.name = 'dbo' AND t.name = ?
                """,
                f"{target_login} entries",
            )
            if cur.fetchone():
                raise ValueError(
                    "Tabela haseł dla nowego loginu już istnieje. Wybierz inny login."
                )

            cur.execute(
                f"EXEC sp_rename '{escaped_old_for_rename}', '{escaped_new_for_rename}', 'OBJECT'"
            )

        table_to_use = new_table_name if login_changed else old_table_name

        if password_changed:
            normalized_new_pwd = new_password.strip()
            cur.execute(
                f"SELECT id, password FROM {table_to_use} WHERE user_id = ?",
                user_id,
            )
            rows = cur.fetchall()
            for entry_row in rows:
                encrypted_value = _extract_ascii_text(entry_row[1])
                decrypted_value = decrypt_with_user_secret(
                    encrypted_value, old_password
                ).decode("utf-8")
                new_encrypted = encrypt_with_user_secret(
                    decrypted_value, normalized_new_pwd
                ).encode("ascii")
                cur.execute(
                    f"""
                    UPDATE {table_to_use}
                    SET password = ?, updated_at = SYSUTCDATETIME()
                    WHERE id = ? AND user_id = ?
                    """,
                    new_encrypted,
                    int(entry_row[0]),
                    user_id,
                )

            if stored_mfa_secret is not None:
                decrypted_mfa_secret = decrypt_mfa_secret(
                    _extract_ascii_text(stored_mfa_secret), old_password
                )
                new_mfa_secret = encrypt_mfa_secret(
                    decrypted_mfa_secret, normalized_new_pwd
                )
            else:
                new_mfa_secret = None

            new_secured_pwd = hash_password(normalized_new_pwd)
        else:
            new_secured_pwd = _ensure_bytes(row[1])
            new_mfa_secret = stored_mfa_secret

        cur.execute(
            """
            UPDATE dbo.users
            SET login = ?, secured_pwd = CAST(? AS varbinary(60)), mfa_secret = CAST(? AS varbinary(max)), updated_at = SYSUTCDATETIME()
            WHERE users_id = ?
            """,
            target_login,
            new_secured_pwd,
            new_mfa_secret,
            user_id,
        )

        conn.commit()
        cur.close()
        return target_login, password_changed, login_changed
    except Exception:
        conn.rollback()
        raise
    finally:
        disconnect(conn)


def ensure_user_mfa_state( # zarzadza stanem MFA uzytkownika
    user_id: int,
    user_secret: str,
    mfa_code: str | None = None,
    *,
    config_path: str = "config/db_config.json",
) -> tuple[bool, str]:
    """
    Zarządza stanem MFA użytkownika.

    Zwraca krotkę (czy_zmieniono_status, komunikat).
    - Jeśli sekret nie istnieje, generuje go i zwraca instrukcję konfiguracji.
    - Jeśli kod jest podany i poprawny, włącza/wyłącza MFA.
    """

    ensure_users_table(config_path=config_path)
    conn = connect(config_path)
    try:
        cur = conn.cursor()
        cur.execute("USE [password_manager]")
        cur.execute(
            "SELECT login, check_mfa, mfa_secret FROM dbo.users WHERE users_id = ?",
            user_id,
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Nie znaleziono użytkownika.")

        login = str(row[0])
        check_mfa = bool(row[1])
        stored_secret = row[2]
        normalized_code = mfa_code.strip() if mfa_code else ""

        if stored_secret is None:
            new_secret = generate_mfa_secret()
            encrypted_secret = encrypt_mfa_secret(new_secret, user_secret)
            cur.execute(
                """
                UPDATE dbo.users
                SET mfa_secret = CAST(? AS varbinary(max)), updated_at = SYSUTCDATETIME()
                WHERE users_id = ?
                """,
                encrypted_secret,
                user_id,
            )
            conn.commit()
            uri = build_provisioning_uri(login, new_secret)
            return False, (
                "[i] Wygenerowano sekret MFA. Dodaj go do aplikacji "
                f"(sekret: {new_secret}). URI dla Authenticatora: {uri}. "
                "Podaj kod z aplikacji, aby aktywować MFA."
            )

        secret = decrypt_mfa_secret(_extract_ascii_text(stored_secret), user_secret)
        if not normalized_code:
            if check_mfa:
                return False, "[i] MFA jest już aktywne. Podaj aktualny kod, aby je wyłączyć."
            uri = build_provisioning_uri(login, secret)
            return False, (
                "[i] Sekret MFA istnieje. Dodaj konto w aplikacji (sekret: "
                f"{secret}). URI: {uri}. Następnie podaj kod, aby włączyć MFA."
            )

        if not verify_mfa_code(secret, normalized_code):
            raise ValueError("Nieprawidłowy kod MFA.")

        if check_mfa:
            cur.execute(
                """
                UPDATE dbo.users
                SET check_mfa = 0, mfa_secret = NULL, updated_at = SYSUTCDATETIME()
                WHERE users_id = ?
                """,
                user_id,
            )
            conn.commit()
            return True, "[+] Wyłączono MFA dla konta."

        cur.execute(
            """
            UPDATE dbo.users
            SET check_mfa = 1, updated_at = SYSUTCDATETIME()
            WHERE users_id = ?
            """,
            user_id,
        )
        conn.commit()
        return True, "[+] Włączono MFA dla konta."
    finally:
        disconnect(conn)


def get_user_mfa_provisioning( # zwraca dane provisioning MFA
    user_id: int, user_secret: str, *, config_path: str = "config/db_config.json"
) -> tuple[str, str, bool]:
    """
    Zwraca aktualny sekret MFA, URI provisioning oraz flagę aktywacji.

    Jeżeli sekret nie istnieje, zostanie wygenerowany i zapisany w bazie.
    """

    ensure_users_table(config_path=config_path) #upewnij się, że tabela użytkowników istnieje
    conn = connect(config_path) #nawiązanie połączenia z bazą danych
    try: #logika pobierania sekretu MFA i URI provisioning
        cur = conn.cursor() #utworzenie kursora do wykonywania zapytań SQL
        cur.execute("USE [password_manager]") #przełączenie na odpowiednią bazę danych
        cur.execute( 
            "SELECT login, check_mfa, mfa_secret FROM dbo.users WHERE users_id = ?",
            user_id,
        )
        row = cur.fetchone() #pobranie wyniku zapytania
        if row is None: 
            raise ValueError("Nie znaleziono użytkownika.") #jeżeli użytkownik nie istnieje to zgłoś błąd

        login = str(row[0]) #pobranie loginu użytkownika
        check_mfa = bool(row[1]) #pobranie flagi czy MFA jest aktywne
        stored_secret = row[2] #pobranie sekretu MFA

        if stored_secret is None:  #jeżeli sekret nie istnieje to wygeneruj nowy
            secret = generate_mfa_secret() #generowanie sekretu MFA
            encrypted_secret = encrypt_mfa_secret(secret, user_secret) #szyfrowanie sekretu MFA
            cur.execute(
                """
                UPDATE dbo.users
                SET mfa_secret = CAST(? AS varbinary(max)), updated_at = SYSUTCDATETIME()
                WHERE users_id = ?
                """,
                encrypted_secret,
                user_id,
            )
            conn.commit() #zatwierdzenie zmian w bazie danych
        else: #jeżeli sekret istnieje to odszyfruj go
            secret = decrypt_mfa_secret(_extract_ascii_text(stored_secret), user_secret)

        uri = build_provisioning_uri(login, secret) #budowanie URI provisioning
        return secret, uri, check_mfa #zwrócenie sekretu, URI i flagi aktywacji MFA
    except Exception: #jeżeli wystąpi błąd to wycofaj zmiany
        conn.rollback() #rozłączenie z bazą danych
        raise #ponowne zgłoszenie wyjątku
    finally: 
        disconnect(conn) #rozłączenie z bazą danych
