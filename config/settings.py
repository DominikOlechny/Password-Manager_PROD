"""Logika konfiguracji aplikacji. Odpowiada za edycję plików config/db_config.json i config/key.json, tworzenie kopii zapasowych oraz interaktywny interfejs użytkownika. Zarówno do użytku w CLI, jak i do integracji z GUI.

Pliki konfiguracyjne są przechowywane w katalogu 'config' w katalogu głównym aplikacji. W formacie JSON.
Kolejno:
- db_config.json: Ustawienia połączenia z bazą danych.
- key.json: Klucz szyfrowania w formacie Base64 (32 bajty).

kopie zapasowe istniejących plików konfiguracyjnych są tworzone w katalogu 'logs' z prefiksem 'backup' i znacznikiem czasu.

Zawiera funkcje:
- edit_db_config(): Interaktywnie edytuje plik config/db_config.json.
- edit_key_file(): Interaktywnie edytuje plik config/key.json.
- configure_application(): Uruchamia interfejs ustawień i obsługuje przerwanie użytkownika.
- main(): Główna pętla interfejsu użytkownika ustawień.
- generate_key(): Generuje losowy klucz Base64 o długości 32 bajtów.
- _load_json(): Wczytuje plik JSON z domyślnymi wartościami.
- _save_json(): Zapisuje dane do pliku JSON z opcjonalną kopią zapasową.
- _prompt_value(): Pomaga w interaktywnym pobieraniu wartości od użytkownika.
- _prompt_bool(): Pomaga w interaktywnym pobieraniu wartości boolean od użytkownika.
- _prompt_secret(): Pomaga w interaktywnym pobieraniu poufnych wartości od użytkownika.
- _load_key(): Wczytuje istniejący klucz z pliku config/key.json.
- _validate_key(): Waliduje klucz Base64 o długości 32 bajtów.
- _get_root_dir(): Określa katalog główny aplikacji, obsługując zarówno środowiska skompilowane, jak i nieskompilowane.
- _ensure_log_dir(): Tworzy katalog 'logs', jeśli nie istnieje.
- _backup_existing_file(): Tworzy kopię zapasową istniejącego pliku konfiguracyjnego w katalogu 'logs'.
- DEFAULT_DB_CONFIG: Domyślne ustawienia bazy danych.
- ROOT_DIR, CONFIG_DIR, LOG_DIR, DB_CONFIG_PATH, KEY_PATH: Ścieżki do odpowiednich katalogów i plików konfiguracyjnych.
"""

import base64 # do kodowania i dekodowania Base64
import binascii # do obsługi błędów kodowania Base64
import json # do operacji na plikach JSON
import secrets # do generowania bezpiecznych losowych kluczy
import sys # do określania katalogu głównego aplikacji
from datetime import datetime # do znaczników czasu kopii zapasowych
from getpass import getpass # do bezpiecznego pobierania poufnych danych wejściowych
from pathlib import Path # do operacji na ścieżkach plików
from typing import Any # do adnotacji typów

def _get_root_dir() -> Path: # określa katalog główny aplikacji
    if getattr(sys, "frozen", False): # obsługuje środowiska skompilowane
        return Path(sys.executable).resolve().parent # katalog główny to katalog z plikiem wykonywalnym
    return Path(__file__).resolve().parent.parent # w środowiskach nieskompilowanych to dwa poziomy wyżej od bieżącego pliku


ROOT_DIR = _get_root_dir() # katalog główny aplikacji
CONFIG_DIR = ROOT_DIR / "config" # katalog konfiguracyjny
LOG_DIR = ROOT_DIR / "logs" # katalog logów i kopii zapasowych
DB_CONFIG_PATH = CONFIG_DIR / "db_config.json" # ścieżka do pliku konfiguracyjnego bazy danych
KEY_PATH = CONFIG_DIR / "key.json" # ścieżka do pliku klucza szyfrowania

DEFAULT_DB_CONFIG: dict[str, Any] = { # domyślne ustawienia bazy danych
    "engine": "mssql", # silnik bazy danych
    "driver": "ODBC Driver 18 for SQL Server", # sterownik ODBC
    "server": "localhost", # adres serwera
    "port": 1433, # port serwera
    "database": "password_manager", # nazwa bazy danych
    "username": "", # nazwa użytkownika (pusta dla Trusted Connection)
    "password": "", # hasło użytkownika
    "encrypt": False, # szyfruj połączenie
    "column_encryption": False, # Always Encrypted (Column Encryption)
    "trust_server_certificate": True, # zaufaj certyfikatowi serwera
    "timeout": 5, # timeout połączenia w sekundach
}


