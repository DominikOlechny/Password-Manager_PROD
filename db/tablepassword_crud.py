"""Logika CRUD dla wpisów haseł użytkowników. W tym miejscu dodawane, odczytywane, aktualizowane i usuwane są wpisy haseł w dedykowanych tabelach użytkowników.

Zawiera funkcje do tworzenia, odczytu, aktualizacji i usuwania wpisów haseł w dedykowanych tabelach użytkowników. Tworzonych kiedy rejestrowane jest konto
Kolejno:
- add_password_entry: Dodaje nowe hasło użytkownika do dedykowanej tabeli haseł.
- list_password_entries: Wyświetla listę wpisów użytkownika.
- update_password_entry: Aktualizuje wpis hasła użytkownika.
- delete_password_entry: Usuwa wpis hasła użytkownika o podanym ID.
- get_password_entry: Zwraca pojedynczy wpis użytkownika wraz z zaszyfrowanym hasłem.
- copy_password_to_clipboard: Kopiuje tekst do schowka systemowego.
- _get_user_table_name: Pomocnicza funkcja do uzyskania nazwy tabeli haseł użytkownika.

Dodatkowo używa funkcji z db_connection.py do zarządzania połączeniami z bazą danych oraz funkcji z tablepassword_creation.py do zapewnienia istnienia tabeli haseł użytkowników. oraz security/decrypt.py do odszyfrowywania haseł.

Umieszczono tu również menu CLI.
"""

from datetime import datetime #importowanie klasy datetime z modułu datetime
import pyodbc #importowanie modułu pyodbc do obsługi połączeń z bazą danych
import importlib #importowanie modułu importlib do dynamicznego ładowania modułów
import threading #importowanie modułu threading do opóźnionego czyszczenia schowka
from security.decrypt import decrypt_with_user_secret #importowanie funkcji do odszyfrowywania haseł

from db.db_connection import connect, disconnect #importowanie funkcji connect i disconnect z pliku db_connection.py
from db.tablepassword_creation import ensure_password_store_for_user #importowanie funkcji ensure_password_store_for_user z pliku tablepassword_creation.py


def _get_user_table_name(cur, user_id: int) -> str: #pomocnicza funkcja do uzyskania nazwy tabeli haseł użytkownika
    """Zwraca w pełni kwalifikowaną nazwę tabeli haseł dla użytkownika."""
    cur.execute("SELECT login FROM dbo.users WHERE users_id = ?", user_id) #wykonanie zapytania SQL w celu pobrania loginu użytkownika
    row = cur.fetchone() #pobranie pierwszego wiersza wyniku zapytania
    if not row or not row[0]: #sprawdzenie, czy wiersz istnieje i czy zawiera login
        raise ValueError(f"user_id {user_id} not found in dbo.users") #jeśli nie, zgłoszenie wyjątku ValueError

    login = str(row[0]) #konwersja loginu na string

    # Ucieczka znaku ']' w nazwie loginu
    bracketed_login = login.replace("]", "]]")
    return f"dbo.[{bracketed_login} entries]"


def add_password_entry( #dodaje nowe hasło użytkownika do dedykowanej tabeli haseł
    user_id: int, #ID użytkownika
    service: str, #nazwa usługi
    account_login: str, #login do konta
    account_password: bytes, #zaszyfrowane hasło do konta
    expire_date=None, #data wygaśnięcia hasła (opcjonalne)
    *,
    config_path: str = "config/db_config.json", #ścieżka do pliku konfiguracyjnego bazy danych
) -> int: 
    """Dodaje nowe hasło użytkownika do dedykowanej tabeli haseł."""
    ensure_password_store_for_user( #upewnij się, że tabela przechowywania haseł dla użytkownika istnieje
        user_id=user_id, #wskazanie ID użytkownika
        db_name="password_manager", #nazwa bazy danych
        config_path=config_path, #ścieżka do pliku konfiguracyjnego bazy danych
    )

    conn = connect(config_path) #nawiązanie połączenia z bazą danych
    try:
        cur = conn.cursor() #utworzenie kursora do wykonywania zapytań SQL
        cur.execute("USE [password_manager]") #wybranie bazy danych password_manager
        table_name = _get_user_table_name(cur, user_id) #get_user_table_name - uzyskanie nazwy tabeli haseł użytkownika

        cur.execute( #dodanie nowego wpisu hasła do tabeli
            f"""
            INSERT INTO {table_name} (
                user_id,
                service,
                login,
                password,
                created_at,
                updated_at,
                expire_date
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME(), ?)
            """,
            user_id, #ID użytkownika
            service, #nazwa usługi
            account_login, #login do konta
            account_password, #zaszyfrowane hasło do konta
            expire_date, #data wygaśnięcia hasła (opcjonalne
        )
        new_id = cur.fetchone()[0] #pobranie ID nowo dodanego wpisu
        conn.commit() #zatwierdzenie transakcji
        cur.close() #zamknięcie kursora
        return int(new_id) #zwrócenie ID nowo dodanego wpisu jako liczba całkowita
    except Exception: #w przypadku wystąpienia wyjątku
        conn.rollback() #wycofanie transakcji
        raise #ponowne zgłoszenie wyjątku
    finally: #na koniec
        disconnect(conn) #rozłączenie z bazą danych


