from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ToastStack(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.layout.addStretch(1)

    def show_message(self, level: str, text: str, duration: int = 3500) -> None:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setMaximumWidth(430)
        colors = {
            "success": ("#167a55", "#ffffff"),
            "warning": ("#9a6514", "#ffffff"),
            "error": ("#b6293d", "#ffffff"),
            "info": ("#245ea8", "#ffffff"),
        }
        background, foreground = colors.get(level, colors["info"])
        label.setStyleSheet(f"QLabel {{ background:{background}; color:{foreground}; border-radius:8px; padding:10px 14px; font-weight:600; }}")
        self.layout.addWidget(label)
        QTimer.singleShot(duration, lambda: self._remove(label))

    def _remove(self, label: QLabel) -> None:
        self.layout.removeWidget(label)
        label.deleteLater()
