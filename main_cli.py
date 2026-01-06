"""Logika interfejsu CLI aplikacji. Cli było na początku tworzenia aplikacji, obecnie nie wspierane jest w 100%.
Zawiera funkcje:
- prompt_credentials(): Pobiera dane logowania z konsoli.
- register_user(): Rejestruje uzytkownika.
- login_user(): Loguje uzytkownika i obsluguje panel.
- show_user_entries(): Wyswietla liste hasel.
- main(): Uruchamia menu glowne CLI.
"""

import sys #importowanie modułu sys do obsługi systemu
from datetime import datetime #importowanie klasy datetime z modułu datetime
from getpass import getpass #importowanie funkcji getpass do bezpiecznego pobierania haseł
from config import settings as app_settings #importowanie narzędzia do zarządzania konfiguracją aplikacji
import pyodbc #importowanie modułu pyodbc do obsługi połączeń z bazą danych

from db.tablepassword_crud import ( #importowanie funkcji CRUD z pliku tablepassword_crud.py
    add_password_entry,
    list_password_entries,
    update_password_entry,
    delete_password_entry,
    view_or_copy_password
)
from db.tableusers_insertandverify import create_user, verify_user #importowanie funkcji create_user i verify_user z pliku tableusers_insertandverify.py
from security.encrypt import encrypt_with_user_secret # importowanie funkcji szyfrujących z pliku security/encrypt.py
from security.hashing import hash_password


def prompt_credentials(*, confirm_password: bool = False) -> tuple[str, str] | None: #funkcja do pobierania danych logowania od użytkownika
    """Zbiera login i hasło od użytkownika w CLI."""
    login = input("Login: ").strip()
    if not login:
        print("\n[!] Login nie może być pusty.\n")
        return None

    password = getpass("Hasło: ")
    if not password:
        print("\n[!] Hasło nie może być puste.\n")
        return None

    if confirm_password:
        repeat = getpass("Powtórz hasło: ")
        if password != repeat:
            print("\n[!] Podane hasła nie są identyczne.\n")
            return None

    return login, password


def register_user() -> None: # rejestruje nowego uzytkownika w bazie
    """Rejestracja nowego użytkownika."""
    credentials = prompt_credentials(confirm_password=True)
    if credentials is None:
        return

    login, password = credentials

    try:
        hashed_password = hash_password(password)
        create_user(login=login, secured_pwd=hashed_password)
    except FileNotFoundError:
        print(
            "\n[!] Brak klucza aplikacji w config/key.json. Skontaktuj się z administratorem.\n"
        )
    except pyodbc.IntegrityError:
        print("\n[!] Użytkownik o podanym loginie już istnieje.\n")
    except pyodbc.Error as exc:
        print(f"\n[!] Błąd podczas rejestracji: {exc}.\n")
    else:
        print("\n[+] Użytkownik został zarejestrowany pomyślnie.\n")


def show_user_entries(user_id: int) -> None: # wyswietla liste hasel uzytkownika
    """Wyświetla listę zapisanych haseł użytkownika."""
    try:
        entries = list_password_entries(user_id=user_id)
    except pyodbc.Error as exc:
        print(f"\n[!] Błąd podczas pobierania haseł: {exc}.\n")
        return

    if not entries:
        print("\n[-] Brak zapisanych haseł.\n")
        return

    print("\nZapisane hasła:")
    print("-" * 60)
    print(f"{'ID':<6} {'Usługa':<20} {'Login':<20} {'Wygasa':<12}")
    print("-" * 60)
    for entry_id, service, login, created_at, expire_date in entries:
        exp_str = expire_date.strftime("%Y-%m-%d") if expire_date else "-"
        print(f"{entry_id:<6} {service:<20} {login:<20} {exp_str:<12}")
    print("-" * 60)
    print()


