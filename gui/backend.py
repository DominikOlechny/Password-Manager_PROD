"""backend.py - logika backendu GUI aplikacji Password Manager. w tym miejscu wykonywana jest większość operacji związanych z bazą danych i bezpieczeństwem. zawiera klasę Backend, która zarządza stanem aplikacji, sesją użytkownika oraz interakcjami z bazą danych.
Zawiera funkcje i właściwości do:
- Zarządzania sesją użytkownika (logowanie, wylogowywanie).
- Obsługi widoków GUI (przełączanie między ekranami).
- Zarządzania danymi haseł (dodawanie, edytowanie, usuwanie, kopiowanie do schowka).

To ona łącznie z klasą PasswordListModel z gui/models.py zarządza danymi wyświetlanymi w GUI.

dodatkowo wykorzystuje funkcje z modułów db i security do operacji na bazie danych i bezpieczeństwie haseł. kolejno:
- db_connection.py: do zarządzania połączeniami z bazą danych.
- db_creation.py: do tworzenia bazy danych i tabel.
- tablepassword_crud.py: do operacji CRUD na tabeli przechowywania haseł.
- tableusers_insertandverify.py: do zarządzania użytkownikami i weryfikacją.
- security/encrypt.py: do szyfrowania i deszyfrowania danych.
- security/hashing.py: do bezpiecznego haszowania haseł.
- security/password_generator.py: do generowania bezpiecznych haseł.
- gui/models.py: do zarządzania modelami danych używanymi w GUI.
- gui/constants.py: do stałych używanych w GUI.
- gui/helpers.py: do pomocniczych funkcji wspierających logikę backendu.
- config/settings.py: do zarządzania ustawieniami aplikacji, takimi jak klucz szyfrowania.
"""

from pathlib import Path #importowanie modułu Path do obsługi ścieżek plików

import pyodbc #importowanie modułu pyodbc do obsługi połączeń z bazą danych
from PySide6.QtCore import ( #importowanie klas QObject, Property, Signal, Slot z modułu PySide6.QtCore
    QObject,
    Property,
    Signal,
    Slot,
    QTimer,
)

from config import settings #importowanie modułu settings z pakietu config
from db.db_connection import format_server_with_port, split_server_and_port #importowanie funkcji format_server_with_port i split_server_and_port z pliku db_connection.py
from db.db_creation import ensure_database_exists #importowanie funkcji ensure_database_exists z pliku db_creation.py
from db.tablepassword_crud import ( #importowanie funkcji CRUD z pliku tablepassword_crud.py
    add_password_entry, #dodawanie wpisu z hasłem
    copy_password_to_clipboard, #kopiowanie hasła do schowka
    delete_password_entry, #usuwanie wpisu z hasłem
    decrypt_password, #odszyfrowywanie hasła
    get_password_entry, #pobieranie wpisu z hasłem
    list_password_entries, #listowanie wpisów z hasłami
    update_password_entry, #aktualizowanie wpisu z hasłem
)
from db.tableusers_insertandverify import ( #importowanie funkcji zarządzających użytkownikami z pliku tableusers_insertandverify.py
    create_user, #tworzenie użytkownika
    ensure_user_mfa_state, #zapewnienie stanu MFA użytkownika
    get_user_mfa_provisioning, #pobieranie URI provisioning MFA użytkownika
    update_user_credentials, #aktualizowanie danych uwierzytelniających użytkownika
    verify_user, #weryfikacja użytkownika
)
from gui.constants import ( #importowanie stałych z pliku constants.py
    VIEW_CLICK_TO_RUN, 
    VIEW_DATABASE_SETTINGS,
    VIEW_EDIT_USER_ACCOUNT,
    VIEW_KEY_SETTINGS,
    VIEW_LOGIN,
    VIEW_PASSWORD_EDIT,
    VIEW_PASSWORDS_LIST,
)
from gui.helpers import build_password_rows, parse_expire #importowanie funkcji build_password_rows i parse_expire z pliku helpers.py
from gui.models import PasswordListModel #importowanie klasy PasswordListModel z pliku models.py
from security.encrypt import encrypt_with_user_secret #importowanie funkcji encrypt_with_user_secret z pliku encrypt.py
from security.hashing import hash_password #importowanie funkcji hash_password z pliku hashing.py
from security.password_generator import generate_password #importowanie funkcji generate_password z pliku password_generator.py


