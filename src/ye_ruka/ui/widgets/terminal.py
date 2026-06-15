from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QDialog, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget


class SerialTerminalDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Serial Terminal")
        self.resize(820, 460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("TerminalOutput")
        layout.addWidget(self.output, 1)

        row = QHBoxLayout()
        row.addStretch(1)
        self.clear_button = QPushButton("Очистити")
        self.close_button = QPushButton("Закрити")
        row.addWidget(self.clear_button)
        row.addWidget(self.close_button)
        layout.addLayout(row)

        self.clear_button.clicked.connect(self.output.clear)
        self.close_button.clicked.connect(self.hide)

    def append_log(self, text: str) -> None:
        self.output.appendPlainText(f"[{datetime.now():%H:%M:%S}] {text}")
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def toggle_visible(self) -> None:
        if self.isVisible():
            self.hide()
            return
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
