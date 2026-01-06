Password Manager - Menedzer Hasel Wresja Prod.

Projekt aplikacji desktopowej do bezpiecznego przechowywania hasel w bazie Microsoft SQL Server. Aplikacja udostepnia:
- graficzny interfejs uzytkownika (PySide6/QML),
- uproszczona wersje CLI (obecnie niewspierana, wykorzystywana w poczatkowych testach).

Implementacja zostala wykonana w Pythonie i wykorzystuje mechanizmy kryptograficzne (szyfrowanie AES-256, hashowanie bcrypt) oraz opcjonalne MFA (TOTP), aby ograniczyc ryzyko nieautoryzowanego dostepu do bazy hasel.
Jest ona nieskomplikowana, w przypadku projektu GUI po konfiguracji klucza i połączenia z bazą, nie jest wygane żadne dodatkowe ustawienia.


KLUCZOWE FUNKCJE
- Rejestracja i logowanie uzytkownika (z opcjonalnym MFA).
- Dodawanie, edycja i usuwanie wpisow (serwis, login, haslo).
- Szyfrowanie zapisanych hasel (AES-256) - w bazie przechowywany jest szyfrogram.
- Hashowanie hasla glownego uzytkownika (bcrypt) - w bazie nie jest przechowywane haslo w postaci jawnej.
- Generator hasel (zalezne od implementacji w module security).
- Kopiowanie hasla do schowka (opcjonalnie przez pyperclip).


WYMAGANIA
- Python 3.11+
- Microsoft SQL Server dostepny lokalnie, w LAN lub publicznie
- ODBC Driver 18 for SQL Server (wymagany przez pyodbc)
- Biblioteki Pythona:
  - pyodbc
  - PySide6
  - pyotp (MFA)
  - pyperclip (opcjonalnie)
- Plik .exe (opcjonalnie, zobacz plik exedownload)


STRUKTURA PROJEKTU
- config/ - pliki konfiguracyjne bazy (db_config.json) i materialu kryptograficznego (key.json) oraz narzedzia do ich edycji.
- db/ - polaczenie z baza, tworzenie tabel oraz operacje CRUD na uzytkownikach i wpisach.
- security/ - szyfrowanie/deszyfrowanie, hashowanie, MFA, generator hasel.
- gui/ - backend GUI, modele danych oraz integracja z warstwa QML.
- ui/ - pliki QML (interfejs graficzny).
- main_gui_app.py - punkt wejscia aplikacji GUI.
- main_cli.py - starsza wersja CLI (niewspierana).


BAZA DANYCH
Aplikacja moze automatycznie utworzyc baze danych oraz wymagane tabele (zalezne od uprawnien konta SQL). W ramach testow przygotowano rowniez wariant bazy z podniesionym poziomem zabezpieczen, m.in.:
- osobne konto aplikacyjne o ograniczonych uprawnieniach,
- backupy,
- dodatkowe mechanizmy ochronne po stronie SQL Server (np. Always Encrypted),
- logika blokady konta i automatycznego odblokowania po okreslonym czasie (np. 15 min - jesli skonfigurowano w bazie).

Uwaga:
- Domyslna "surowa" konfiguracja nie wymusza polityk typu Always Encrypted, backup czy granularnych uprawnien.
- Jezeli korzystasz z wlasnej instancji SQL Server, wdrozenie zabezpieczen i ewentualna modyfikacja konfiguracji leza po stronie uzytkownika/administratora.
- Jesli baza jest wystawiona publicznie, rekomendowane jest ograniczenie dostepu sieciowego (firewall, allowlista IP, VPN) oraz wymuszenie szyfrowania polaczenia.


KONFIGURACJA
Aplikacja korzysta z dwoch plikow w katalogu config/:
- db_config.json - parametry polaczenia z MSSQL,
- key.json - material wykorzystywany przez mechanizmy kryptograficzne (np. salt/klucz/parametry wyprowadzania klucza - zgodnie z implementacja).


SWIEZA INSTALACJA
1. Uzupelnij config/db_config.json (z poziomu aplikacji lub recznie).
2. Uruchom aplikacje. Jezeli polaczenie sie powiedzie, aplikacja utworzy wymagane tabele.
3. Konto MSSQL uzyte w konfiguracji musi miec uprawnienia do operacji CRUD na tabelach oraz (jesli aplikacja tworzy baze) prawo do tworzenia bazy/tabel.


ISTNIEJACA INSTALACJA
1. Wskaz istniejaca baze (np. uruchomiona na Dockerze) poprzez db_config.json.
2. key.json:
   - jezeli masz juz zalozone konta i dane, plik key.json musi pozostac zgodny z poprzednia konfiguracja (w przeciwnym razie odczyt danych moze byc niemozliwy),
   - jezeli startujesz od zera, wygeneruj nowy key.json, aby podniesc bezpieczenstwo.
3. Po poprawnej konfiguracji utworz konto lub zaloguj sie.


LOGI I KOPIE ZAPASOWE KONFIGURACJI
- Pliki konfiguracyjne sa automatycznie archiwizowane przed nadpisaniem w katalogu logs/ (np. backup*.json).


HASHOWANIE I SZYFROWANIE - OPIS LOGICZNY
- Haslo glowne uzytkownika jest zabezpieczone poprzez hashowanie (bcrypt). KEY.JSON+Hasło użytkownika
- Dane wpisow (hasla do serwisow) sa przechowywane w bazie w postaci zaszyfrowanej (AES-256). Hasłoużytkownika+Hasłogenerowane.
- Odszyfrowanie nastepuje po stronie aplikacji, po poprawnym uwierzytelnieniu uzytkownika.
- MFA (jesli wlaczone) wykorzystuje mechanizm TOTP.


WSKAZOWKI BEZPIECZENSTWA (OPERACYJNE)
- Chron config/key.json i config/db_config.json - traktuj je jak dane wrazliwe.
- Wymus szyfrowanie polaczenia do SQL Server (np. Encrypt=True) oraz stosuj certyfikat, jezeli srodowisko tego wymaga.
- Ogranicz dostep sieciowy do SQL Server: allowlista IP, VPN lub tunelowanie.
- Publiczne wystawienie portu MSSQL bez dodatkowych warstw ochrony zwieksza ekspozycje na ataki.
- Wlacz MFA dla kont uzytkownikow, aby zredukowac ryzyko przejecia konta po wycieku hasla.
- Stosuj silne hasla glowne.


STATUS PROJEKTU
- GUI: wspierane (glowny tor rozwoju).
- CLI: niewspierane (tylko historycznie do testow).
