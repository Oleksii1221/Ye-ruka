from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class ThemeManager:
    def __init__(self, styles_dir: Path) -> None:
        self.styles_dir = styles_dir
        self.current = "dark"

    def apply(self, app: QApplication, theme: str) -> None:
        selected = theme
        if theme == "system":
            theme = self._system_theme(app)
        path = self.styles_dir / f"{theme}.qss"
        if not path.exists():
            path = self.styles_dir / "dark.qss"
            theme = "dark"
        palette = QPalette()
        if theme == "light":
            palette.setColor(QPalette.ColorRole.Window, QColor("#EEF2F8"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#182235"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F3F6FB"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#182235"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#273246"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#725BFF"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#7A879B"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#13B8D4"))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor("#080B12"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#EAF0FA"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#0D1320"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#121A29"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#EAF0FA"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#202A3D"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#EAF0FA"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#725BFF"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#77849A"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#22D3EE"))
        app.setPalette(palette)
        app.setStyleSheet(path.read_text(encoding="utf-8"))
        self.current = selected

    @staticmethod
    def _system_theme(app: QApplication) -> str:
        if sys.platform == "win32":
            try:
                import winreg

                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                ) as key:
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    return "light" if value else "dark"
            except OSError:
                pass
        return "dark" if app.palette().window().color().lightness() < 128 else "light"