def list_password_entries( #wyświetla listę wpisów użytkownika
    user_id: int, #ID użytkownika
    *, #argumenty nazwane
    config_path: str = "config/db_config.json", #ścieżka do pliku konfiguracyjnego bazy danych
):
    """Zwraca listę wpisów użytkownika (id, service, login, created_at, expire_date)."""
    ensure_password_store_for_user( #upewnij się, że tabela przechowywania haseł dla użytkownika istnieje
        user_id=user_id, #wskazanie ID użytkownika
        db_name="password_manager", #nazwa bazy danych
        config_path=config_path, #ścieżka do pliku konfiguracyjnego bazy danych
    )

    conn = connect(config_path) #nawiązanie połączenia z bazą danych
    try: #na początku bloku try
        cur = conn.cursor() #utworzenie kursora do wykonywania zapytań SQL
        cur.execute("USE [password_manager]") #wybranie bazy danych password_manager
        table_name = _get_user_table_name(cur, user_id) #get_user_table_name - uzyskanie nazwy tabeli haseł użytkownika

        cur.execute( #wykonanie zapytania SQL w celu pobrania wpisów hasła użytkownika
            f"""
            SELECT
                id,
                service,
                login,
                created_at,
                expire_date
            FROM {table_name}
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            user_id,
        )
        rows = cur.fetchall() #pobranie wszystkich wierszy wyniku zapytania
        cur.close() #zamknięcie kursora

        result: list[tuple[int, str, str, datetime, datetime | None]] = [] #inicjalizacja pustej listy do przechowywania wyników
        for r in rows: #iteracja po pobranych wierszach
            result.append( #dodanie wpisu do listy wyników
                (
                    int(r.id), #ID wpisu jako liczba całkowita
                    str(r.service), #nazwa usługi jako string
                    str(r.login), #login do konta jako string
                    r.created_at, #data utworzenia wpisu
                    r.expire_date, #data wygaśnięcia wpisu (lub None)
                )
            )
        return result #zwrócenie listy wyników
    finally: #na koniec
        disconnect(conn) #rozłączenie z bazą danych


def update_password_entry( #aktualizuje wpis hasła użytkownika
    user_id: int, #ID użytkownika
    entry_id: int, #ID wpisu do aktualizacji
    *,
    new_service=None, #nowa nazwa usługi
    new_login=None, #nowy login do konta
    new_password=None, #nowe zaszyfrowane hasło do konta
    new_expire_date=None, #nowa data wygaśnięcia hasła
    config_path: str = "config/db_config.json", #ścieżka do pliku konfiguracyjnego bazy danych
) -> bool: 
    """Aktualizuje wskazany wpis użytkownika."""
    ensure_password_store_for_user( #upewnij się, że tabela przechowywania haseł dla użytkownika istnieje
        user_id=user_id, #wskazanie ID użytkownika
        db_name="password_manager", #nazwa bazy danych
        config_path=config_path, #ścieżka do pliku konfiguracyjnego bazy danych
    )

    conn = connect(config_path) #nawiązanie połączenia z bazą danych
    try: #na początku bloku try
        cur = conn.cursor() #utworzenie kursora do wykonywania zapytań SQL
        cur.execute("USE [password_manager]") #wybranie bazy danych password_manager
        table_name = _get_user_table_name(cur, user_id) #get_user_table_name - uzyskanie nazwy tabeli haseł użytkownika

        cur.execute( #wykonanie zapytania SQL w celu aktualizacji wpisu hasła użytkownika
            f"""
            UPDATE {table_name}
            SET
                service = COALESCE(?, service),
                login = COALESCE(?, login),
                password = COALESCE(?, password),
                expire_date = COALESCE(?, expire_date),
                updated_at = SYSUTCDATETIME()
            WHERE id = ? AND user_id = ?
            """,
            new_service,
            new_login,
            new_password,
            new_expire_date,
            entry_id,
            user_id,
        )
        affected = cur.rowcount #pobranie liczby zmodyfikowanych wierszy
        conn.commit() #zatwierdzenie transakcji
        cur.close() #zamknięcie kursora
        return affected == 1 #zwrócenie True, jeśli jeden wiersz został zaktualizowany
    except Exception: #w przypadku wystąpienia wyjątku
        conn.rollback() #wycofanie transakcji
        raise #ponowne zgłoszenie wyjątku
    finally: #na koniec
        disconnect(conn) #rozłączenie z bazą danych


def delete_password_entry( #usuwa wpis hasła użytkownika o podanym ID
    user_id: int,
    entry_id: int,
    *,
    config_path: str = "config/db_config.json",
) -> bool:
    """Usuwa wpis użytkownika o podanym ID."""
    ensure_password_store_for_user(
        user_id=user_id,
        db_name="password_manager",
        config_path=config_path,
    )

    conn = connect(config_path)
    try:
        cur = conn.cursor()
        cur.execute("USE [password_manager]")
        table_name = _get_user_table_name(cur, user_id)

        cur.execute(
            f"DELETE FROM {table_name} WHERE id = ? AND user_id = ?",
            entry_id,
            user_id,
        )
        affected = cur.rowcount
        conn.commit()
        cur.close()
        return affected == 1
    except Exception:
        conn.rollback() 
        raise
    finally:
        disconnect(conn) #rozłączenie z bazą danych

def get_password_entry( # pobiera pojedynczy wpis hasla
    user_id: int,
    entry_id: int,
    *,
    config_path: str = "config/db_config.json",
):
    """Zwraca pojedynczy wpis użytkownika wraz z zaszyfrowanym hasłem."""

    ensure_password_store_for_user( #upewnij się, że tabela przechowywania haseł dla użytkownika istnieje
        user_id=user_id,
        db_name="password_manager",
        config_path=config_path,
    )

    conn = connect(config_path) #nawiązanie połączenia z bazą danych
    try: #na początku bloku try
        cur = conn.cursor() #utworzenie kursora do wykonywania zapytań SQL
        cur.execute("USE [password_manager]") #wybranie bazy danych password_manager
        table_name = _get_user_table_name(cur, user_id) #get_user_table_name - uzyskanie nazwy tabeli haseł użytkownika

        cur.execute( #wykonanie zapytania SQL w celu pobrania wpisu hasła użytkownika o podanym ID
            f"""
            SELECT
                id,
                service,
                login,
                password,
                created_at,
                expire_date
            FROM {table_name}
            WHERE id = ? AND user_id = ?
            """,
            entry_id,
            user_id,
        )
        row = cur.fetchone() #pobranie pierwszego wiersza wyniku zapytania
        cur.close() #zamknięcie kursora

        if row is None: #jeśli wiersz nie istnieje
            return None #zwrócenie None

        password_value = row.password #pobranie wartości hasła z wiersza
        if isinstance(password_value, memoryview): #jeśli wartość hasła jest typu memoryview
            password_bytes = password_value.tobytes() #konwersja na bytes
        elif isinstance(password_value, bytearray): #jeśli wartość hasła jest typu bytearray
            password_bytes = bytes(password_value) #konwersja na bytes
        elif isinstance(password_value, str): #jeśli wartość hasła jest typu str
            password_bytes = password_value.encode("ascii") #konwersja na bytes
        else: #w przeciwnym razie
            password_bytes = password_value #przypisanie wartości bez zmian

        return ( #zwrócenie wpisu jako krotki
            int(row.id), #ID wpisu jako liczba całkowita
            str(row.service), #nazwa usługi jako string
            str(row.login), #login do konta jako string
            password_bytes, #zaszyfrowane hasło do konta jako bytes
            row.created_at, #data utworzenia wpisu
            row.expire_date, #data wygaśnięcia wpisu (lub None)
        )
    finally: #na koniec
        disconnect(conn) #rozłączenie z bazą danych


def copy_password_to_clipboard(text: str) -> tuple[bool, str]: #kopiuje tekst do schowka systemowego
    """Próbuje skopiować ``text`` do schowka systemowego."""

    def _schedule_clipboard_clear_with_pyperclip(module) -> None: #czyści schowek po 15 sekundach, wstawiając pojedynczą spację
        timer = threading.Timer(15, lambda: module.copy(" "))
        timer.daemon = True
        timer.start()

    def _schedule_clipboard_clear_with_tkinter(module) -> None: #czyści schowek po 15 sekundach, wstawiając pojedynczą spację
        def _clear_clipboard() -> None:
            root = module.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(" ")
            root.update()
            root.destroy()

        timer = threading.Timer(15, _clear_clipboard)
        timer.daemon = True
        timer.start()

    pyperclip_spec = importlib.util.find_spec("pyperclip") #sprawdzenie, czy moduł pyperclip jest dostępny
    if pyperclip_spec is not None: #jeśli moduł pyperclip jest dostępny
        pyperclip = importlib.import_module("pyperclip") #dynamiczne zaimportowanie modułu pyperclip
        try: #próba skopiowania tekstu do schowka
            pyperclip.copy(text) #skopiowanie tekstu do schowka
        except pyperclip.PyperclipException as exc: #w przypadku wystąpienia wyjątku PyperclipException
            return False, f"Nie udało się skopiować hasła: {exc}" #zwrócenie informacji o błędzie
        _schedule_clipboard_clear_with_pyperclip(pyperclip)
        return True, "Hasło skopiowano do schowka." #zwrócenie informacji o sukcesie

    tkinter_spec = importlib.util.find_spec("tkinter") #sprawdzenie, czy moduł tkinter jest dostępny
    if tkinter_spec is not None: #jeśli moduł tkinter jest dostępny
        tkinter = importlib.import_module("tkinter") #dynamiczne zaimportowanie modułu tkinter
        try: #próba skopiowania tekstu do schowka
            root = tkinter.Tk() #utworzenie głównego okna tkinter
            root.withdraw() #ukrycie głównego okna
            root.clipboard_clear() #wyczyszczenie schowka
            root.clipboard_append(text) #dodanie tekstu do schowka
            root.update() #aktualizacja okna tkinter
        except tkinter.TclError as exc: #w przypadku wystąpienia wyjątku TclError
            return False, f"Nie udało się skopiować hasła: {exc}" #zwrócenie informacji o błędzie
        finally: #na koniec
            if "root" in locals(): #jeśli zmienna root istnieje
                root.destroy() #zniszczenie okna tkinter
        _schedule_clipboard_clear_with_tkinter(tkinter)
        return True, "Hasło skopiowano do schowka." #zwrócenie informacji o sukcesie

    return False, "Schowek systemowy jest niedostępny w tym środowisku." #jeśli żaden z modułów nie jest dostępny, zwrócenie informacji o braku schowka


def decrypt_password( # odszyfrowuje haslo uzytkownika
    encrypted_password: bytes | bytearray | memoryview | str, user_secret: str
) -> str:
    if isinstance(encrypted_password, memoryview):
        encrypted_bytes = encrypted_password.tobytes()
    elif isinstance(encrypted_password, bytearray):
        encrypted_bytes = bytes(encrypted_password)
    elif isinstance(encrypted_password, bytes):
        encrypted_bytes = encrypted_password
    else:
        encrypted_bytes = str(encrypted_password).encode("ascii")
    encrypted_token = encrypted_bytes.decode("ascii")
    return decrypt_with_user_secret(encrypted_token, user_secret).decode("utf-8")


def view_or_copy_password( # pozwala na podgląd lub skopiowanie wybranego hasła użytkownika
    user_id: int, #ID użytkownika
    user_secret: str, #sekretny klucz użytkownika do odszyfrowywania haseł
    *,
    config_path: str = "config/db_config.json", #ścieżka do pliku konfiguracyjnego bazy danych
) -> None:
    """Pozwala na podgląd lub skopiowanie wybranego hasła użytkownika."""

    try: #próba pobrania listy wpisów hasła użytkownika
        entries = list_password_entries(user_id=user_id, config_path=config_path) #pobranie listy wpisów hasła użytkownika
    except pyodbc.Error as exc: #w przypadku wystąpienia wyjątku pyodbc.Error
        print(f"\n[!] Błąd podczas pobierania haseł: {exc}.\n") #wyświetlenie informacji o błędzie
        return #zakończenie funkcji

    if not entries: #jeśli lista wpisów jest pusta
        print("\n[-] Brak zapisanych haseł.\n") #wyświetlenie informacji o braku zapisanych haseł
        return #zakończenie funkcji

    print("\nZapisane hasła:") #wyświetlenie nagłówka listy wpisów hasła
    print("-" * 60) #wyświetlenie linii oddzielającej
    print(f"{'ID':<6} {'Usługa':<20} {'Login':<20} {'Wygasa':<12}") #wyświetlenie nagłówków kolumn
    print("-" * 60) #wyświetlenie linii oddzielającej
    for entry_id, service, login, _, expire_date in entries: #iteracja po wpisach hasła użytkownika
        exp_str = expire_date.strftime("%Y-%m-%d") if expire_date else "-" #formatowanie daty wygaśnięcia lub zastąpienie jej myślnikiem, jeśli brak
        print(f"{entry_id:<6} {service:<20} {login:<20} {exp_str:<12}") #wyświetlenie szczegółów wpisu hasła
    print("-" * 60) #wyświetlenie linii oddzielającej
    print() #wyświetlenie pustej linii

    entry_raw = input("Podaj ID wpisu do podglądu: ").strip() #pobranie ID wpisu od użytkownika
    if not entry_raw.isdigit(): #sprawdzenie, czy podane ID jest liczbą
        print("\n[!] Nieprawidłowe ID.\n") #wyświetlenie informacji o nieprawidłowym ID
        return #zakończenie funkcji
    entry_id = int(entry_raw) #konwersja podanego ID na liczbę całkowitą

    try: #próba pobrania wpisu hasła użytkownika o podanym ID
        entry = get_password_entry( # pobranie wpisu hasła użytkownika o podanym ID
            user_id=user_id, #ID użytkownika
            entry_id=entry_id, #ID wpisu hasła
            config_path=config_path, #ścieżka do pliku konfiguracyjnego bazy danych
        )
    except pyodbc.Error as exc: #w przypadku wystąpienia wyjątku pyodbc.Error
        print(f"\n[!] Błąd podczas pobierania hasła: {exc}.\n") #wyświetlenie informacji o błędzie
        return #zakończenie funkcji

    if entry is None: #jeśli wpis o podanym ID nie istnieje
        print("\n[-] Nie znaleziono wpisu o podanym ID.\n") #wyświetlenie informacji o braku wpisu
        return #zakończenie funkcji

    _, service, login, encrypted_password, _, _ = entry #rozpakowanie szczegółów wpisu hasła

    try: #próba odszyfrowania hasła użytkownika
        decrypted_password = decrypt_password( #    odszyfrowanie hasła użytkownika
            encrypted_password, user_secret #zaszyfrowane hasło i sekret użytkownika
        )
    except Exception as exc:#w przypadku wystąpienia wyjątku podczas odszyfrowywania
        print(f"\n[!] Nie udało się odszyfrować hasła: {exc}.\n") #wyświetlenie informacji o błędzie
        return #zakończenie funkcji

    masked_password = "*" * len(decrypted_password) #utworzenie maski hasła za pomocą gwiazdek
    if not masked_password: #jeśli hasło jest puste
        masked_password = "(puste)" #ustawienie maski na "(puste)"

    print("\nSzczegóły wpisu:") #wyświetlenie nagłówka szczegółów wpisu
    print("-" * 40) #wyświetlenie linii oddzielającej
    print(f"Usługa : {service}") #wyświetlenie nazwy usługi
    print(f"Login   : {login}") #wyświetlenie loginu do konta
    print(f"Hasło   : {masked_password}") #wyświetlenie zamaskowanego hasła
    print("-" * 40) #wyświetlenie linii oddzielającej

    while True: #pętla do wyboru działania
        action = input("Wybierz działanie - (P)okaż, (K)opiuj, (W)róć: ").strip().lower() #pobranie wyboru działania od użytkownika
        if action == "p": #jeśli użytkownik wybrał opcję podglądu hasła
            print(f"\nHasło: {decrypted_password}\n") #wyświetlenie odszyfrowanego hasła
        elif action == "k": #jeśli użytkownik wybrał opcję kopiowania hasła
            success, message = copy_password_to_clipboard(decrypted_password) #próba skopiowania hasła do schowka
            prefix = "[+]" if success else "[!]" # ustawienie prefiksu w zależności od sukcesu operacji
            print(f"\n{prefix} {message}\n") #wyświetlenie informacji o wyniku operacji
        elif action == "w": #jeśli użytkownik wybrał opcję powrotu
            break #zakończenie pętli
        else: #jeśli użytkownik wybrał nieprawidłową opcję
            print("\n[!] Nieprawidłowa opcja.\n") #wyświetlenie informacji o nieprawidłowej opcji