def _load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]: # wczytuje plik JSON z domyślnymi wartościami
    if path.exists(): # jeśli plik istnieje
        try: # wczytaj dane z pliku
            data = json.loads(path.read_text(encoding="utf-8")) # wczytuje zawartość pliku jako JSON
        except json.JSONDecodeError: # obsługuje błędy dekodowania JSON
            print(f"[!] Nieprawidłowy format JSON w pliku {path}.") # informuje o błędzie
            data = {} # ustawia puste dane w przypadku błędu
        return {**default, **data} # łączy domyślne wartości z wczytanymi danymi
    return default.copy() # zwraca kopię domyślnych wartości, jeśli plik nie istnieje


def _ensure_log_dir() -> None: # tworzy katalog 'logs', jeśli nie istnieje
    LOG_DIR.mkdir(exist_ok=True) # tworzy katalog logów, jeśli nie istnieje


def _backup_existing_file(path: Path, prefix: str) -> None: # tworzy kopię zapasową istniejącego pliku konfiguracyjnego w katalogu 'logs'
    if not path.exists(): # jeśli plik nie istnieje
        return
    try: # wczytaj zawartość pliku
        content = path.read_text(encoding="utf-8") # wczytuje zawartość pliku
    except OSError as exc: # obsługuje błędy odczytu pliku
        print(f"[!] Nie udało się utworzyć kopii zapasowej {path}: {exc}")
        return

    _ensure_log_dir() # upewnia się, że katalog logów istnieje
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S") # tworzy znacznik czasu
    backup_path = LOG_DIR / f"{prefix}{timestamp}.json" # tworzy ścieżkę do pliku kopii zapasowej
    backup_path.write_text(content, encoding="utf-8") # zapisuje zawartość do pliku kopii zapasowej
    print(f"[+] Utworzono kopię zapasową: {backup_path}") # informuje o utworzeniu kopii zapasowej


def _save_json(path: Path, payload: dict[str, Any], backup_prefix: str | None = None) -> None: # zapisuje dane do pliku JSON z opcjonalną kopią zapasową
    if backup_prefix: # jeśli podano prefiks kopii zapasowej
        _backup_existing_file(path, backup_prefix) # tworzy kopię zapasową istniejącego pliku
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8") # zapisuje dane do pliku JSON
    print(f"\n[+] Zapisano zmiany w {path}.") # informuje o zapisaniu zmian


def _prompt_value(prompt: str, current: Any, caster, allow_blank: bool = True) -> Any: # pomaga w interaktywnym pobieraniu wartości od użytkownika
    while True: # pętla do pobierania wartości
        raw = input(f"{prompt} [{current!r}]: ").strip() # pobiera wartość od użytkownika
        if not raw: # jeśli wartość jest pusta
            if allow_blank: # jeśli puste wartości są dozwolone
                return current # zwraca aktualną wartość
            print("[!] Wartość nie może być pusta.")
            continue # ponawia pętlę
        try: # próbuje przekonwertować wartość
            return caster(raw) # zwraca przekonwertowaną wartość
        except ValueError: # obsługuje błędy konwersji
            print("[!] Nieprawidłowa wartość, spróbuj ponownie.") # informuje o błędzie


def _prompt_bool(prompt: str, current: bool) -> bool: # pomaga w interaktywnym pobieraniu wartości boolean od użytkownika
    mapping = {"t": True, "tak": True, "y": True, "yes": True, "n": False, "no": False, "nie": False} # mapowanie odpowiedzi użytkownika na wartości boolean
    while True: # pętla do pobierania wartości
        raw = input(f"{prompt} [aktualnie {'TAK' if current else 'NIE'}]: ").strip().lower() # pobiera wartość od użytkownika
        if not raw: # jeśli wartość jest pusta
            return current # zwraca aktualną wartość
        if raw in mapping: # jeśli wartość jest w mapowaniu
            return mapping[raw] # zwraca odpowiadającą wartość boolean
        print("[!] Wpisz tak/t lub nie/n.") # informuje o błędzie


def _prompt_secret(prompt: str, current: str) -> str: # pomaga w interaktywnym pobieraniu poufnych wartości od użytkownika
    raw = getpass(f"{prompt} (pozostaw puste aby nie zmieniać): ") # pobiera poufną wartość od użytkownika
    return current if not raw else raw # zwraca aktualną wartość, jeśli wejście jest puste, w przeciwnym razie zwraca nowe wejście


def edit_db_config() -> None: # interaktywnie edytuje plik config/db_config.json
    print("\n--- Edycja config/db_config.json ---") # nagłówek sekcji edycji konfiguracji bazy danych
    config = _load_json(DB_CONFIG_PATH, DEFAULT_DB_CONFIG) # wczytuje istniejącą konfigurację lub używa domyślnych wartości
