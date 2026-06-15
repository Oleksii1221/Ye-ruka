from __future__ import annotations

import configparser
from pathlib import Path

from .config import ConfigManager


def apply_install_preferences(config: ConfigManager, path: Path, first_run: bool) -> bool:
    if not path.is_file():
        return False
    try:
        if not first_run:
            return False
        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")
        language = parser.get("preferences", "language", fallback="uk")
        theme = parser.get("preferences", "theme", fallback="system")
        if language in {"uk", "en"}:
            config.data["language"] = language
        if theme in {"system", "dark", "light"}:
            config.data["theme"] = theme
        config.save()
        return True
    finally:
        path.unlink(missing_ok=True)
