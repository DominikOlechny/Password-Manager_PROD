"""Logika tworzenia tabeli użytkowników.
Sprawdza istnienie tabeli dbo.users, a jeśli nie istnieje, tworzy ją. w tej bazie przechowywani są użytkownicy aplikacji.
Zamieszczono tutaj funkcje kolejno:
- ensure_users_table: Sprawdza istnienie tabeli użytkowników i tworzy ją, jeśli nie istnieje.

Dodatkowo używa funkcji z db_creation.py do zapewnienia istnienia bazy danych.
"""


from .db_connection import connect, disconnect #importowanie funkcji connect i disconnect z pliku db_connection.py
from .db_creation import ensure_database_exists # importowanie funkcji ensure_database_exists z pliku db_creation.py

def ensure_users_table( #upewnij się, że tabela użytkowników istnieje
    db_name: str = "password_manager",
    config_path: str = "config/db_config.json", #ścieżka do pliku konfiguracyjnego bazy danych
) -> bool:
    # 1. Upewnij się, że baza istnieje
    ensure_database_exists(db_name=db_name, config_path=config_path) #upewnij się, że baza danych o podanej nazwie istnieje

    conn = connect(config_path) #nawiązanie połączenia z bazą danych
    try:
        cur = conn.cursor() #utworzenie kursora do wykonywania zapytań SQL

        # 2. Wejdź w kontekst bazy bez parametrów
        escaped = db_name.replace("]", "]]") #ucieczka nawiasów zamykających w nazwie bazy danych
        cur.execute(f"USE [{escaped}]") #wybranie bazy danych o podanej nazwie

        # 3. Sprawdź czy tabela istnieje
        cur.execute("SELECT OBJECT_ID(N'dbo.users', N'U')") #sprawdzenie czy tabela dbo.users istnieje
        exists_before = cur.fetchone()[0] is not None #pobranie wyniku zapytania i sprawdzenie czy tabela istnieje
        if exists_before: #jeśli tabela już istnieje
            return False #zwrócenie False

        # 4. Utwórz tabelę i unikalny indeks na login
        cur.execute("""
CREATE TABLE dbo.users (
    users_id        INT IDENTITY(1,1) PRIMARY KEY,
    login           NVARCHAR(255)   NOT NULL,
    secured_pwd     VARBINARY(MAX)  NOT NULL,
    check_mfa       BIT             NOT NULL CONSTRAINT DF_users_check_mfa DEFAULT(0),
    mfa_secret      VARBINARY(MAX)  NULL,
    is_locked       BIT             NOT NULL CONSTRAINT DF_users_is_locked DEFAULT(0),
    failed_attempts INT             NOT NULL CONSTRAINT DF_users_failed_attempts DEFAULT(0),
    created_at      DATETIME2(0)    NOT NULL CONSTRAINT DF_users_created_at DEFAULT (SYSUTCDATETIME()),
    updated_at      DATETIME2(0)    NOT NULL CONSTRAINT DF_users_updated_at DEFAULT (SYSUTCDATETIME())
);
""")

        # zabezpieczenie przed powtórnym uruchomieniem
        cur.execute("""
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UX_users_login' AND object_id = OBJECT_ID(N'dbo.users')
)
    CREATE UNIQUE INDEX UX_users_login ON dbo.users(login);
""")

        conn.commit()
        return True
    finally:
        disconnect(conn)

"""
def testtabeli(): # testuje tworzenie tabeli users:
    created = ensure_users_table()
    print("Tabela użytkowników została utworzona." if created else "Tabela użytkowników już istnieje.")

testtabeli():
"""