# interaktywnie pobiera nowe wartości od użytkownika
    config["engine"] = _prompt_value("Silnik bazy danych", config["engine"], str) 
    config["driver"] = _prompt_value("Sterownik ODBC", config["driver"], str) 
    config["server"] = _prompt_value("Adres serwera", config["server"], str) 
    config["port"] = _prompt_value("Port", config["port"], int)
    config["database"] = _prompt_value("Nazwa bazy danych", config["database"], str)
    config["username"] = _prompt_value("Login SQL (pozostaw puste dla Trusted Connection)", config["username"], str)
    config["password"] = _prompt_secret("Hasło SQL", config["password"])
    config["trust_server_certificate"] = _prompt_bool("Zaufaj certyfikatowi serwera", config["trust_server_certificate"])
    config["timeout"] = _prompt_value("Timeout (s)", config["timeout"], int)

    _save_json(DB_CONFIG_PATH, config, backup_prefix="backupdb_config") # zapisuje zmienioną konfigurację z kopią zapasową


def _load_key() -> str | None: # wczytuje istniejący klucz z pliku config/key.json
    if not KEY_PATH.exists(): # jeśli plik nie istnieje
        return None
    try: # wczytaj dane z pliku
        data = json.loads(KEY_PATH.read_text(encoding="utf-8")) # wczytuje zawartość pliku jako JSON
        return data.get("key") # zwraca klucz z danych
    except (json.JSONDecodeError, AttributeError): # obsługuje błędy dekodowania JSON i brak klucza
        print("[!] Nie można odczytać istniejącego klucza – zostanie nadpisany.") # informuje o błędzie
        return None # zwraca None w przypadku błędu


def _validate_key(raw: str) -> str | None: # waliduje klucz Base64 o długości 32 bajtów
    try:
        decoded = base64.b64decode(raw, validate=True)
    except binascii.Error: # obsługuje błędy dekodowania Base64
        return None # zwraca None, jeśli dekodowanie się nie powiodło
    return raw if len(decoded) == 32 else None # zwraca klucz, jeśli ma 32 bajty, w przeciwnym razie None


def generate_key() -> str: # generuje losowy klucz Base64 o długości 32 bajtów
    return base64.b64encode(secrets.token_bytes(32)).decode("ascii") # generuje i koduje klucz


def edit_key_file() -> None: # interaktywnie edytuje plik config/key.json
    print("\n--- Edycja config/key.json ---") # nagłówek sekcji edycji klucza
    current = _load_key() # wczytuje istniejący klucz
    if current:
        print(f"Aktualny klucz: {current}") # wyświetla aktualny klucz
    else:
        print("Aktualny klucz: <brak>") # informuje, że klucz nie istnieje

    while True: # pętla do edycji klucza
        print("\n1. Wprowadź własny klucz Base64 (32 bajty)")
        print("2. Wygeneruj losowy klucz")
        print("Q. Powrót")
        choice = input("Wybierz opcję: ").strip().lower()

        if choice == "1":
            candidate = input("Podaj klucz: ").strip()
            if not candidate:
                print("[!] Klucz nie może być pusty.")
                continue
            valid = _validate_key(candidate) # waliduje podany klucz
            if not valid:
                print("[!] Nieprawidłowy klucz – upewnij się, że to Base64 32 bajtów.")
                continue
            _save_json(KEY_PATH, {"key": valid}, backup_prefix="backupkey")
            break
        elif choice == "2": # generuje nowy klucz
            print("[!] Uwaga: zmiana klucza może uniemożliwić logowanie do bazy danych.")
            confirm = input("Czy na pewno wygenerować nowy klucz? (t/N): ").strip().lower()
            if confirm not in {"t", "tak", "y", "yes"}:
                print("Anulowano generowanie nowego klucza.")
                continue
            new_key = generate_key() # generuje nowy klucz
            _save_json(KEY_PATH, {"key": new_key}, backup_prefix="backupkey")
            print(f"Nowy klucz: {new_key}")
            break
        elif choice == "q":
            print("Przerwano edycję klucza.")
            break
        else:
            print("[!] Nieznana opcja.")


def main() -> None: # główna pętla interfejsu użytkownika ustawień W CLI
    while True:
        print("\n===== Ustawienia aplikacji =====")
        print("1. Edytuj config/db_config.json")
        print("2. Edytuj config/key.json")
        print("Q. Zakończ")

        choice = input("Wybierz opcję: ").strip().lower()
        if choice == "1":
            edit_db_config()
        elif choice == "2":
            edit_key_file()
        elif choice == "q":
            print("Do zobaczenia!")
            break
        else:
            print("[!] Nieznana opcja, spróbuj ponownie.")


def configure_application() -> None: # uruchamia interfejs ustawien 
    """Uruchamia interfejs ustawień i obsługuje przerwanie użytkownika."""
    try:
        main()
    except KeyboardInterrupt:
        print("\n[-] Przerwano edycję ustawień.\n")


if __name__ == "__main__": # uruchamia konfigurację aplikacji
    configure_application()
