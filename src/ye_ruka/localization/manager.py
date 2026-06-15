from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal


class LocalizationManager(QObject):
    changed = Signal(str)

    def __init__(self, translations_dir: Path, language: str = "uk") -> None:
        super().__init__()
        self.translations_dir = translations_dir
        self.language = language
        self.messages: dict[str, str] = {}
        self.set_language(language, emit=False)

    def set_language(self, language: str, emit: bool = True) -> None:
        path = self.translations_dir / f"{language}.json"
        if not path.exists():
            language = "uk"
            path = self.translations_dir / "uk.json"
        self.language = language
        self.messages = json.loads(path.read_text(encoding="utf-8"))
        if emit:
            self.changed.emit(language)

    def tr(self, key: str, fallback: str = "") -> str:
        return self.messages.get(key, fallback or key)
