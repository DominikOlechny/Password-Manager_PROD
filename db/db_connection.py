"""Logika połączenia z bazą danych SQL Server. Odczytuje konfigurację z pliku JSON i tworzy połączenie za pomocą pyodbc. Zarówno do użytku w CLI, jak i do integracji z GUI.



Zawiera funkcje do formatowania serwera i portu oraz budowania łańcucha połączenia.
Kolejno:
- split_server_and_port: Rozdziela surowy ciąg serwera na serwer i port.
- format_server_with_port: Formatuje serwer z portem do postaci odpowiedniej dla łańcucha połączenia.
- build_connection_string: Buduje łańcuch połączenia na podstawie konfiguracji.
- connect_with_config: Nawiązuje połączenie z bazą danych na podstawie podanej konfiguracji.
- connect: Nawiązuje połączenie z bazą danych, odczytując konfigurację z pliku JSON.
- disconnect: Zamyka połączenie z bazą danych.  


"""

import json #importowanie modułu json celem odczytania pliku JSON
from pathlib import Path #importowanie modułu Path do obsługi ścieżek

import pyodbc #importowanie modułu pyodbc do obsługi połączeń z bazą danych

def _resolve_config_path(path: str) -> Path: #zamyka względne ścieżki do katalogu głównego aplikacji
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    root_dir = Path(__file__).resolve().parent.parent
    return root_dir / candidate

def split_server_and_port( #logika rozdzielania serwera i portu z surowego ciągu np. "localhost,1433 ----> ("localhost", 1433)
    raw_server: str, default_server: str, default_port: int | None 
) -> tuple[str, int | None, str | None]: 
    server_value = raw_server.strip() or default_server #usuwanie białych znaków i ustawianie domyślnego serwera
    port_value: int | None = default_port #ustawianie domyślnego portu
    warning: str | None = None #inicjalizacja zmiennej ostrzeżenia jako None
    if "," in server_value: #sprawdzanie czy w surowym ciągu znajduje się przecinek
        host_part, port_part = server_value.split(",", 1) #rozdzielanie surowego ciągu na część hosta i portu
        server_value = host_part.strip() or default_server #usuwanie białych znaków z części hosta i ustawianie domyślnego serwera
        port_candidate = port_part.strip() #usuwanie białych znaków z części portu
        if port_candidate: #sprawdzanie czy część portu nie jest pusta
            try:
                port_value = int(port_candidate) #próba konwersji części portu na liczbę całkowitą
            except ValueError:
                warning = "[!] Nieprawidłowy port w adresie serwera – użyto wartości domyślnej."
    return server_value, port_value, warning #zwracanie serwera, portu i ostrzeżenia


def format_server_with_port(server: str, port: int | None) -> str: #formatowanie serwera z portem do postaci odpowiedniej dla łańcucha połączenia
    return f"{server},{port}" if port else server #jeżeli port jest podany to zwróć serwer z portem, w przeciwnym razie zwróć sam serwer


def build_connection_string( # buduje lancuch polaczenia
    config: dict, *, include_database: bool = False
) -> str:
    raw_server = str(config.get("server") or "")
    default_server = raw_server or "localhost"
    server_value, port_value, _ = split_server_and_port(
        raw_server, default_server, config.get("port")
    )
    server = format_server_with_port(server_value, port_value) #Formatowanie serwera z portem
    driver = config.get("driver", "ODBC Driver 18 for SQL Server") #Domyślny sterownik ODBC
    trust = "yes" if config.get("trust_server_certificate", True) else "no" #Ustawienie zaufania do certyfikatu serwera
    encrypt = "yes" if config.get("encrypt", True) else "no" #Ustawienie szyfrowania połączenia
    column_encryption = bool(config.get("column_encryption")) #Always Encrypted (Column Encryption)
    app_name = "PasswordManagerClient" #Nazwa aplikacji - wymagane gdyż SQL Server blokuje bez nazwy aplikacji

    parts = [
        f"DRIVER={{{driver}}}",  #Utworzenie ciagu polaczenia z uzyciem sterownika ODBC
        f"SERVER={server}",  #Utworzenie ciagu polaczenia z serwerem
        f"Encrypt={encrypt}", #Ustawienie szyfrowania
        f"TrustServerCertificate={trust}", #Ustawienie zaufania do certyfikatu serwera
        f"APP={app_name}", #Nazwa aplikacji - wymagane gdyż SQL Server blokuje bez nazwy aplikacji
    ]

    if column_encryption:
        parts.append("ColumnEncryption=Enabled")

    if include_database and config.get("database"):
        parts.append(f"DATABASE={config['database']}")

    if config.get("username"):  #jeżeli podano nazwe uzytkownika i haslo to dodaj je do ciagu polaczenia
        parts += [f"UID={config['username']}", f"PWD={config.get('password', '')}"]
    else:
        parts += ["Trusted_Connection=yes"] #jeżeli nie podano to uzyj polaczenia zaufanego (Windows Authentication)

    return ";".join(parts) #Utworzenie koncowego ciagu polaczenia


def connect_with_config( #Logika połaczenia z baza danych, uzywane dane do polaczenia sa z pliku json config\db_config.json
    config: dict, *, include_database: bool = False
):
    conn_str = build_connection_string(config, include_database=include_database)
    timeout = int(config.get("timeout", 5)) #pobranie timeoutu z pliku konfiguracyjnego lub ustawienie domyślnej wartosci 5 sekund
    return pyodbc.connect(conn_str, timeout=timeout, autocommit=False) #zwrócenie obiektu połączenia z bazą danych


def connect(path: str = "config/db_config.json"): #Logika połaczenia z baza danych, uzywane dane do polaczenia sa z pliku json config\db_config.json
    config_path = _resolve_config_path(path)
    with config_path.open("r", encoding="utf-8") as f:
        c = json.load(f)

    return connect_with_config(c, include_database=True)



def disconnect(conn) -> None: # Logika rozłączania z bazą danych
    if conn: #jeżeli istnieje polaczenie to je zamknij
        try:
            conn.close() #zamkniecie polaczenia z baza danych
        except:
            pass #ignorowanie bledow przy zamykaniu polaczenia

""" pozostawiona logika do testowania bazy danych. 
def testbazy(): # testuje polaczenie z baza:
    conn = None
    try:
        conn = connect()
        print("STATUS: OK")  # połączenie nawiązane
    except Exception as e:
        print("STATUS: FAIL")
        print(f"DETAILS: {e}")
    finally:
        disconnect(conn)

testbazy()
"""