class Backend(QObject): #klasa Backend dziedzicząca po QObject
    statusMessageChanged = Signal(str) #sygnał zmiany komunikatu statusu
    currentViewChanged = Signal() #sygnał zmiany bieżącego widoku
    editContextChanged = Signal() #sygnał zmiany kontekstu edycji
    mfaSetupChanged = Signal() #sygnał zmiany ustawień MFA

    def __init__(self) -> None: #konstruktor klasy Backend
        super().__init__() #wywołanie konstruktora klasy bazowej QObject
        self._status = "" #inicjalizacja zmiennej status jako pusty ciąg znaków
        self._ui_dir = Path(__file__).resolve().parent.parent / "ui" #ścieżka do katalogu ui
        self._current_view = (self._ui_dir / VIEW_CLICK_TO_RUN).as_uri() #ustawienie bieżącego widoku na widok początkowy
        self.password_model = PasswordListModel() #utworzenie instancji modelu listy haseł
        self._user_id: int | None = None #inicjalizacja zmiennej user_id jako None
        self._user_secret: str | None = None #inicjalizacja zmiennej user_secret jako None
        self._user_login: str | None = None #inicjalizacja zmiennej user_login jako None
        self._edit_entry_id: int | None = None #inicjalizacja zmiennej edit_entry_id jako None
        self._edit_service = "" #inicjalizacja zmiennej edit_service jako pusty ciąg znaków
        self._edit_login = "" #inicjalizacja zmiennej edit_login jako pusty ciąg znaków
        self._edit_password = "" #inicjalizacja zmiennej edit_password jako pusty ciąg znaków
        self._edit_expire = "" #inicjalizacja zmiennej edit_expire jako pusty ciąg znaków
        self._db_driver = "" #inicjalizacja zmiennej db_driver jako pusty ciąg znaków
        self._db_server = "" #inicjalizacja zmiennej db_server jako pusty ciąg znaków
        self._db_database = "" #inicjalizacja zmiennej db_database jako pusty ciąg znaków
        self._db_username = "" #inicjalizacja zmiennej db_username jako pusty ciąg znaków
        self._db_password = "" #inicjalizacja zmiennej db_password jako pusty ciąg znaków
        self._current_key = settings._load_key() or "" #inicjalizacja zmiennej current_key załadowanym kluczem z ustawień lub pustym ciągiem znaków
        self._pending_short_password: tuple[str, str] | None = None #inicjalizacja zmiennej pending_short_password jako None
        self._mfa_secret = "" #inicjalizacja zmiennej mfa_secret jako pusty ciąg znaków
        self._mfa_uri = "" #inicjalizacja zmiennej mfa_uri jako pusty ciąg znaków
        self._session_timer = QTimer(self) #timer do wygaszania sesji użytkownika
        self._session_timer.setInterval(10 * 60 * 1000) #ustawienie interwału na 10 minut
        self._session_timer.setSingleShot(True) #timer jednorazowy
        self._session_timer.timeout.connect(self._handle_session_timeout) #po upływie czasu wywołuje funkcję wygaszającą sesję

