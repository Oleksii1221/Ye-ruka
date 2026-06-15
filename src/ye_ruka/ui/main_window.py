from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QSettings, Qt
from PySide6.QtGui import QCloseEvent, QCursor, QIcon, QKeySequence, QMouseEvent, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.paths import resource_path
from ye_ruka.ui.language import apply_language
from ye_ruka.ui.pages.automatic import AutomaticPage
from ye_ruka.ui.pages.calibration import CalibrationPage
from ye_ruka.ui.pages.diagnostics import DiagnosticsPage
from ye_ruka.ui.pages.glove import GlovePage
from ye_ruka.ui.pages.home import HomePage
from ye_ruka.ui.pages.manual import ManualPage
from ye_ruka.ui.pages.service import ServicePage
from ye_ruka.ui.pages.settings import SettingsPage
from ye_ruka.ui.widgets.navigation import NavigationButton
from ye_ruka.ui.widgets.terminal import SerialTerminalDialog
from ye_ruka.ui.widgets.titlebar import TitleBar
from ye_ruka.ui.widgets.toast import ToastStack


BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 1000000, 2000000)


class MainWindow(QMainWindow):
    BORDER = 7

    def __init__(self, controller: ApplicationController, theme_manager) -> None:
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager
        self.setWindowTitle("Є-Рука")
        self.setWindowIcon(QIcon(str(resource_path("resources", "icons", "ye-ruka.ico"))))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1120, 720)
        self.resize(1480, 900)
        self.setObjectName("Root")

        central = QWidget()
        central.setObjectName("Root")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        logo = QPixmap(str(resource_path("resources", "logo", "ye-ruka-logo.png")))
        self.titlebar = TitleBar(logo)
        self.titlebar.set_profile(controller.data.get("profile_name", "Default profile"))
        self.titlebar.minimize_clicked.connect(self.showMinimized)
        self.titlebar.maximize_clicked.connect(self.toggle_maximized)
        self.titlebar.fullscreen_clicked.connect(self.toggle_fullscreen)
        self.titlebar.close_clicked.connect(self.close)
        self.titlebar.double_clicked.connect(self.toggle_maximized)
        outer.addWidget(self.titlebar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.sidebar = self._create_sidebar()
        body.addWidget(self.sidebar)

        workspace = QWidget()
        workspace.setObjectName("Workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        self.command_bar = self._create_command_bar()
        workspace_layout.addWidget(self.command_bar)
        self.stack = QStackedWidget()
        self.stack.setObjectName("PageStack")
        self.pages = {
            "home": HomePage(),
            "automatic": AutomaticPage(controller),
            "glove": GlovePage(controller),
            "manual": ManualPage(controller),
            "calibration": CalibrationPage(controller),
            "service": ServicePage(controller),
            "diagnostics": DiagnosticsPage(),
            "settings": SettingsPage(controller),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        workspace_layout.addWidget(self.stack, 1)
        self.status = self._create_statusbar()
        workspace_layout.addWidget(self.status)
        body.addWidget(workspace, 1)
        outer.addLayout(body, 1)

        self.toast_stack = ToastStack(central)
        self.toast_stack.raise_()
        self.terminal = SerialTerminalDialog(self)
        self.terminal_shortcut = QShortcut(QKeySequence("F12"), self)
        self.terminal_shortcut.activated.connect(self.terminal.toggle_visible)
        self.pages["home"].navigate.connect(self.navigate)
        self.pages["settings"].theme_changed.connect(self.apply_theme)
        self.pages["settings"].language_changed.connect(self.apply_language)
        controller.diagnostics_changed.connect(self.pages["home"].update_diagnostics)
        controller.diagnostics_changed.connect(self.pages["diagnostics"].update_snapshot)
        controller.diagnostics_changed.connect(self.update_status)
        controller.log.connect(self.pages["diagnostics"].append_log)
        controller.log.connect(self.terminal.append_log)
        controller.toast.connect(self.toast_stack.show_message)
        controller.serial_state_changed.connect(self.serial_state_changed)
        controller.glove_state_changed.connect(self.glove_state_changed)
        controller.camera_state_changed.connect(self.camera_state_changed)
        controller.transmission_changed.connect(self.transmission_state_changed)
        controller.mode_changed.connect(self.mode_state_changed)

        self.navigate("home")
        self.scan_ports()
        self.restore_window()
        self.apply_language(controller.data.get("language", "uk"))
        QApplication.instance().installEventFilter(self)

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("NavigationRail")
        sidebar.setFixedWidth(218)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(4)
        eyebrow = QLabel("CONTROL SPACE")
        eyebrow.setObjectName("SectionEyebrow")
        layout.addWidget(eyebrow)
        layout.addSpacing(8)
        items = [
            ("home", "home", "Головна"),
            ("automatic", "camera", "Камера"),
            ("glove", "glove", "Рукавиця"),
            ("manual", "manual", "Ручне керування"),
            ("calibration", "calibration", "Калібрування"),
            ("service", "service", "Обслуговування"),
            ("diagnostics", "diagnostics", "Діагностика"),
            ("settings", "settings", "Налаштування"),
        ]
        self.nav_buttons: dict[str, NavigationButton] = {}
        for key, icon, text in items:
            button = NavigationButton(icon, text)
            button.clicked.connect(lambda checked=False, name=key: self.navigate(name))
            layout.addWidget(button)
            self.nav_buttons[key] = button
        layout.addStretch(1)
        self.side_camera = QLabel("●  CAMERA")
        self.side_glove = QLabel("●  GLOVE")
        self.side_robot = QLabel("●  ROBOT")
        for label in (self.side_camera, self.side_glove, self.side_robot):
            label.setObjectName("RailStatus")
            layout.addWidget(label)
        layout.addSpacing(10)
        author = QLabel("Medvid Oleksii\nKico")
        author.setObjectName("RailAuthor")
        layout.addWidget(author)
        return sidebar

    def _create_command_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("CommandBar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 10, 20, 10)
        layout.setSpacing(8)
        label = QLabel("ROBOT LINK")
        label.setObjectName("SectionEyebrow")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(250)
        self.baud_combo = QComboBox()
        for value in BAUDRATES:
            self.baud_combo.addItem(str(value), value)
        self.refresh_port_button = QPushButton("↻")
        self.refresh_port_button.setObjectName("RoundButton")
        self.refresh_port_button.setFixedSize(36, 36)
        self.connect_button = QPushButton("Підключити")
        self.connect_button.setProperty("accent", True)
        self.disconnect_button = QPushButton("Відключити")
        divider = QFrame()
        divider.setObjectName("VerticalDivider")
        divider.setFixedWidth(1)
        self.tx_button = QPushButton("TX OFF")
        self.tx_button.setObjectName("TransmitButton")
        self.tx_button.setCheckable(True)
        self.mode_badge = QLabel("MANUAL")
        self.mode_badge.setObjectName("ModeBadge")
        self.reset_estop_button = QPushButton("RESET E-STOP")
        self.estop_button = QPushButton("E-STOP")
        self.estop_button.setProperty("danger", True)
        self.estop_button.setMinimumWidth(106)
        layout.addWidget(label)
        layout.addWidget(self.port_combo)
        layout.addWidget(self.baud_combo)
        layout.addWidget(self.refresh_port_button)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addSpacing(8)
        layout.addWidget(divider)
        layout.addSpacing(8)
        layout.addWidget(self.mode_badge)
        layout.addWidget(self.tx_button)
        layout.addStretch(1)
        layout.addWidget(self.reset_estop_button)
        layout.addWidget(self.estop_button)
        self.refresh_port_button.clicked.connect(self.scan_ports)
        self.connect_button.clicked.connect(self.connect_serial)
        self.disconnect_button.clicked.connect(self.controller.disconnect_serial)
        self.tx_button.toggled.connect(self.controller.set_transmission)
        self.estop_button.clicked.connect(self.controller.emergency_stop)
        self.reset_estop_button.clicked.connect(self.controller.reset_estop)
        return frame

    def _create_statusbar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("StatusStrip")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 6, 22, 7)
        layout.setSpacing(18)
        self.camera_status = QLabel("CAMERA  —")
        self.glove_status = QLabel("GLOVE  —")
        self.serial_status = QLabel("ROBOT  —")
        self.tx_status = QLabel("TX  OFF")
        self.packet_status = QLabel("0 PACKETS")
        for item in (self.camera_status, self.glove_status, self.serial_status, self.tx_status, self.packet_status):
            item.setObjectName("BottomMetric")
        layout.addWidget(self.camera_status)
        layout.addWidget(self.glove_status)
        layout.addWidget(self.serial_status)
        layout.addWidget(self.tx_status)
        layout.addStretch(1)
        layout.addWidget(self.packet_status)
        return frame

    def scan_ports(self) -> None:
        configured = self.controller.data["serial"].get("port", "")
        baud = int(self.controller.data["serial"].get("baudrate", 115200))
        self.baud_combo.setCurrentIndex(max(0, self.baud_combo.findData(baud)))
        self.port_combo.clear()
        ports = list(list_ports.comports())
        if not ports:
            self.port_combo.addItem("COM-порти не знайдено", "")
            return
        glove_port = self.controller.data["glove"].get("port", "")
        for port in ports:
            ids = f"  {port.vid:04X}:{port.pid:04X}" if port.vid is not None and port.pid is not None else ""
            suffix = "  • GLOVE" if port.device == glove_port else ""
            self.port_combo.addItem(f"{port.device}  ·  {port.description}{ids}{suffix}", port.device)
        index = self.port_combo.findData(configured)
        self.port_combo.setCurrentIndex(max(0, index))

    def connect_serial(self) -> None:
        self.controller.data["serial"]["port"] = self.port_combo.currentData() or ""
        self.controller.data["serial"]["baudrate"] = int(self.baud_combo.currentData())
        self.controller.config.save()
        self.controller.connect_serial()

    def navigate(self, name: str) -> None:
        page = self.pages[name]
        self.stack.setCurrentWidget(page)
        for key, button in self.nav_buttons.items():
            button.setChecked(key == name)
        if name == "automatic":
            self.controller.set_mode("automatic")
        elif name == "manual":
            self.controller.set_mode("manual")
        elif name == "glove":
            self.controller.set_mode("glove")

    def update_status(self, snapshot) -> None:
        camera_live = snapshot.camera_state == "running"
        glove_live = snapshot.glove_state == "connected"
        robot_live = snapshot.serial_state == "connected"
        self.camera_status.setText(f"CAMERA  {'LIVE' if camera_live else 'OFF'}")
        self.glove_status.setText(f"GLOVE  {'LIVE' if glove_live else 'OFF'}")
        self.serial_status.setText(f"ROBOT  {'LIVE' if robot_live else 'OFF'}")
        self.packet_status.setText(f"{snapshot.packets_sent} PACKETS  ·  {snapshot.serial_errors} ERR")
        self.side_camera.setText(f"●  CAMERA  {'LIVE' if camera_live else 'OFF'}")
        self.side_glove.setText(f"●  GLOVE  {'LIVE' if glove_live else 'OFF'}")
        self.side_robot.setText(f"●  ROBOT  {'LIVE' if robot_live else 'OFF'}")
        for label, state in (
            (self.side_camera, camera_live),
            (self.side_glove, glove_live),
            (self.side_robot, robot_live),
        ):
            label.setProperty("live", state)
            label.style().unpolish(label)
            label.style().polish(label)

    def serial_state_changed(self, state: str) -> None:
        self.connect_button.setEnabled(state != "connected")
        self.disconnect_button.setEnabled(state == "connected")

    def glove_state_changed(self, state: str) -> None:
        pass

    def camera_state_changed(self, state: str) -> None:
        if state == "running":
            self.toast_stack.show_message("success", "Камера запущена")

    def transmission_state_changed(self, enabled: bool) -> None:
        self.tx_button.blockSignals(True)
        self.tx_button.setChecked(enabled)
        self.tx_button.setText("TX LIVE" if enabled else "TX OFF")
        self.tx_button.blockSignals(False)
        self.tx_status.setText("TX  LIVE" if enabled else "TX  OFF")

    def mode_state_changed(self, mode: str) -> None:
        self.mode_badge.setText({"manual": "MANUAL", "automatic": "CAMERA", "glove": "GLOVE"}.get(mode, mode.upper()))

    def apply_theme(self, theme: str) -> None:
        self.theme_manager.apply(QApplication.instance(), theme)
        for widget in self.findChildren(QWidget):
            widget.update()

    def apply_language(self, language: str) -> None:
        self.controller.data["language"] = language
        apply_language(self, language)
        for key in ("automatic", "manual", "calibration", "service"):
            self.pages[key].set_language(language)
        self.titlebar.title.setText("Ye-Ruka" if language == "en" else "Є-Рука")
        self.setWindowTitle(self.titlebar.title.text())

    def toggle_maximized(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            return
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def toggle_fullscreen(self) -> None:
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        width = min(430, max(320, self.width() // 4))
        x = self.sidebar.width() + 24
        height = min(240, max(150, self.height() - 170))
        y = max(118, self.height() - height - 58)
        self.toast_stack.setGeometry(x, y, width, height)

    def eventFilter(self, watched, event) -> bool:
        if self.isMaximized() or self.isFullScreen():
            return super().eventFilter(watched, event)
        if isinstance(watched, QWidget) and watched.window() is not self:
            return super().eventFilter(watched, event)
        if event.type() not in {QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress}:
            return super().eventFilter(watched, event)
        if not isinstance(event, QMouseEvent):
            return super().eventFilter(watched, event)
        local = self.mapFromGlobal(event.globalPosition().toPoint())
        edges = self._edges_at(local)
        if event.type() == QEvent.Type.MouseMove:
            self._set_resize_cursor(edges)
        elif event.button() == Qt.MouseButton.LeftButton and edges:
            handle = self.windowHandle()
            if handle:
                handle.startSystemResize(edges)
                return True
        return super().eventFilter(watched, event)

    def _edges_at(self, pos: QPoint) -> Qt.Edge:
        edges = Qt.Edge(0)
        if pos.x() <= self.BORDER:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= self.width() - self.BORDER:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= self.BORDER:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= self.height() - self.BORDER:
            edges |= Qt.Edge.BottomEdge
        return edges

    @staticmethod
    def _set_resize_cursor(edges: Qt.Edge) -> None:
        shape = None
        if edges in {Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.Edge.RightEdge | Qt.Edge.BottomEdge}:
            shape = Qt.CursorShape.SizeFDiagCursor
        elif edges in {Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.Edge.LeftEdge | Qt.Edge.BottomEdge}:
            shape = Qt.CursorShape.SizeBDiagCursor
        elif edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
            shape = Qt.CursorShape.SizeHorCursor
        elif edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge):
            shape = Qt.CursorShape.SizeVerCursor
        if shape is None:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
        elif QApplication.overrideCursor() is None:
            QApplication.setOverrideCursor(QCursor(shape))
        else:
            QApplication.changeOverrideCursor(QCursor(shape))

    def restore_window(self) -> None:
        settings = QSettings("Kico", "Ye-Ruka")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        if settings.value("maximized", False, bool):
            self.showMaximized()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.pages["automatic"].shutdown()
        self.pages["service"].shutdown()
        settings = QSettings("Kico", "Ye-Ruka")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("maximized", self.isMaximized())
        self.controller.shutdown()
        event.accept()
