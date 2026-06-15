from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

from PySide6.QtCore import QProcess, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.paths import project_root, resource_path
from ye_ruka.ui.widgets.common import card, subtitle_label, title_label


BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 1000000, 2000000)
FIELD_MIN_HEIGHT = 44
TABLE_ROW_HEIGHT = 46


class SettingsPage(QWidget):
    theme_changed = Signal(str)
    language_changed = Signal(str)

    def __init__(self, controller: ApplicationController) -> None:
        super().__init__()
        self.controller = controller
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(14)
        root.addWidget(title_label("Налаштування"))
        root.addWidget(subtitle_label("Профіль, джерела даних, безпека, інтерфейс та параметри протоколів"))
        self.tabs = QTabWidget()
        self.tabs.setObjectName("SettingsTabs")
        root.addWidget(self.tabs, 1)
        self.tabs.addTab(self._scrollable(self._general_tab()), "Загальні")
        self.tabs.addTab(self._scrollable(self._camera_tab()), "Камера")
        self.tabs.addTab(self._scrollable(self._serial_tab()), "Кисть / Serial")
        self.tabs.addTab(self._scrollable(self._glove_tab()), "Рукавиця")
        self.tabs.addTab(self._scrollable(self._tracking_tab()), "Відстеження")
        self.tabs.addTab(self._scrollable(self._safety_tab()), "Безпека")
        self.tabs.addTab(self._scrollable(self._about_tab()), "Про програму")
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.import_button = QPushButton("Імпорт профілю")
        self.export_button = QPushButton("Експорт профілю")
        self.reset_button = QPushButton("Скинути")
        self.save_button = QPushButton("Зберегти зміни")
        self.save_button.setProperty("accent", True)
        buttons.addWidget(self.import_button)
        buttons.addWidget(self.export_button)
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.save_button)
        root.addLayout(buttons)
        self.save_button.clicked.connect(self.save)
        self.export_button.clicked.connect(self.export_profile)
        self.import_button.clicked.connect(self.import_profile)
        self.reset_button.clicked.connect(self.reset_profile)
        self._normalize_field_metrics()

    def _general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        frame, content = card(name="SettingsSurface")
        form = QFormLayout()
        self._tune_form(form)
        self.profile_name = QLineEdit(self.controller.data.get("profile_name", ""))
        self.theme = QComboBox()
        self.theme.addItem("Системна", "system")
        self.theme.addItem("Темна", "dark")
        self.theme.addItem("Світла", "light")
        self.theme.setCurrentIndex(max(0, self.theme.findData(self.controller.data.get("theme", "dark"))))
        self.language = QComboBox()
        self.language.addItem("Українська", "uk")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(max(0, self.language.findData(self.controller.data.get("language", "uk"))))
        form.addRow("Назва профілю", self.profile_name)
        form.addRow("Тема", self.theme)
        form.addRow("Мова", self.language)
        content.addLayout(form)
        layout.addWidget(frame)
        layout.addStretch(1)
        return widget

    @staticmethod
    def _scrollable(widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(widget)
        return scroll

    def _camera_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        frame, content = card(name="SettingsSurface")
        form = QFormLayout()
        self._tune_form(form)
        cfg = self.controller.data["camera"]
        self.camera_index = QSpinBox()
        self.camera_index.setRange(0, 32)
        self.camera_index.setValue(int(cfg.get("index", 0)))
        self.camera_resolution = QComboBox()
        self.camera_resolution.addItems(["640×480", "1280×720", "1920×1080"])
        self.camera_resolution.setCurrentText(f"{cfg.get('width', 1280)}×{cfg.get('height', 720)}")
        self.camera_fps = QSpinBox()
        self.camera_fps.setRange(5, 120)
        self.camera_fps.setValue(int(cfg.get("fps", 30)))
        self.camera_mirror = QCheckBox()
        self.camera_mirror.setChecked(bool(cfg.get("mirror", True)))
        self.hand = QComboBox()
        self.hand.addItem("Автоматично", "auto")
        self.hand.addItem("Ліва", "left")
        self.hand.addItem("Права", "right")
        self.hand.setCurrentIndex(max(0, self.hand.findData(cfg.get("hand_preference", "auto"))))
        form.addRow("Індекс камери", self.camera_index)
        form.addRow("Роздільна здатність", self.camera_resolution)
        form.addRow("FPS", self.camera_fps)
        form.addRow("Дзеркально", self.camera_mirror)
        form.addRow("Рука", self.hand)
        content.addLayout(form)
        layout.addWidget(frame)
        layout.addStretch(1)
        return widget

    def _serial_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        frame, content = card(name="SettingsSurface")
        form = QFormLayout()
        self._tune_form(form)
        cfg = self.controller.data["serial"]
        port_row = QHBoxLayout()
        self.port = QComboBox()
        self.refresh_ports = QPushButton("Оновити")
        port_row.addWidget(self.port, 1)
        port_row.addWidget(self.refresh_ports)
        self.baud = QComboBox()
        for value in BAUDRATES:
            self.baud.addItem(str(value), value)
        self.baud.setCurrentIndex(max(0, self.baud.findData(int(cfg.get("baudrate", 115200)))))
        self.protocol = QComboBox()
        self.protocol.addItem("Захищений YR1 + CRC16", "extended")
        self.protocol.addItem("Простий масив", "simple")
        self.protocol.setCurrentIndex(max(0, self.protocol.findData(cfg.get("protocol", "extended"))))
        self.rate = QSpinBox()
        self.rate.setRange(1, 200)
        self.rate.setValue(int(cfg.get("send_rate_hz", 60)))
        self.rate.setSuffix(" Гц")
        self.auto_reconnect = QCheckBox()
        self.auto_reconnect.setChecked(bool(cfg.get("auto_reconnect", True)))
        self.ack = QCheckBox()
        self.ack.setChecked(bool(cfg.get("ack_enabled", False)))
        form.addRow("COM-порт кисті", port_row)
        form.addRow("Швидкість", self.baud)
        form.addRow("Протокол", self.protocol)
        form.addRow("Частота", self.rate)
        form.addRow("Автоперепідключення", self.auto_reconnect)
        form.addRow("ACK", self.ack)
        content.addLayout(form)
        layout.addWidget(frame)
        layout.addStretch(1)
        self.refresh_ports.clicked.connect(self.scan_ports)
        self.scan_ports()
        return widget

    def _glove_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        general, general_layout = card(name="SettingsSurface")
        form = QFormLayout()
        self._tune_form(form)
        cfg = self.controller.data["glove"]
        self.glove_port = QComboBox()
        self.glove_baud = QComboBox()
        for value in BAUDRATES:
            self.glove_baud.addItem(str(value), value)
        self.glove_baud.setCurrentIndex(max(0, self.glove_baud.findData(int(cfg.get("baudrate", 115200)))))
        self.glove_format = QComboBox()
        self.glove_format.addItem("Автовизначення", "auto")
        self.glove_format.addItem("Масив [1,2,3]", "array")
        self.glove_format.addItem("CSV 1,2,3", "csv")
        self.glove_format.addItem("Префіксований", "prefixed")
        self.glove_format.setCurrentIndex(max(0, self.glove_format.findData(cfg.get("format", "auto"))))
        self.glove_channels = QSpinBox()
        self.glove_channels.setRange(1, 32)
        self.glove_channels.setValue(int(cfg.get("channel_count", len(self.controller.axes))))
        self.glove_input_min = QDoubleSpinBox()
        self.glove_input_min.setRange(-1000000, 1000000)
        self.glove_input_min.setValue(float(cfg.get("input_min", 0.0)))
        self.glove_input_max = QDoubleSpinBox()
        self.glove_input_max.setRange(-1000000, 1000000)
        self.glove_input_max.setValue(float(cfg.get("input_max", 4095.0)))
        self.glove_smoothing = QDoubleSpinBox()
        self.glove_smoothing.setRange(0.0, 0.98)
        self.glove_smoothing.setSingleStep(0.01)
        self.glove_smoothing.setValue(float(cfg.get("smoothing", 0.22)))
        self.glove_auto_reconnect = QCheckBox()
        self.glove_auto_reconnect.setChecked(bool(cfg.get("auto_reconnect", True)))
        form.addRow("COM-порт рукавиці", self.glove_port)
        form.addRow("Швидкість", self.glove_baud)
        form.addRow("Формат RX", self.glove_format)
        form.addRow("Кількість каналів", self.glove_channels)
        form.addRow("Глобальний мінімум", self.glove_input_min)
        form.addRow("Глобальний максимум", self.glove_input_max)
        form.addRow("Згладжування візуалізації", self.glove_smoothing)
        form.addRow("Автоперепідключення", self.glove_auto_reconnect)
        general_layout.addLayout(form)
        layout.addWidget(general)

        mapping, mapping_layout = card(name="SettingsSurface")
        mapping_layout.addWidget(QLabel("Відповідність каналів рукавиці осям кисті"))
        note = QLabel("Для кожної осі можна задати окремий канал датчика, діапазон та інверсію.")
        note.setObjectName("MicroText")
        mapping_layout.addWidget(note)
        self.glove_mapping = QTableWidget(len(self.controller.axes), 5)
        self.glove_mapping.setHorizontalHeaderLabels(["Вісь", "Канал", "Min", "Max", "Inv"])
        self.glove_mapping.verticalHeader().setVisible(False)
        self.glove_mapping.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        self.glove_mapping.horizontalHeader().setStretchLastSection(True)
        self.glove_mapping.setMinimumHeight(190)
        for row, axis in enumerate(self.controller.axes):
            self.glove_mapping.setRowHeight(row, TABLE_ROW_HEIGHT)
            name = QTableWidgetItem(axis.name(self.controller.data.get("language", "uk")))
            name.setData(Qt.ItemDataRole.UserRole, axis.id)
            name.setFlags(name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.glove_mapping.setItem(row, 0, name)
            channel = QSpinBox()
            channel.setRange(-1, 31)
            channel.setSpecialValueText("—")
            channel.setValue(axis.glove_channel)
            minimum = QDoubleSpinBox()
            minimum.setRange(-1000000, 1000000)
            minimum.setValue(axis.glove_min)
            maximum = QDoubleSpinBox()
            maximum.setRange(-1000000, 1000000)
            maximum.setValue(axis.glove_max)
            inverted = QCheckBox()
            inverted.setChecked(axis.glove_inverted)
            self.glove_mapping.setCellWidget(row, 1, channel)
            self.glove_mapping.setCellWidget(row, 2, minimum)
            self.glove_mapping.setCellWidget(row, 3, maximum)
            self.glove_mapping.setCellWidget(row, 4, inverted)
        self.glove_mapping.resizeColumnsToContents()
        mapping_layout.addWidget(self.glove_mapping)
        layout.addWidget(mapping, 1)
        self.scan_glove_ports()
        return widget

    def _normalize_field_metrics(self) -> None:
        for widget_type in (QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox):
            for widget in self.findChildren(widget_type):
                widget.setMinimumHeight(FIELD_MIN_HEIGHT)

    @staticmethod
    def _tune_form(form: QFormLayout) -> None:
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)

    def _tracking_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        frame, content = card(name="SettingsSurface")
        form = QFormLayout()
        cfg = self.controller.data["tracking"]
        camera = self.controller.data["camera"]
        self.lost_policy = QComboBox()
        self.lost_policy.addItem("Утримувати останнє", "hold")
        self.lost_policy.addItem("Перейти в нейтраль", "neutral")
        self.lost_policy.addItem("Перейти в безпечне", "safe")
        self.lost_policy.addItem("Зупинити передачу", "stop")
        self.lost_policy.setCurrentIndex(max(0, self.lost_policy.findData(cfg.get("lost_hand_policy", "safe"))))
        self.lost_timeout = QSpinBox()
        self.lost_timeout.setRange(100, 10000)
        self.lost_timeout.setValue(int(cfg.get("lost_hand_timeout_ms", 700)))
        self.lost_timeout.setSuffix(" мс")
        self.detection_conf = QSpinBox()
        self.detection_conf.setRange(1, 99)
        self.detection_conf.setValue(int(float(camera.get("detection_confidence", 0.55)) * 100))
        self.detection_conf.setSuffix("%")
        self.tracking_conf = QSpinBox()
        self.tracking_conf.setRange(1, 99)
        self.tracking_conf.setValue(int(float(camera.get("tracking_confidence", 0.55)) * 100))
        self.tracking_conf.setSuffix("%")
        self.value_smoothing = QSpinBox()
        self.value_smoothing.setRange(0, 98)
        self.value_smoothing.setValue(int(float(cfg.get("value_smoothing", 0.62)) * 100))
        self.value_smoothing.setSuffix("%")
        self.value_dead_zone = QDoubleSpinBox()
        self.value_dead_zone.setRange(0.0, 0.2)
        self.value_dead_zone.setSingleStep(0.005)
        self.value_dead_zone.setDecimals(3)
        self.value_dead_zone.setValue(float(cfg.get("value_dead_zone", 0.018)))
        self.draw_landmarks = QCheckBox()
        self.draw_landmarks.setChecked(bool(cfg.get("draw_landmarks", True)))
        form.addRow("Втрата руки", self.lost_policy)
        form.addRow("Таймаут", self.lost_timeout)
        form.addRow("Detection confidence", self.detection_conf)
        form.addRow("Tracking confidence", self.tracking_conf)
        form.addRow("Згладжування значень", self.value_smoothing)
        form.addRow("Поріг дребезгу", self.value_dead_zone)
        form.addRow("Показувати орієнтири", self.draw_landmarks)
        content.addLayout(form)
        layout.addWidget(frame)
        layout.addStretch(1)
        return widget

    def _safety_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        frame, content = card(name="SettingsSurface")
        form = QFormLayout()
        cfg = self.controller.data["safety"]
        self.transition = QSpinBox()
        self.transition.setRange(50, 10000)
        self.transition.setValue(int(cfg.get("smooth_transition_ms", 800)))
        self.transition.setSuffix(" мс")
        self.require_verified = QCheckBox()
        self.require_verified.setChecked(bool(cfg.get("require_verified_profile", True)))
        self.serial_timeout = QSpinBox()
        self.serial_timeout.setRange(100, 10000)
        self.serial_timeout.setValue(int(cfg.get("serial_timeout_ms", 1000)))
        self.serial_timeout.setSuffix(" мс")
        form.addRow("Плавний перехід", self.transition)
        form.addRow("Вимагати перевірені осі", self.require_verified)
        form.addRow("Таймаут ESP", self.serial_timeout)
        content.addLayout(form)
        layout.addWidget(frame)
        layout.addStretch(1)
        return widget

    def _about_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        frame, content = card(name="SettingsSurface")
        version = QApplication.applicationVersion() or "2.2.1"
        title = QLabel(f"Є-Рука {version}")
        title.setObjectName("PageTitle")
        content.addWidget(title)
        content.addWidget(QLabel("Керування роботизованою кистю через камеру, сенсорну рукавицю або ручну панель."))
        content.addWidget(QLabel("Власний код: MIT License. Qt/PySide6 та інші залежності мають окремі ліцензії."))
        content.addStretch(1)
        author = QLabel("Автор: Kico")
        author.setObjectName("MetricValueSmall")
        content.addWidget(author)

        paths, paths_layout = card(name="SettingsSurface")
        paths_layout.addWidget(QLabel("Файли та обслуговування програми"))
        install_path = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else project_root()
        config_path = Path(getattr(self.controller.config, "root", Path.home()))
        install_label = QLabel(f"Програма: {install_path}")
        config_label = QLabel(f"Налаштування: {config_path}")
        for label in (install_label, config_label):
            label.setObjectName("MicroText")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setWordWrap(True)
            paths_layout.addWidget(label)

        file_actions = QHBoxLayout()
        open_install = QPushButton("Відкрити папку програми")
        open_config = QPushButton("Відкрити папку налаштувань")
        open_license = QPushButton("Ліцензія")
        open_privacy = QPushButton("Конфіденційність")
        file_actions.addWidget(open_install)
        file_actions.addWidget(open_config)
        file_actions.addWidget(open_license)
        file_actions.addWidget(open_privacy)
        file_actions.addStretch(1)
        paths_layout.addLayout(file_actions)

        uninstall = QPushButton("Видалити Є-Рука з комп'ютера")
        uninstall.setProperty("danger", True)
        uninstall_path = install_path / "unins000.exe"
        uninstall.setVisible(uninstall_path.is_file())
        paths_layout.addWidget(uninstall, 0, Qt.AlignmentFlag.AlignLeft)
        open_install.clicked.connect(lambda: self._open_path(install_path))
        open_config.clicked.connect(lambda: self._open_path(config_path))
        open_license.clicked.connect(lambda: self._open_distribution_file("LICENSE"))
        open_privacy.clicked.connect(lambda: self._open_distribution_file("PRIVACY_POLICY_UK.txt"))
        uninstall.clicked.connect(lambda: self._run_uninstaller(uninstall_path))

        layout.addWidget(frame)
        layout.addWidget(paths)
        layout.addStretch(1)
        return widget

    @staticmethod
    def _open_path(path: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_distribution_file(self, name: str) -> None:
        candidates = [
            Path(sys.executable).resolve().parent / name,
            resource_path(name),
            project_root() / "packaging" / name,
        ]
        target = next((path for path in candidates if path.is_file()), None)
        if target:
            self._open_path(target)
        else:
            self.controller.toast.emit("warning", f"Файл не знайдено: {name}")

    def _run_uninstaller(self, path: Path) -> None:
        answer = QMessageBox.question(
            self,
            "Видалити Є-Рука",
            "Програму буде закрито та запущено майстер видалення. Локальний профіль калібрування буде збережено.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if QProcess.startDetached(str(path), []):
            QApplication.quit()
        else:
            self.controller.toast.emit("error", "Не вдалося запустити деінсталятор")

    @staticmethod
    def _fill_ports(combo: QComboBox, configured: str) -> None:
        combo.clear()
        ports = list(list_ports.comports())
        if not ports:
            combo.addItem("COM-порти не знайдено", "")
            return
        for port in ports:
            details = port.description or "Serial device"
            ids = f"  {port.vid:04X}:{port.pid:04X}" if port.vid is not None and port.pid is not None else ""
            combo.addItem(f"{port.device}  ·  {details}{ids}", port.device)
        combo.setCurrentIndex(max(0, combo.findData(configured)))

    def scan_ports(self) -> None:
        self._fill_ports(self.port, self.controller.data["serial"].get("port", ""))

    def scan_glove_ports(self) -> None:
        self._fill_ports(self.glove_port, self.controller.data["glove"].get("port", ""))

    def save(self) -> None:
        data = self.controller.data
        data["profile_name"] = self.profile_name.text().strip() or "Профіль руки"
        data["theme"] = self.theme.currentData()
        data["language"] = self.language.currentData()
        width, height = [int(value) for value in self.camera_resolution.currentText().split("×")]
        data["camera"].update(
            {
                "index": self.camera_index.value(),
                "width": width,
                "height": height,
                "fps": self.camera_fps.value(),
                "mirror": self.camera_mirror.isChecked(),
                "hand_preference": self.hand.currentData(),
                "detection_confidence": self.detection_conf.value() / 100.0,
                "tracking_confidence": self.tracking_conf.value() / 100.0,
            }
        )
        data["serial"].update(
            {
                "port": self.port.currentData() or "",
                "baudrate": self.baud.currentData(),
                "protocol": self.protocol.currentData(),
                "send_rate_hz": self.rate.value(),
                "auto_reconnect": self.auto_reconnect.isChecked(),
                "ack_enabled": self.ack.isChecked(),
            }
        )
        data["glove"].update(
            {
                "port": self.glove_port.currentData() or "",
                "baudrate": self.glove_baud.currentData(),
                "format": self.glove_format.currentData(),
                "channel_count": self.glove_channels.value(),
                "input_min": self.glove_input_min.value(),
                "input_max": self.glove_input_max.value(),
                "smoothing": self.glove_smoothing.value(),
                "auto_reconnect": self.glove_auto_reconnect.isChecked(),
            }
        )
        data["tracking"].update(
            {
                "lost_hand_policy": self.lost_policy.currentData(),
                "lost_hand_timeout_ms": self.lost_timeout.value(),
                "value_smoothing": self.value_smoothing.value() / 100.0,
                "value_dead_zone": self.value_dead_zone.value(),
                "draw_landmarks": self.draw_landmarks.isChecked(),
            }
        )
        data["safety"].update(
            {
                "smooth_transition_ms": self.transition.value(),
                "require_verified_profile": self.require_verified.isChecked(),
                "serial_timeout_ms": self.serial_timeout.value(),
            }
        )
        axes_by_id = {axis.id: axis for axis in self.controller.axes}
        axes = []
        for row in range(self.glove_mapping.rowCount()):
            axis_id = self.glove_mapping.item(row, 0).data(Qt.ItemDataRole.UserRole)
            old = axes_by_id[axis_id]
            axes.append(
                replace(
                    old,
                    glove_channel=self.glove_mapping.cellWidget(row, 1).value(),
                    glove_min=self.glove_mapping.cellWidget(row, 2).value(),
                    glove_max=self.glove_mapping.cellWidget(row, 3).value(),
                    glove_inverted=self.glove_mapping.cellWidget(row, 4).isChecked(),
                )
            )
        self.controller.update_axes(axes)
        self.controller.config.save()
        self.controller.update_serial_config()
        self.controller.update_glove_config()
        self.theme_changed.emit(data["theme"])
        self.language_changed.emit(data["language"])
        self.controller.toast.emit("success", "Налаштування збережено")

    def export_profile(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Експорт профілю", "ye-ruka-profile.json", "JSON (*.json)")
        if path:
            self.controller.config.export_to(Path(path))

    def import_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Імпорт профілю", "", "JSON (*.json)")
        if not path:
            return
        self.controller.config.import_from(Path(path))
        self.controller.data = self.controller.config.data
        self.controller.update_axes(self.controller.config.axes())
        self.controller.update_serial_config()
        self.controller.update_glove_config()
        self.controller.toast.emit("success", "Профіль імпортовано. Перезапустіть джерела даних")

    def reset_profile(self) -> None:
        self.controller.config.reset()
        self.controller.data = self.controller.config.data
        self.controller.update_axes(self.controller.config.axes())
        self.controller.update_serial_config()
        self.controller.update_glove_config()
        self.controller.toast.emit("warning", "Профіль скинуто до стандартного")