#Poniżej właściwości klasy Backend z dekoratorem Property do udostępniania danych do QML i powiązanymi sygnałami zmiany wartości. 

    @Property(str, notify=statusMessageChanged) 
    def statusMessage(self) -> str: # zwraca komunikat statusu  
        return self._status

    @Property(str, notify=currentViewChanged)
    def currentView(self) -> str: # zwraca aktualny widok QML  
        return self._current_view

    @Property(str, notify=editContextChanged)
    def editService(self) -> str: # zwraca nazwe serwisu w edycji  
        return self._edit_service

    @Property(str, notify=editContextChanged)
    def editLogin(self) -> str: # zwraca login w edycji 
        return self._edit_login

    @Property(str, notify=editContextChanged)
    def editPassword(self) -> str: # zwraca haslo w edycji  
        return self._edit_password

    @Property(str, notify=editContextChanged)
    def editExpire(self) -> str: # zwraca date wygasniecia w edycji  
        return self._edit_expire

    @Property(str, notify=editContextChanged)
    def dbDriver(self) -> str: # zwraca sterownik bazy danych  
        return self._db_driver

    @Property(str, notify=editContextChanged)
    def dbServer(self) -> str: # zwraca serwer bazy danych  
        return self._db_server

    @Property(str, notify=editContextChanged)
    def dbDatabase(self) -> str: # zwraca nazwe bazy danych  
        return self._db_database

    @Property(str, notify=editContextChanged)
    def dbUsername(self) -> str: # zwraca login bazy danych  
        return self._db_username

    @Property(str, notify=editContextChanged)
    def dbPassword(self) -> str: # zwraca haslo bazy danych  
        return self._db_password

    @Property(str, notify=editContextChanged)
    def currentKey(self) -> str: # zwraca aktualny klucz aplikacji  
        return self._current_key

    @Property(str, notify=editContextChanged)
    def currentLogin(self) -> str: # zwraca login uzytkownika  
        return self._user_login or ""

    @Property(str, notify=mfaSetupChanged)
    def mfaSecret(self) -> str: # zwraca sekret MFA  
        return self._mfa_secret

    @Property(str, notify=mfaSetupChanged)
    def mfaProvisioningUri(self) -> str: # zwraca URI provisioning MFA  
        return self._mfa_uri

    def _set_status(self, message: str) -> None: # ustawia komunikat statusu
        self._status = message
        self.statusMessageChanged.emit(message)

    def _set_view(self, filename: str) -> None: # ustawia aktualny widok QML
        path = (self._ui_dir / filename).as_uri()
        if path != self._current_view:
            self._current_view = path
            self.currentViewChanged.emit()

    def _handle_session_timeout(self) -> None: #obsługa wygaśnięcia sesji po upływie czasu
        if self._user_id is None: #jeżeli nie ma aktywnej sesji to nic nie rób
            return
        self.logout() #wylogowanie użytkownika
        self._set_status("[i] Sesja wygasła po 10 minutach. Wrócono do menu głównego.") #ustawienie komunikatu o wygaśnięciu sesji

    def _clear_mfa_setup(self) -> None: #wyczyszczenie ustawień MFA
        self._mfa_secret = ""
        self._mfa_uri = ""
        self.mfaSetupChanged.emit()

    @Slot() #slot do czyszczenia ustawień MFA
    def clearMfaSetup(self) -> None: # czysci ustawienia MFA
        self._clear_mfa_setup()

    def _require_session(self) -> bool: #sprawdzenie czy istnieje aktywna sesja użytkownika
        if self._user_id is None or self._user_secret is None: #jeżeli nie to zwróć False i ustaw komunikat statusu
            self._set_status("[!] Brak aktywnej sesji użytkownika.") 
            return False
        return True


    def _refresh_passwords(self) -> None: #odświeżenie listy haseł użytkownika
        if not self._require_session(): # jeżeli nie ma aktywnej sesji to zakończ funkcję
            return
        try: #pobranie listy wpisów z hasłami dla zalogowanego użytkownika
            entries = list_password_entries(user_id=self._user_id) #lista wpisów z hasłami
        except pyodbc.Error as exc:  #komunikat o błędzie w czasie wykonywania
            self._set_status(f"[!] Błąd podczas pobierania haseł: {exc}") # ustawienie komunikatu statusu z informacją o błędzie
            return
        self.password_model.set_entries(build_password_rows(entries)) #ustawienie wpisów w modelu listy haseł

    def _prepare_edit_context( #przygotowanie kontekstu edycji hasła
        self,
        *,
        entry_id: int | None = None,
        service: str = "",
        login: str = "",
        password: str = "",
        expire: str = "",
    ) -> None:
        self._edit_entry_id = entry_id
        self._edit_service = service
        self._edit_login = login
        self._edit_password = password
        self._edit_expire = expire
        self.editContextChanged.emit()

    def _fetch_entry(self, entry_id: int, not_found_message: str, error_label: str): #pobranie wpisu z hasłem
        try:
            entry = get_password_entry(user_id=self._user_id, entry_id=entry_id)
        except pyodbc.Error as exc:  # komunikat o błędzie w czasie wykonywania
            self._set_status(f"[!] {error_label}: {exc}") #ustawienie komunikatu statusu z informacją o błędzie
            return None #zwrócenie None w przypadku błędu
        if entry is None: #jeżeli wpis nie został znaleziony
            self._set_status(not_found_message) #ustawienie komunikatu statusu z informacją o braku wpisu
            return None #zwrócenie None
        return entry #zwrócenie wpisu

    @Slot(str) #slot do wyświetlania komunikatu
    def showMessage(self, message: str) -> None: #wyświetlenie komunikatu
        self._set_status(message) #ustawienie komunikatu statusu

    @Slot(str, str, str) #slot do logowania użytkownika
    def loginUser(self, login: str, password: str, mfa_code: str) -> None: #logowanie użytkownika
        login = login.strip() #usunięcie białych znaków z loginu
        password = password.strip() #usunięcie białych znaków z hasła
        mfa_code = mfa_code.strip() #usunięcie białych znaków z kodu MFA
        if not login or not password: #jeżeli login lub hasło są puste
            self._set_status("[!] Podaj login i hasło.") #ustawienie komunikatu statusu z informacją o braku loginu lub hasła
            return #zakończenie funkcji
        try: #próba weryfikacji użytkownika
            result = verify_user(login=login, password=password, mfa_code=mfa_code) #wynik weryfikacji użytkownika
        except pyodbc.Error as exc:  # komunikat o błędzie w czasie wykonywania
            self._set_status(f"[!] Błąd logowania: {exc}") #ustawienie komunikatu statusu z informacją o błędzie logowania
            return

        if result.status == "locked": #jeżeli konto jest zablokowane
            self._set_status(
                "[!] Konto jest zablokowane. Skontaktuj się z administratorem."
            )
            return #zakończenie funkcji
        if result.status == "mfa_required": #jeżeli wymagany jest kod MFA
            self._set_status("[!] Podaj aktualny kod MFA z aplikacji.") #ustawienie komunikatu statusu z informacją o wymaganym kodzie MFA
            return 
        if result.status == "mfa_invalid": #jeżeli kod MFA jest nieprawidłowy
            self._set_status("[!] Nieprawidłowy kod MFA.") #ustawienie komunikatu statusu z informacją o nieprawidłowym kodzie MFA
            return
        if result.status != "ok" or result.user_id is None or result.login is None: #jeżeli weryfikacja nie powiodła się
            self._set_status("[!] Nieprawidłowy login lub hasło.") #ustawienie komunikatu statusu z informacją o nieprawidłowym loginie lub haśle
            return

        self._user_id, self._user_login = result.user_id, result.login #ustawienie identyfikatora użytkownika i loginu
        self._user_secret = password #ustawienie sekretu użytkownika jako hasła
        self._clear_mfa_setup() #wyczyszczenie ustawień MFA
        self._set_status(f"[+] Zalogowano jako {self._user_login}.") #ustawienie komunikatu statusu z informacją o zalogowaniu
        self._session_timer.start() #uruchomienie timera sesji po zalogowaniu
        self._refresh_passwords() #odświeżenie listy haseł użytkownika
        self.editContextChanged.emit() #emitowanie sygnału zmiany kontekstu edycji
        self._set_view(VIEW_PASSWORDS_LIST) #ustawienie widoku na listę haseł

    @Slot(str, str, str) #slot do rejestracji użytkownika
    def registerUser(self, login: str, password: str, repeat: str) -> None: #rejestracja użytkownika
        login = login.strip() #usunięcie białych znaków z loginu
        password = password.strip() #usunięcie białych znaków z hasła
        repeat = repeat.strip() #usunięcie białych znaków z powtórzonego hasła
        if not login or not password: #jeżeli login lub hasło są puste
            self._pending_short_password = None #wyzerowanie zmiennej pending_short_password
            self._set_status("[!] Podaj login i hasło do rejestracji.") #ustawienie komunikatu statusu z informacją o braku loginu lub hasła
            return #zakończenie funkcji
        if password != repeat: #jeżeli hasła nie są identyczne
            self._pending_short_password = None #wyzerowanie zmiennej pending_short_password
            self._set_status("[!] Hasła nie są identyczne.") #ustawienie komunikatu statusu z informacją o niezgodności haseł
            return 
        if len(password) < 12: #jeżeli hasło jest krótsze niż 12 znaków
            if self._pending_short_password == (login, password): #jeżeli hasło krótkie zostało już potwierdzone
                self._pending_short_password = None #wyzerowanie zmiennej pending_short_password
            else: #jeżeli hasło krótkie nie zostało potwierdzone
                self._pending_short_password = (login, password) #ustawienie zmiennej pending_short_password
                self._set_status( #ustawienie komunikatu statusu z informacją o krótkim haśle
                    "[!] Hasło ma mniej niż 12 znaków. Jeśli chcesz kontynuować, " 
                    "naciśnij ZAREJESTRUJ ponownie."
                )
                return
        else:
            self._pending_short_password = None #wyzerowanie zmiennej pending_short_password
        try: 
            hashed_password = hash_password(password) #zahashowanie hasła
            create_user(login=login, secured_pwd=hashed_password) #utworzenie użytkownika w bazie danych
        except FileNotFoundError: #jeżeli plik z kluczem aplikacji nie został znaleziony
            self._set_status("[!] Brak klucza aplikacji w config/key.json.") #ustawienie komunikatu statusu z informacją o braku klucza aplikacji
            return #zakończenie funkcji
        except pyodbc.IntegrityError: #jeżeli wystąpi błąd integralności bazy danych
            self._set_status("[!] Użytkownik o podanym loginie już istnieje.") #ustawienie komunikatu statusu z informacją o istnieniu użytkownika
            return
        except pyodbc.Error as exc:  # komunikat o błędzie w czasie wykonywania
            self._set_status(f"[!] Błąd podczas rejestracji: {exc}") #ustawienie komunikatu statusu z informacją o błędzie rejestracji
            return #zakończenie funkcji

        self._set_status("[+] Użytkownik został zarejestrowany. Możesz się zalogować.") #ustawienie komunikatu statusu z informacją o pomyślnej rejestracji

    @Slot() #slot do wylogowania użytkownika
    def logout(self) -> None: #wylogowanie użytkownika
        self._session_timer.stop() #zatrzymanie timera sesji
        self._user_id = None #wyzerowanie identyfikatora użytkownika
        self._user_secret = None #wyzerowanie sekretu użytkownika
        self._user_login = None #wyzerowanie loginu użytkownika
        self.password_model.set_entries([]) #wyczyszczenie wpisów w modelu listy haseł
        self._prepare_edit_context() #wyzerowanie kontekstu edycji
        self.editContextChanged.emit() #emitowanie sygnału zmiany kontekstu edycji
        self._clear_mfa_setup() #wyczyszczenie ustawień MFA
        self._set_view(VIEW_LOGIN) #ustawienie widoku na ekran logowania

    @Slot() #slot do otwarcia ustawień bazy danych
    def openDatabaseSettings(self) -> None: #otwarcie ustawień bazy danych
        self._set_status("") #wyzerowanie komunikatu statusu
        config = settings._load_json(settings.DB_CONFIG_PATH, settings.DEFAULT_DB_CONFIG) #załadowanie konfiguracji bazy danych z pliku lub użycie domyślnej konfiguracji
        self._db_driver = str(config.get("driver", "")) #ustawienie sterownika bazy danych
        port = config.get("port") #pobranie portu z konfiguracji
        try:
            port_int = int(port) #konwersja portu na liczbę całkowitą
        except (TypeError, ValueError): #jeżeli konwersja się nie powiedzie
            port_int = None #ustawienie portu jako None
        self._db_server = format_server_with_port(str(config.get("server", "")), port_int) #ustawienie serwera bazy danych z formatowaniem portu
        self._db_database = str(config.get("database", "")) #ustawienie nazwy bazy danych
        self._db_username = str(config.get("username", "")) #ustawienie nazwy użytkownika bazy danych
        self._db_password = str(config.get("password", "")) #ustawienie hasła użytkownika bazy danych
        self.editContextChanged.emit() #emitowanie sygnału zmiany kontekstu edycji
        self._set_view(VIEW_DATABASE_SETTINGS) #ustawienie widoku na ekran ustawień bazy danych

    @Slot(str, str, str, str, str) #slot do zapisywania konfiguracji bazy danych
    def saveDatabaseConfig( # zapisuje konfiguracje bazy 
        self, driver: str, server: str, database: str, username: str, password: str
    ) -> None: #zapisywanie konfiguracji bazy danych
        payload = settings._load_json( #załadowanie istniejącej konfiguracji
            settings.DB_CONFIG_PATH, settings.DEFAULT_DB_CONFIG
        )
        server_value, port_value, warning = split_server_and_port(
            server, payload["server"], payload.get("port") #podział serwera i portu
        )
        payload.update( #aktualizacja konfiguracji bazy danych
            {
                "driver": driver or payload["driver"],
                "server": server_value,
                "port": port_value,
                "database": database or payload["database"],
                "username": username,
                "password": password,
            }
        )
        settings._save_json( #zapisanie konfiguracji bazy danych do pliku
            settings.DB_CONFIG_PATH, payload, backup_prefix="backupdb_config"
        )
        if warning: #jeżeli wystąpiło ostrzeżenie
            self._set_status(warning)
        else: #jeżeli zapis konfiguracji powiódł się
            self._set_status("[+] Zapisano konfigurację bazy danych.")

    @Slot(str, str, str, str, str) #slot do testowania połączenia z bazą danych
    def testDatabaseConnection( # testuje polaczenie z baza 
        self, driver: str, server: str, database: str, username: str, password: str
    ) -> None: #testowanie połączenia z bazą danych
        payload = settings._load_json( #załadowanie istniejącej konfiguracji
            settings.DB_CONFIG_PATH, settings.DEFAULT_DB_CONFIG
        )
        server_value, port_value, warning = split_server_and_port( #podział serwera i portu
            server, payload["server"], payload.get("port") 
        )
        payload.update(
            {
                "driver": driver or payload["driver"],
                "server": server_value,
                "port": port_value,
                "database": database or payload["database"],
                "username": username,
                "password": password,
            }
        )
        try: #próba nawiązania połączenia z bazą danych i utworzenia bazy danych jeżeli nie istnieje
            created = ensure_database_exists(db_name=payload["database"], config=payload) #sprawdzenie i utworzenie bazy danych
            if warning: #jeżeli wystąpiło ostrzeżenie
                self._set_status(warning) #ustawienie komunikatu statusu z ostrzeżeniem
            elif created: #jeżeli baza danych została utworzona
                self._set_status(
                    "[+] Połączenie z bazą powiodło się. Utworzono bazę danych." #ustawienie komunikatu statusu z informacją o utworzeniu bazy danych
                )
            else:
                self._set_status("[+] Połączenie z bazą powiodło się.")
        except Exception as exc:  # bład w czasie wykonywania
            self._set_status(f"[!] Błąd połączenia z bazą: {exc}") #ustawienie komunikatu statusu z informacją o błędzie połączenia

    @Slot() #slot do otwarcia ustawień klucza aplikacji
    def openKeySettings(self) -> None: #otwarcie ustawień klucza aplikacji
        self._current_key = settings._load_key() or "" #załadowanie klucza aplikacji z ustawień
        self._set_view(VIEW_KEY_SETTINGS) #ustawienie widoku na ekran ustawień klucza aplikacji
        self.editContextChanged.emit() #emitowanie sygnału zmiany kontekstu edycji

    @Slot(str) #slot do zapisywania klucza aplikacji
    def saveKey(self, key: str) -> None: #zapisywanie klucza aplikacji
        valid = settings._validate_key(key) #walidacja klucza aplikacji
        if not valid: #jeżeli klucz jest nieprawidłowy
            self._set_status("[!] Nieprawidłowy klucz – użyj Base64 32 bajtów.") 
            return 
        settings._save_json(settings.KEY_PATH, {"key": valid}, backup_prefix="backupkey")
        self._current_key = valid
        self._set_status("[+] Zapisano klucz aplikacji.")
        self.editContextChanged.emit() 

    @Slot() #slot do generowania key.json
    def generateKey(self) -> None: # generowanie kodu
        new_key = settings.generate_key() #generacja
        settings._save_json( #zapis do json
            settings.KEY_PATH, {"key": new_key}, backup_prefix="backupkey"
        )
        self._current_key = new_key
        self._set_status("[+] Wygenerowano nowy klucz aplikacji.")
        self.editContextChanged.emit()

    @Slot() #wylogowanie
    def backToLogin(self) -> None: # wraca do ekranu logowania
        self._set_view(VIEW_LOGIN)

    @Slot() 
    def startApplication(self) -> None: # ustawia widok startowy
        self._set_status("")
        self._set_view(VIEW_LOGIN)

    @Slot()
    def backToPasswords(self) -> None: # wraca do listy hasel
        if self._user_id:
            self._refresh_passwords()
        self._set_view(VIEW_PASSWORDS_LIST)

    @Slot()
    def startEditUserAccount(self) -> None: # otwiera edycje konta
        if not self._require_session():
            return
        self._set_status("")
        self._set_view(VIEW_EDIT_USER_ACCOUNT)

    @Slot()
    def startAddPassword(self) -> None: # przygotowuje dodanie hasla
        if not self._require_session():
            return
        self._prepare_edit_context(entry_id=None, service="", login="", password="", expire="")
        self._set_view(VIEW_PASSWORD_EDIT)

    @Slot(int)
    def startEditPassword(self, entry_id: int) -> None: # przygotowuje edycje hasla
        if not self._require_session():
            return
        entry = self._fetch_entry(
            entry_id, "[!] Nie znaleziono wpisu do edycji.", "Błąd pobierania wpisu"
        )
        if entry is None:
            return
        _, service, login, encrypted_password, _, expire_date = entry
        try:
            decrypted = decrypt_password(encrypted_password, self._user_secret)
        except Exception:  # pragma: no cover - runtime message
            decrypted = ""
        expire_str = expire_date.strftime("%Y-%m-%d") if expire_date else ""
        self._prepare_edit_context(
            entry_id=entry_id,
            service=service or "",
            login=login or "",
            password=decrypted,
            expire=expire_str,
        )
        self._set_view(VIEW_PASSWORD_EDIT)

    @Slot(int)
    def deletePassword(self, entry_id: int) -> None: # usuwa wpis hasla
        if not self._require_session():
            return
        try:
            deleted = delete_password_entry(user_id=self._user_id, entry_id=entry_id)
        except pyodbc.Error as exc:  # pragma: no cover - runtime message
            self._set_status(f"[!] Błąd usuwania wpisu: {exc}")
            return
        if deleted:
            self._set_status("[+] Wpis usunięto.")
            self._refresh_passwords()
        else:
            self._set_status("[!] Nie znaleziono wskazanego wpisu.")

    @Slot(int)
    def revealPassword(self, entry_id: int) -> None: # pokazuje lub ukrywa haslo
        if not self._require_session():
            return
        if self.password_model.is_revealed(entry_id):
            self.password_model.update_password_text(entry_id, "********", False)
            self._set_status("[+] Hasło ukryto.")
            return
        entry = self._fetch_entry(
            entry_id, "[!] Nie znaleziono hasła.", "Błąd pobierania hasła"
        )
        if entry is None:
            return
        encrypted = entry[3]
        try:
            decrypted = decrypt_password(encrypted, self._user_secret)
        except Exception as exc:  # pragma: no cover - runtime message
            self._set_status(f"[!] Nie udało się odszyfrować hasła: {exc}")
            return
        self.password_model.update_password_text(entry_id, decrypted, True)
        self._set_status("[+] Hasło odszyfrowano.")

    @Slot(int)
    def copyPassword(self, entry_id: int) -> None: # kopiuje haslo do schowka
        if not self._require_session():
            return
        entry = self._fetch_entry(
            entry_id, "[!] Nie znaleziono hasła.", "Błąd pobierania hasła"
        )
        if entry is None:
            return
        encrypted = entry[3]
        try:
            decrypted = decrypt_password(encrypted, self._user_secret)
        except Exception as exc:  # pragma: no cover - runtime message
            self._set_status(f"[!] Nie udało się odszyfrować hasła: {exc}")
            return
        success, message = copy_password_to_clipboard(decrypted)
        prefix = "[+]" if success else "[!]"
        self._set_status(f"{prefix} {message}")

    @Slot(str)
    def copyPlainText(self, text: str) -> None: # kopiuje tekst do schowka
        success, message = copy_password_to_clipboard(text)
        prefix = "[+]" if success else "[!]"
        self._set_status(f"{prefix} {message}")

    @Slot(str, str, str, str, str)
    def saveUserAccount( # zapisuje zmiany konta i MFA
        self,
        old_password: str,
        new_password: str,
        confirm_password: str,
        mfa_code: str,
        new_login: str,
    ) -> None:
        if not self._require_session():
            return

        old_password = old_password.strip()
        if not old_password:
            self._set_status("[!] Podaj aktualne hasło.")
            return

        if new_password != confirm_password:
            self._set_status("[!] Nowe hasła nie są identyczne.")
            return

        trimmed_new_pwd = new_password.strip()
        trimmed_login = new_login.strip()
        normalized_mfa = mfa_code.strip()

        try:
            (
                updated_login,
                password_changed,
                login_changed,
            ) = update_user_credentials(
                user_id=self._user_id,
                old_password=old_password,
                new_login=trimmed_login or None,
                new_password=trimmed_new_pwd or None,
            )
        except ValueError as exc:
            self._set_status(f"[!] {exc}")
            return
        except pyodbc.Error as exc:  # pragma: no cover - runtime message
            self._set_status(f"[!] Błąd aktualizacji konta: {exc}")
            return

        self._user_login = updated_login
        if password_changed:
            self._user_secret = trimmed_new_pwd

        try:
            _, mfa_message = ensure_user_mfa_state(
                user_id=self._user_id,
                user_secret=self._user_secret,
                mfa_code=normalized_mfa,
            )
        except ValueError as exc:
            self._set_status(f"[!] {exc}")
            return
        except pyodbc.Error as exc:  # pragma: no cover - runtime message
            self._set_status(f"[!] Błąd aktualizacji MFA: {exc}")
            return

        requires_relogin = password_changed or login_changed
        status_message = "[+] Zaktualizowano dane konta."
        if requires_relogin:
            self.logout()
            status_message = "[+] Zaktualizowano dane konta. Zaloguj się ponownie."
        else:
            self.editContextChanged.emit()
            self._set_view(VIEW_PASSWORDS_LIST)
            self._refresh_passwords()

        if mfa_message:
            status_message = f"{status_message} {mfa_message}"

        self._set_status(status_message)

    @Slot()
    def generateMfaSetup(self) -> None: # generuje dane do konfiguracji MFA
        if not self._require_session():
            return

        try:
            secret, uri, is_enabled = get_user_mfa_provisioning(
                user_id=self._user_id,
                user_secret=self._user_secret,
            )
        except ValueError as exc:
            self._set_status(f"[!] {exc}")
            return
        except pyodbc.Error as exc:  # pragma: no cover - runtime message
            self._set_status(f"[!] Błąd generowania sekretu MFA: {exc}")
            return

        self._mfa_secret = secret
        self._mfa_uri = uri
        self.mfaSetupChanged.emit()

        prefix = "[i]" if is_enabled else "[+]"
        self._set_status(
            f"{prefix} Sekret MFA jest gotowy. Zeskanuj kod QR lub wpisz sekret, a następnie podaj kod z aplikacji."
        )

    @Slot(str, str, str, str)
    def savePassword(self, service: str, login: str, password: str, expire: str) -> None: # zapisuje wpis hasla
        if not self._require_session():
            return
        trimmed_service = service.strip()
        trimmed_login = login.strip()
        if not trimmed_service:
            self._set_status("[!] Pole SERWIS nie może być puste.")
            return
        if not trimmed_login:
            self._set_status("[!] Pole LOGIN nie może być puste.")
            return
        try:
            expire_date = parse_expire(expire)
        except ValueError as exc:
            self._set_status(f"[!] {exc}")
            return
        if expire and expire_date is None:
            return
        encrypted = (
            encrypt_with_user_secret(password, self._user_secret).encode("ascii")
            if password
            else None
        )
        try:
            if self._edit_entry_id is None:
                add_password_entry(
                    user_id=self._user_id,
                    service=trimmed_service,
                    account_login=trimmed_login,
                    account_password=encrypted or b"",
                    expire_date=expire_date,
                )
                self._set_status("[+] Dodano nowe hasło.")
            else:
                updated = update_password_entry(
                    user_id=self._user_id,
                    entry_id=self._edit_entry_id,
                    new_service=trimmed_service,
                    new_login=trimmed_login,
                    new_password=encrypted,
                    new_expire_date=expire_date,
                )
                if updated:
                    self._set_status("[+] Zapisano zmiany hasła.")
                else:
                    self._set_status("[!] Nie znaleziono wpisu do aktualizacji.")
        except Exception as exc:  # pragma: no cover - runtime message
            self._set_status(f"[!] Błąd zapisu hasła: {exc}")
            return
        self._set_view(VIEW_PASSWORDS_LIST)
        self._refresh_passwords()

    @Slot(int, result=str)
    def generatePassword(self, length: int = 16) -> str: # generuje haslo o zadanej dlugosci
        try:
            parsed_length = int(length)
        except (TypeError, ValueError):
            parsed_length = 16

        clamped_length = max(4, min(parsed_length, 128))
        return generate_password(clamped_length) 
