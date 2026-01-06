"""Modele danych GUI aplikacji.
Zawiera klasy:
- PasswordRow: Struktura danych wpisu hasla.
- PasswordListModel: Model listy hasel dla QML.
"""

from dataclasses import dataclass

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


@dataclass
class PasswordRow: # struktura wpisu hasla
    entry_id: int
    service: str
    login: str
    password_text: str = "********"
    revealed: bool = False
    expired: bool = False


class PasswordListModel(QAbstractListModel): # model listy hasel dla QML
    EntryIdRole = Qt.UserRole + 1
    ServiceRole = Qt.UserRole + 2
    LoginRole = Qt.UserRole + 3
    PasswordRole = Qt.UserRole + 4
    RevealedRole = Qt.UserRole + 5
    ExpiredRole = Qt.UserRole + 6

    def __init__(self) -> None: # inicjalizuje model
        super().__init__()
        self._items: list[PasswordRow] = []

    def rowCount(self, parent=QModelIndex()) -> int: # zwraca liczbe wierszy
        if parent.isValid():
            return 0
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole): # zwraca dane dla roli
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        item = self._items[index.row()]
        if role == self.EntryIdRole:
            return item.entry_id
        if role == self.ServiceRole:
            return item.service
        if role == self.LoginRole:
            return item.login
        if role == self.PasswordRole:
            return item.password_text
        if role == self.RevealedRole:
            return item.revealed
        if role == self.ExpiredRole:
            return item.expired
        return None

    def roleNames(self): # mapuje role na nazwy
        return {
            self.EntryIdRole: b"entryId",
            self.ServiceRole: b"service",
            self.LoginRole: b"login",
            self.PasswordRole: b"passwordText",
            self.RevealedRole: b"revealed",
            self.ExpiredRole: b"expired",
        }

    def set_entries(self, entries: list[PasswordRow]) -> None: # ustawia liste wpisow
        self.beginResetModel()
        self._items = list(entries)
        self.endResetModel()

    def is_revealed(self, entry_id: int) -> bool: # sprawdza czy haslo jest ujawnione
        for item in self._items:
            if item.entry_id == entry_id:
                return item.revealed
        return False

    def update_password_text(self, entry_id: int, text: str, revealed: bool) -> None: # aktualizuje tekst i stan ujawnienia
        for row, item in enumerate(self._items):
            if item.entry_id == entry_id:
                item.password_text = text
                item.revealed = revealed
                index = self.index(row, 0)
                self.dataChanged.emit(
                    index, index, [self.PasswordRole, self.RevealedRole]
                )
                break
