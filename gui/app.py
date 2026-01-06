"""Gui aplikacji Password Manager. tu rozpoczyna się aplikacja GUI.
Zawiera funkcję run_gui, która inicjalizuje aplikację GUI, ustawia kontekst backendu i modeli danych, a następnie ładuje
główny plik QML interfejsu użytkownika.
"""
import sys #import os
from pathlib import Path #importowanie modułu Path do obsługi ścieżek plików

from PySide6.QtGui import QGuiApplication, QIcon #importowanie klasy QGuiApplication z modułu PySide6.QtGui
from PySide6.QtQml import QQmlApplicationEngine #importowanie klasy QQmlApplicationEngine z modułu PySide6.QtQml
from PySide6.QtCore import QUrl #importowanie klasy QUrl z modułu PySide6.QtCore

from gui.backend import Backend #importowanie klasy Backend z pliku gui/backend.py


def run_gui() -> None: #funkcja uruchamiająca aplikację GUI
    app = QGuiApplication(sys.argv) #utworzenie instancji aplikacji GUI
    backend = Backend() #utworzenie instancji backendu aplikacji
    engine = QQmlApplicationEngine() #utworzenie instancji silnika aplikacji QML
    icon_path = _resolve_resource(Path("gui") / "Icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    ctx = engine.rootContext() #pobranie kontekstu głównego silnika QML
    ctx.setContextProperty("backend", backend) #ustawienie właściwości kontekstu o nazwie "backend" na instancję backendu
    ctx.setContextProperty("passwordModel", backend.password_model) #ustawienie właściwości kontekstu o nazwie "passwordModel" na model haseł z backendu
    ctx.setContextProperty(
        "appIconSource",
        QUrl.fromLocalFile(str(icon_path)) if icon_path.exists() else "",
    )
    main_qml = QUrl.fromLocalFile( #ładowanie głównego pliku QML interfejsu użytkownika
        str((Path(__file__).resolve().parent.parent / "ui" / "MainApp.qml")) #ścieżka do pliku MainApp.qml
    )
    engine.load(main_qml) #załadowanie pliku QML do silnika aplikacji
    if not engine.rootObjects(): #sprawdzenie czy załadowano jakieś obiekty QML
        sys.exit(-1) #jeśli nie, zakończenie aplikacji z kodem błędu -1
    sys.exit(app.exec()) #uruchomienie pętli zdarzeń aplikacji i zakończenie aplikacji po jej zamknięciu


def _resolve_resource(relative_path: Path) -> Path:
    """Zwraca ścieżkę do zasobu zarówno w środowisku dev, jak i PyInstaller."""

    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path