def login_user() -> None: # loguje uzytkownika i obsluguje panel po zalogowaniu
    """Obsługuje proces logowania użytkownika i panel użytkownika."""
    credentials = prompt_credentials(confirm_password=False)
    if credentials is None:
        return

    login, password = credentials

    try:
        verification = verify_user(login=login, password=password)
    except pyodbc.Error as exc:
        print(f"\n[!] Błąd podczas logowania: {exc}.\n")
        return

    if verification.status == "mfa_required":
        mfa_code = input("Kod MFA: ").strip()
        if not mfa_code:
            print("\n[!] Kod MFA jest wymagany.\n")
            return
        try:
            verification = verify_user(login=login, password=password, mfa_code=mfa_code)
        except pyodbc.Error as exc:
            print(f"\n[!] Błąd podczas weryfikacji MFA: {exc}.\n")
            return

    if verification.status == "locked":
        print("\n[!] Konto jest zablokowane. Skontaktuj się z administratorem.\n")
        return

    if verification.status in {"invalid", "mfa_invalid"} or verification.user_id is None:
        print("\n[!] Nieprawidłowy login, hasło lub kod MFA.\n")
        return

    user_id, user_login = verification.user_id, verification.login or login
    user_secret = password
    print("\n[+] Logowanie zakończone sukcesem.\n")

    while True:
        print("-" * 40)
        print(f"Panel użytkownika: {user_login}")
        print("-" * 40)
        print("1. Dodaj nowe hasło")
        print("2. Wyświetl zapisane hasła")
        print("3. Podgląd lub kopiowanie hasła")
        print("4. Edytuj hasło")
        print("5. Usuń hasło")
        print("Q. Wyloguj")

        choice = input("\nWybierz opcję: ").strip()

        if choice == "1":
            service = input("Nazwa usługi: ").strip()
            if not service:
                print("\n[!] Nazwa usługi nie może być pusta.\n")
                continue

            account_login = input("Login do usługi: ").strip()
            if not account_login:
                print("\n[!] Login do usługi nie może być pusty.\n")
                continue

            account_password = getpass("Hasło do usługi: ")
            if not account_password:
                print("\n[!] Hasło do usługi nie może być puste.\n")
                continue

            expire_raw = input(
                "Data wygaśnięcia (YYYY-MM-DD) [opcjonalnie]: "
            ).strip()
            expire_date = None
            if expire_raw:
                try:
                    expire_date = datetime.strptime(expire_raw, "%Y-%m-%d")
                except ValueError:
                    print("\n[!] Nieprawidłowy format daty. Użyj YYYY-MM-DD.\n")
                    continue

            try:
                encrypted_password = encrypt_with_user_secret(
                    account_password, user_secret
                ).encode("ascii")
                add_password_entry(
                    user_id=user_id,
                    service=service,
                    account_login=account_login,
                    account_password=encrypted_password,
                    expire_date=expire_date,
                )
            except pyodbc.Error as exc:
                print(f"\n[!] Błąd podczas zapisywania hasła: {exc}.\n")
            except ValueError as exc:
                print(f"\n[!] {exc}.\n")
            else:
                print("\n[+] Hasło zostało dodane.\n")

        elif choice == "2":
            show_user_entries(user_id)

        elif choice == "3":
            view_or_copy_password(user_id, user_secret)

        elif choice == "4":
            show_user_entries(user_id)
            entry_raw = input("Podaj ID wpisu do edycji: ").strip()
            if not entry_raw.isdigit():
                print("\n[!] Nieprawidłowe ID.\n")
                continue
            entry_id = int(entry_raw)

            print("\nPodaj nowe wartości lub pozostaw puste aby nie zmieniać.\n")
            new_service = input("Nowa nazwa usługi: ").strip()
            if new_service == "":
                new_service = None

            new_login = input("Nowy login do usługi: ").strip()
            if new_login == "":
                new_login = None

            change_pwd = input("Czy zmienić hasło? [t/N]: ").strip().lower()
            new_password_bytes = None
            if change_pwd == "t":
                new_password = getpass("Nowe hasło do usługi: ")
                if not new_password:
                    print("\n[!] Hasło nie może być puste.\n")
                    continue
                new_password_bytes = encrypt_with_user_secret(
                    new_password, user_secret
                ).encode("ascii")

            expire_raw = input(
                "Nowa data wygaśnięcia (YYYY-MM-DD) [puste - bez zmian]: "
            ).strip()
            new_expire_date = None
            if expire_raw:
                try:
                    new_expire_date = datetime.strptime(expire_raw, "%Y-%m-%d")
                except ValueError:
                    print("\n[!] Nieprawidłowy format daty. Użyj YYYY-MM-DD.\n")
                    continue

            try:
                updated = update_password_entry(
                    user_id=user_id,
                    entry_id=entry_id,
                    new_service=new_service,
                    new_login=new_login,
                    new_password=new_password_bytes,
                    new_expire_date=new_expire_date,
                )
            except pyodbc.Error as exc:
                print(f"\n[!] Błąd podczas edycji hasła: {exc}.\n")
            else:
                if updated:
                    print("\n[+] Wpis został zaktualizowany.\n")
                else:
                    print("\n[-] Nie znaleziono wpisu o podanym ID.\n")

        elif choice == "5":
            show_user_entries(user_id)
            entry_raw = input("Podaj ID wpisu do usunięcia: ").strip()
            if not entry_raw.isdigit():
                print("\n[!] Nieprawidłowe ID.\n")
                continue
            entry_id = int(entry_raw)

            confirm = input(
                "Czy na pewno chcesz usunąć ten wpis? [t/N]: "
            ).strip().lower()
            if confirm != "t":
                print("\n[-] Anulowano usunięcie.\n")
                continue

            try:
                deleted = delete_password_entry(user_id=user_id, entry_id=entry_id)
            except pyodbc.Error as exc:
                print(f"\n[!] Błąd podczas usuwania hasła: {exc}.\n")
            else:
                if deleted:
                    print("\n[+] Wpis został usunięty.\n")
                else:
                    print("\n[-] Nie znaleziono wpisu o podanym ID.\n")

        elif choice.upper() == "Q":
            print("\n[-] Wylogowano użytkownika.\n")
            break

        else:
            print("\n[!] Nieprawidłowa opcja.\n")


def main() -> None: # uruchamia glowne menu CLI
    """Główne menu aplikacji."""
    while True:
        print("-" * 40)
        print("Menedżer haseł - menu główne")
        print("-" * 40)
        print("1. Zaloguj")
        print("2. Zarejestruj nowe konto")
        print("3. Ustawienia aplikacji")
        print("Q. Zakończ")

        choice = input("\nWybierz opcję: ").strip()

        if choice == "1":
            login_user()
        elif choice == "2":
            register_user()
        elif choice == "3":
            app_settings.configure_application()
        elif choice.upper() == "Q":
            print("\n[-] Zamykanie aplikacji.\n")
            break
        else:
            print("\n[!] Nieprawidłowa opcja.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[-] Przerwano przez użytkownika.\n")
        sys.exit(1)
