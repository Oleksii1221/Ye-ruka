from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.paths import resource_path
from ye_ruka.firmware.service import CalibrationSerialThread, FirmwareFlashThread
from ye_ruka.ui.language import apply_language
from ye_ruka.ui.widgets.common import card, subtitle_label, title_label


SERVO_NAMES_UK = (
    "1 · Мізинець",
    "2 · Безіменний",
    "3 · Середній",
    "4 · Вказівний",
    "5 · Великий: згин",
    "6 · Великий: до пальців",
    "7 · Великий: до долоні",
)
SERVO_NAMES_EN = (
    "1 · Little finger",
    "2 · Ring finger",
    "3 · Middle finger",
    "4 · Index finger",
    "5 · Thumb flexion",
    "6 · Thumb opposition",
    "7 · Thumb palm flexion",
)


class ServicePage(QWidget):
    def __init__(self, controller: ApplicationController) -> None:
        super().__init__()
        self.controller = controller
        self.flash_thread: FirmwareFlashThread | None = None
        self.service_ready = False
        self.calibration = CalibrationSerialThread()
        self.calibration.state_changed.connect(self._calibration_state)
        self.calibration.received.connect(self._serial_received)
        self.calibration.error.connect(self._service_error)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(14)
        root.addWidget(title_label("Обслуговування"))
        root.addWidget(
            subtitle_label(
                "Прошивання ESP32, відновлення робочого режиму та сервісна перевірка приводів"
            )
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 8)
        layout.setSpacing(14)

        firmware, firmware_layout = card(name="SettingsSurface")
        firmware_layout.addWidget(self._section_title("ПРОШИВКА КОНТРОЛЕРА"))
        firmware_layout.addWidget(
            subtitle_label(
                "Готові бінарні прошивки вже входять до програми. Arduino IDE та PlatformIO не потрібні."
            )
        )
        port_row = QHBoxLayout()
        self.port = QComboBox()
        self.port.setMinimumHeight(44)
        self.refresh_button = QPushButton("Оновити порти")
        self.refresh_button.setMinimumHeight(44)
        port_row.addWidget(self.port, 1)
        port_row.addWidget(self.refresh_button)
        firmware_layout.addLayout(port_row)

        flash_buttons = QHBoxLayout()
        self.production_button = QPushButton("Встановити робочу прошивку")
        self.production_button.setProperty("accent", True)
        self.calibration_button = QPushButton("Встановити сервісну прошивку")
        flash_buttons.addWidget(self.production_button)
        flash_buttons.addWidget(self.calibration_button)
        flash_buttons.addStretch(1)
        firmware_layout.addLayout(flash_buttons)

        self.flash_progress = QProgressBar()
        self.flash_progress.setRange(0, 100)
        self.flash_progress.setValue(0)
        self.flash_progress.setTextVisible(False)
        firmware_layout.addWidget(self.flash_progress)
        self.flash_status = QLabel("Готово до роботи")
        self.flash_status.setObjectName("MicroText")
        firmware_layout.addWidget(self.flash_status)
        layout.addWidget(firmware)

        test, test_layout = card(name="SettingsSurface")
        test_layout.addWidget(self._section_title("СИРИЙ ТЕСТ СЕРВОПРИВОДІВ"))
        warning = QLabel(
            "Сервісна прошивка обходить кути профілю. Одночасно активна лише одна серва, "
            "але механізм може рухнути різко. Тримайте руки поза зоною руху."
        )
        warning.setWordWrap(True)
        warning.setProperty("tone", "warning")
        warning.setObjectName("InlineNotice")
        test_layout.addWidget(warning)
        self.risk_confirm = QCheckBox("Я розумію ризик і прибрав руки від механізму")
        test_layout.addWidget(self.risk_confirm)

        connection_row = QHBoxLayout()
        self.test_connect = QPushButton("Підключити сервісний режим")
        self.test_disconnect = QPushButton("Відключити")
        self.test_disconnect.setEnabled(False)
        self.test_state = QLabel("SERVICE  OFF")
        self.test_state.setObjectName("ModeBadge")
        connection_row.addWidget(self.test_connect)
        connection_row.addWidget(self.test_disconnect)
        connection_row.addWidget(self.test_state)
        connection_row.addStretch(1)
        test_layout.addLayout(connection_row)

        servo_row = QHBoxLayout()
        self.servo = QComboBox()
        self.servo.setMinimumWidth(250)
        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(-90, 90)
        self.angle_slider.setValue(0)
        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(-90, 90)
        self.angle_spin.setSuffix("°")
        self.angle_spin.setValue(0)
        self.move_button = QPushButton("Подати кут")
        self.move_button.setProperty("accent", True)
        self.center_button = QPushButton("Центр 0°")
        self.off_button = QPushButton("OFF")
        self.off_button.setProperty("danger", True)
        for widget in (self.servo, self.angle_spin, self.move_button, self.center_button, self.off_button):
            widget.setMinimumHeight(44)
        servo_row.addWidget(self.servo)
        servo_row.addWidget(self.angle_slider, 1)
        servo_row.addWidget(self.angle_spin)
        servo_row.addWidget(self.move_button)
        servo_row.addWidget(self.center_button)
        servo_row.addWidget(self.off_button)
        test_layout.addLayout(servo_row)
        self._set_test_controls(False)

        self.service_log = QTextEdit()
        self.service_log.setReadOnly(True)
        self.service_log.setMinimumHeight(135)
        self.service_log.setPlaceholderText("Журнал прошивання та сервісного порту")
        test_layout.addWidget(self.service_log)
        layout.addWidget(test)
        layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.refresh_button.clicked.connect(self.scan_ports)
        self.production_button.clicked.connect(lambda: self._confirm_flash("production"))
        self.calibration_button.clicked.connect(lambda: self._confirm_flash("calibration"))
        self.test_connect.clicked.connect(self._connect_calibration)
        self.test_disconnect.clicked.connect(self.calibration.disconnect_device)
        self.move_button.clicked.connect(self._move_servo)
        self.center_button.clicked.connect(self._center_servo)
        self.off_button.clicked.connect(lambda: self.calibration.send("off"))
        self.angle_slider.valueChanged.connect(self.angle_spin.setValue)
        self.angle_spin.valueChanged.connect(self.angle_slider.setValue)
        self.scan_ports()
        self.set_language(controller.data.get("language", "uk"))

    @staticmethod
    def _section_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionEyebrow")
        return label

    def scan_ports(self) -> None:
        selected = self.port.currentData() or self.controller.data["serial"].get("port", "")
        self.port.clear()
        ports = list(list_ports.comports())
        if not ports:
            self.port.addItem("COM-порти не знайдено", "")
            return
        for port in ports:
            details = port.description or "Serial device"
            self.port.addItem(f"{port.device}  ·  {details}", port.device)
        self.port.setCurrentIndex(max(0, self.port.findData(selected)))

    def _confirm_flash(self, mode: str) -> None:
        port = self.port.currentData() or ""
        if not port:
            self.controller.toast.emit("warning", "Оберіть COM-порт ESP32")
            return
        calibration = mode == "calibration"
        title = "Сервісна прошивка" if calibration else "Робоча прошивка"
        message = (
            "Після прошивання профільні обмеження не діятимуть. Використовуйте режим лише для тестування."
            if calibration
            else "Контролер буде повернуто до звичайного безпечного режиму Є-Рука."
        )
        result = QMessageBox.warning(
            self,
            title,
            f"{message}\n\nПід час прошивання не від'єднуйте USB-кабель.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if result != QMessageBox.StandardButton.Ok:
            return
        self.controller.disconnect_serial()
        self.calibration.disconnect_device()
        self._set_flash_busy(True)
        self.flash_status.setText(f"Підготовка {port}…")
        QTimer.singleShot(650, lambda: self._start_flash(mode, port))

    def _start_flash(self, mode: str, port: str) -> None:
        bundle = resource_path("firmware", mode)
        self.service_log.clear()
        self._append_log(f"FLASH {mode.upper()} -> {port}")
        self.flash_thread = FirmwareFlashThread(port, Path(bundle))
        self.flash_thread.log.connect(self._append_log)
        self.flash_thread.completed.connect(self._flash_completed)
        self.flash_thread.start()

    def _set_flash_busy(self, busy: bool) -> None:
        self.production_button.setEnabled(not busy)
        self.calibration_button.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy)
        self.port.setEnabled(not busy)
        self.flash_progress.setRange(0, 0 if busy else 100)
        if not busy:
            self.flash_progress.setValue(100)

    def _flash_completed(self, success: bool, message: str) -> None:
        self._set_flash_busy(False)
        self.flash_status.setText(message)
        self._append_log(message)
        self.controller.toast.emit("success" if success else "error", message)
        self.flash_thread = None

    def _connect_calibration(self) -> None:
        if not self.risk_confirm.isChecked():
            self.controller.toast.emit("warning", "Підтвердьте безпечну зону перед тестом")
            return
        port = self.port.currentData() or ""
        if not port:
            self.controller.toast.emit("warning", "Оберіть COM-порт ESP32")
            return
        self.controller.disconnect_serial()
        QTimer.singleShot(500, lambda: self.calibration.connect_device(port))

    def _move_servo(self) -> None:
        if not self.risk_confirm.isChecked():
            self.controller.toast.emit("warning", "Підтвердьте безпечну зону перед рухом")
            return
        command = f"{self.servo.currentIndex() + 1} {self.angle_spin.value()}"
        self.calibration.send(command)
        self._append_log(f"> {command}")

    def _center_servo(self) -> None:
        self.angle_spin.setValue(0)
        self._move_servo()

    def _calibration_state(self, state: str) -> None:
        connected = state == "connected"
        self.service_ready = False
        self.test_connect.setEnabled(not connected)
        self.test_disconnect.setEnabled(connected)
        self.test_state.setText("SERVICE  CHECK" if connected else "SERVICE  OFF")
        self.test_state.setProperty("live", False)
        self._set_test_controls(False)
        self.test_state.style().unpolish(self.test_state)
        self.test_state.style().polish(self.test_state)
        self._append_log(f"SERVICE {state.upper()}")

    def _serial_received(self, line: str) -> None:
        self._append_log(line)
        if line.startswith("!CAL,PONG") or line.startswith("!READY,CAL1"):
            self.service_ready = True
            self.test_state.setText("SERVICE  LIVE")
            self.test_state.setProperty("live", True)
            self._set_test_controls(True)
            self.test_state.style().unpolish(self.test_state)
            self.test_state.style().polish(self.test_state)
        elif line.startswith("!READY,YR1") or line.startswith("!ERR,FORMAT"):
            self._set_test_controls(False)
            self.controller.toast.emit("warning", "Спочатку встановіть сервісну прошивку")

    def _set_test_controls(self, enabled: bool) -> None:
        for widget in (
            self.servo,
            self.angle_slider,
            self.angle_spin,
            self.move_button,
            self.center_button,
            self.off_button,
        ):
            widget.setEnabled(enabled)

    def _service_error(self, message: str) -> None:
        self._append_log(f"ERROR: {message}")
        self.controller.toast.emit("error", f"Сервісний порт: {message}")

    def _append_log(self, line: str) -> None:
        self.service_log.append(line)

    def set_language(self, language: str) -> None:
        names = SERVO_NAMES_EN if language == "en" else SERVO_NAMES_UK
        current = self.servo.currentIndex()
        self.servo.clear()
        self.servo.addItems(names)
        self.servo.setCurrentIndex(max(0, current))
        apply_language(self, language)

    def shutdown(self) -> None:
        self.calibration.stop()
        if self.flash_thread and self.flash_thread.isRunning():
            self.flash_thread.wait()
