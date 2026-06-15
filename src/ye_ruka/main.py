from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ye_ruka.core.config import ConfigError, ConfigManager
from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.paths import resource_path
from ye_ruka.core.startup import apply_install_preferences
from ye_ruka.resources.theme import ThemeManager
from ye_ruka.ui.main_window import MainWindow


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Є-Рука")
    app.setOrganizationName("Kico")
    app.setApplicationVersion("2.2.1")
    app.setWindowIcon(QIcon(str(resource_path("resources", "icons", "ye-ruka.ico"))))
    config = ConfigManager(resource_path("config", "default_profile.json"))
    first_run = not config.path.exists()
    config_error = ""
    try:
        config.load()
    except ConfigError as exc:
        config_error = str(exc)
    install_dir = Path(sys.executable).resolve().parent
    apply_install_preferences(config, install_dir / "install_preferences.ini", first_run)
    theme = ThemeManager(resource_path("resources", "styles"))
    theme.apply(app, config.data.get("theme", "dark"))
    controller = ApplicationController(config, resource_path("models", "hand_landmarker.task"))
    window = MainWindow(controller, theme)
    window.show()
    if config_error:
        window.toast_stack.show_message("warning", config_error, 7000)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
