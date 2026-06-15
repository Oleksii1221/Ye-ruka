from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from ye_ruka.glove.worker import GloveSerialThread
from ye_ruka.serial_io.worker import SerialThread
from ye_ruka.vision.camera_worker import CameraThread
from .config import ConfigManager
from .filters import FilterBank
from .gestures import built_in_gestures
from .models import AxisConfig, DiagnosticsSnapshot, Gesture, TrackingResult
from .protocol import SerialProtocol
from .tracking_calibration import apply_pose_calibration, stabilize_tracking_values


class ApplicationController(QObject):
    axes_changed = Signal(list)
    values_changed = Signal(dict)
    tracking_changed = Signal(object)
    frame_changed = Signal(object)
    packet_changed = Signal(str)
    diagnostics_changed = Signal(object)
    camera_state_changed = Signal(str)
    serial_state_changed = Signal(str)
    glove_state_changed = Signal(str)
    glove_values_changed = Signal(object, object)
    glove_packet_changed = Signal(str)
    transmission_changed = Signal(bool)
    gestures_changed = Signal(list)
    mode_changed = Signal(str)
    toast = Signal(str, str)
    log = Signal(str)

    def __init__(self, config: ConfigManager, model_path: Path) -> None:
        super().__init__()
        self.config = config
        self.data = config.data
        self.model_path = model_path
        self.axes = sorted(config.axes(), key=lambda item: item.channel)
        self.custom_gestures = config.gestures()
        self.filters = FilterBank(self.axes)
        self.protocol = SerialProtocol(self.data["serial"].get("protocol", "extended"))
        self.sequence = 0
        self.mode = "manual"
        self.transmission_enabled = False
        self.estop_latched = False
        self.last_tracking_time = 0.0
        self.last_filter_time = time.monotonic()
        self.current_values = {axis.id: axis.neutral_angle for axis in self.axes}
        self.target_values = dict(self.current_values)
        self.tracking_filtered: dict[str, float] = {}
        self.glove_filtered: list[float] = []
        self.diagnostics = DiagnosticsSnapshot(servo_values=self.ordered_values())
        self.camera_thread: CameraThread | None = None

        self.serial_thread = SerialThread()
        self.serial_thread.state_changed.connect(self._serial_state)
        self.serial_thread.log.connect(self._log)
        self.serial_thread.received.connect(lambda line: self._log(f"ROBOT RX: {line}"))
        self.serial_thread.error.connect(lambda text: self._error("Serial кисті", text))
        self.serial_thread.metrics.connect(self._serial_metrics)
        self.serial_thread.start()
        self.update_serial_config()

        self.glove_thread = GloveSerialThread()
        self.glove_thread.state_changed.connect(self._glove_state)
        self.glove_thread.line_received.connect(self._glove_line)
        self.glove_thread.values_received.connect(self._glove_values)
        self.glove_thread.metrics.connect(self._glove_metrics)
        self.glove_thread.error.connect(lambda text: self._error("Рукавиця", text, toast=False))
        self.glove_thread.log.connect(self._log)
        self.glove_thread.start()
        self.update_glove_config()

        self.transition_timer = QTimer(self)
        self.transition_timer.setInterval(20)
        self.transition_timer.timeout.connect(self._transition_tick)
        self.transition_start: dict[str, int] = {}
        self.transition_target: dict[str, int] = {}
        self.transition_started = 0.0
        self.transition_duration = 0.7
        self._publish_values(self.current_values, immediate=True)

    def all_gestures(self) -> list[Gesture]:
        return built_in_gestures(self.axes) + self.custom_gestures

    def set_mode(self, mode: str) -> None:
        if mode not in {"manual", "automatic", "glove"}:
            return
        if self.mode != mode:
            self.mode = mode
            self.filters.reset(self.current_values)
            self.mode_changed.emit(mode)
            names = {"manual": "Ручний режим", "automatic": "Камера", "glove": "Рукавиця"}
            self.toast.emit("info", f"Активне джерело: {names[mode]}")

    def set_manual_value(self, axis_id: str, value: int) -> None:
        if self.mode != "manual" or self.estop_latched:
            return
        self.target_values[axis_id] = value
        self._filter_and_publish(self.target_values)

    def set_grip(self, percent: int) -> None:
        amount = max(0.0, min(1.0, percent / 100.0))
        targets = dict(self.target_values)
        for axis in self.axes:
            if axis.grip and axis.enabled:
                targets[axis.id] = axis.map_normalized(min(1.0, amount * axis.grip_weight))
        self.target_values = targets
        self._filter_and_publish(targets)

    def apply_gesture(self, gesture: Gesture) -> None:
        self.set_mode("manual")
        self.start_transition(gesture.values, gesture.duration_ms)
        self.toast.emit("success", f"Жест: {gesture.name}")

    def save_gesture(self, name: str, duration_ms: int, hotkey: str = "") -> None:
        gesture = Gesture(name.strip(), dict(self.current_values), duration_ms, hotkey, False)
        self.custom_gestures = [item for item in self.custom_gestures if item.name != gesture.name]
        self.custom_gestures.append(gesture)
        self.config.set_gestures(self.custom_gestures)
        self.config.save()
        self.gestures_changed.emit(self.all_gestures())
        self.toast.emit("success", "Жест збережено")

    def delete_gesture(self, name: str) -> None:
        self.custom_gestures = [item for item in self.custom_gestures if item.name != name]
        self.config.set_gestures(self.custom_gestures)
        self.config.save()
        self.gestures_changed.emit(self.all_gestures())

    def rename_gesture(self, old_name: str, new_name: str) -> None:
        clean = new_name.strip()
        if not clean:
            return
        for gesture in self.custom_gestures:
            if gesture.name == old_name:
                gesture.name = clean
                break
        self.config.set_gestures(self.custom_gestures)
        self.config.save()
        self.gestures_changed.emit(self.all_gestures())
        self.toast.emit("success", "Жест перейменовано")

    def start_transition(self, values: dict[str, int], duration_ms: int | None = None) -> None:
        self.transition_start = dict(self.current_values)
        self.transition_target = {
            axis.id: (
                axis.clamp(values.get(axis.id, self.current_values.get(axis.id, axis.neutral_angle)))
                if axis.enabled
                else axis.safe_angle
            )
            for axis in self.axes
        }
        self.transition_started = time.monotonic()
        self.transition_duration = max(
            0.05,
            (duration_ms or self.data["safety"].get("smooth_transition_ms", 800)) / 1000.0,
        )
        self.transition_timer.start()

    def _transition_tick(self) -> None:
        progress = min(1.0, (time.monotonic() - self.transition_started) / self.transition_duration)
        eased = progress * progress * (3.0 - 2.0 * progress)
        values = {
            axis.id: int(
                round(
                    self.transition_start[axis.id]
                    + (self.transition_target[axis.id] - self.transition_start[axis.id]) * eased
                )
            )
            for axis in self.axes
        }
        self._publish_values(values, immediate=True)
        if progress >= 1.0:
            self.transition_timer.stop()
            self.target_values = dict(self.transition_target)

    def connect_serial(self) -> None:
        self.update_serial_config()
        self.serial_thread.connect_device()

    def disconnect_serial(self) -> None:
        self.set_transmission(False)
        self.serial_thread.disconnect_device()

    def connect_glove(self) -> None:
        self.update_glove_config()
        self.glove_thread.connect_device()

    def disconnect_glove(self) -> None:
        self.glove_thread.disconnect_device()

    def set_transmission(self, enabled: bool) -> None:
        if enabled and self.estop_latched:
            self.toast.emit("error", "Спочатку скиньте аварійну зупинку")
            self.transmission_changed.emit(False)
            return
        if enabled and self.data["safety"].get("require_verified_profile", True):
            unverified = [axis.name("uk") for axis in self.axes if axis.enabled and not axis.verified]
            if unverified:
                self.toast.emit("warning", "Профіль не перевірено. Перевірте осі або змініть параметр безпеки")
                self.transmission_changed.emit(False)
                return
        self.transmission_enabled = enabled
        self.serial_thread.set_enabled(enabled)
        self.transmission_changed.emit(enabled)
        self.toast.emit("success" if enabled else "info", "Передавання активовано" if enabled else "Передавання вимкнено")

    def emergency_stop(self) -> None:
        self.estop_latched = True
        safe = {axis.id: axis.safe_angle for axis in self.axes}
        self._publish_values(safe, immediate=True)
        self.serial_thread.send_once(self.protocol.encode(self.sequence, self.ordered_values()))
        self.serial_thread.set_enabled(False)
        self.transmission_enabled = False
        self.transmission_changed.emit(False)
        self.toast.emit("error", "Аварійна зупинка активована")

    def reset_estop(self) -> None:
        self.estop_latched = False
        self.toast.emit("info", "E-STOP скинуто. Передавання залишається вимкненим")

    def start_camera(self) -> None:
        if self.camera_thread and self.camera_thread.isRunning():
            return
        settings = dict(self.data["camera"])
        settings["draw_landmarks"] = self.data["tracking"].get("draw_landmarks", True)
        self.camera_thread = CameraThread()
        self.camera_thread.configure(settings, self.model_path)
        self.camera_thread.frame_ready.connect(self.frame_changed)
        self.camera_thread.tracking_ready.connect(self._tracking)
        self.camera_thread.state_changed.connect(self._camera_state)
        self.camera_thread.metrics.connect(self._camera_metrics)
        self.camera_thread.error.connect(lambda text: self._error("Камера", text))
        self.camera_thread.start()
        self.toast.emit("info", "Запуск камери")

    def stop_camera(self) -> None:
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        self.toast.emit("info", "Камеру зупинено")

    def update_serial_config(self) -> None:
        self.protocol.mode = self.data["serial"].get("protocol", "extended")
        serial_cfg = self.data["serial"]
        self.serial_thread.configure(
            str(serial_cfg.get("port", "")),
            int(serial_cfg.get("baudrate", 115200)),
            int(serial_cfg.get("send_rate_hz", 60)),
            bool(serial_cfg.get("auto_reconnect", True)),
        )

    def update_glove_config(self) -> None:
        cfg = self.data["glove"]
        self.glove_thread.configure(
            str(cfg.get("port", "")),
            int(cfg.get("baudrate", 115200)),
            bool(cfg.get("auto_reconnect", True)),
            str(cfg.get("format", "auto")),
            int(cfg.get("channel_count", len(self.axes))),
        )

    def update_axes(self, axes: list[AxisConfig]) -> None:
        self.axes = sorted(axes, key=lambda item: item.channel)
        self.config.set_axes(self.axes)
        self.config.save()
        self.filters.rebuild(self.axes)
        self.current_values = {axis.id: self.current_values.get(axis.id, axis.neutral_angle) for axis in self.axes}
        self.target_values = dict(self.current_values)
        self.axes_changed.emit(self.axes)
        self.gestures_changed.emit(self.all_gestures())
        self._publish_values(self.current_values, immediate=True)

    def ordered_values(self) -> list[int]:
        return [
            self.current_values.get(axis.id, axis.neutral_angle) if axis.enabled else axis.safe_angle
            for axis in self.axes
        ]

    def _tracking(self, result: TrackingResult) -> None:
        if result.detected:
            tracking_cfg = self.data.get("tracking", {})
            stabilized_raw = stabilize_tracking_values(
                result.raw_values,
                self.tracking_filtered,
                float(tracking_cfg.get("value_smoothing", 0.62)),
                float(tracking_cfg.get("value_dead_zone", 0.018)),
            )
            self.tracking_filtered = stabilized_raw
            result.calibration_values = dict(stabilized_raw)
            result.raw_values = apply_pose_calibration(
                stabilized_raw,
                self.axes,
                self.data.get("calibration", {}),
            )
        else:
            self.tracking_filtered = {}
        self.tracking_changed.emit(result)
        self.diagnostics.raw_values = dict(result.raw_values)
        if result.detected:
            self.last_tracking_time = time.monotonic()
            if self.mode == "automatic" and not self.estop_latched:
                targets = dict(self.target_values)
                for axis in self.axes:
                    if axis.enabled and axis.source in result.raw_values:
                        targets[axis.id] = axis.map_normalized(result.raw_values[axis.source])
                self.target_values = targets
                self._filter_and_publish(targets)
            return
        if self.mode != "automatic":
            return
        elapsed_ms = (time.monotonic() - self.last_tracking_time) * 1000.0
        timeout = int(self.data["tracking"].get("lost_hand_timeout_ms", 700))
        if elapsed_ms < timeout:
            return
        policy = self.data["tracking"].get("lost_hand_policy", "safe")
        if policy == "neutral":
            self.start_transition({axis.id: axis.neutral_angle for axis in self.axes}, 900)
        elif policy == "safe":
            self.start_transition({axis.id: axis.safe_angle for axis in self.axes}, 900)
        elif policy == "stop":
            self.set_transmission(False)

    def _glove_line(self, line: str) -> None:
        self.diagnostics.glove_last_packet = line
        self.glove_packet_changed.emit(line)
        self.log.emit(f"GLOVE RX: {line}")

    def _glove_values(self, values: list[float]) -> None:
        cfg = self.data["glove"]
        low = float(cfg.get("input_min", 0.0))
        high = float(cfg.get("input_max", 4095.0))
        span = high - low if high != low else 1.0
        normalized = [max(0.0, min(1.0, (value - low) / span)) for value in values]
        smoothing = max(0.0, min(0.98, float(cfg.get("smoothing", 0.22))))
        if len(self.glove_filtered) != len(normalized):
            self.glove_filtered = list(normalized)
        else:
            alpha = 1.0 - smoothing
            self.glove_filtered = [
                previous + alpha * (current - previous)
                for previous, current in zip(self.glove_filtered, normalized)
            ]
        self.diagnostics.glove_raw_values = list(values)
        self.diagnostics.glove_normalized_values = list(self.glove_filtered)
        self.glove_values_changed.emit(list(values), list(self.glove_filtered))
        if self.mode == "glove" and not self.estop_latched:
            targets = dict(self.target_values)
            for axis in self.axes:
                index = axis.glove_channel
                if axis.enabled and 0 <= index < len(values):
                    targets[axis.id] = axis.map_normalized(axis.normalize_glove(values[index]))
            self.target_values = targets
            self._filter_and_publish(targets)
        self.diagnostics_changed.emit(self.diagnostics)

    def _filter_and_publish(self, targets: dict[str, float]) -> None:
        now = time.monotonic()
        dt = min(0.2, max(0.001, now - self.last_filter_time))
        self.last_filter_time = now
        filtered = self.filters.update(targets, dt)
        self.diagnostics.filtered_values = {key: float(value) for key, value in filtered.items()}
        self._publish_values(filtered)

    def _publish_values(self, values: dict[str, int], immediate: bool = False) -> None:
        self.current_values = {
            axis.id: axis.clamp(values.get(axis.id, axis.neutral_angle)) if axis.enabled else axis.safe_angle
            for axis in self.axes
        }
        if immediate:
            self.filters.reset(self.current_values)
        self.sequence = (self.sequence + 1) % 100000
        packet = self.protocol.encode(self.sequence, self.ordered_values())
        self.serial_thread.set_packet(packet)
        self.diagnostics.last_packet = packet.strip()
        self.diagnostics.servo_values = self.ordered_values()
        self.values_changed.emit(dict(self.current_values))
        self.packet_changed.emit(packet.strip())
        self.diagnostics_changed.emit(self.diagnostics)

    def _camera_state(self, state: str) -> None:
        self.diagnostics.camera_state = state
        self.camera_state_changed.emit(state)
        self.diagnostics_changed.emit(self.diagnostics)

    def _serial_state(self, state: str) -> None:
        self.diagnostics.serial_state = state
        self.serial_state_changed.emit(state)
        self.diagnostics_changed.emit(self.diagnostics)

    def _glove_state(self, state: str) -> None:
        self.diagnostics.glove_state = state
        self.glove_state_changed.emit(state)
        self.diagnostics_changed.emit(self.diagnostics)
        if state == "connected":
            self.toast.emit("success", "Рукавицю підключено")
        elif state == "disconnected":
            self.glove_filtered = []

    def _camera_metrics(self, fps: float, processing_ms: float) -> None:
        self.diagnostics.camera_fps = fps
        self.diagnostics.processing_ms = processing_ms
        self.diagnostics_changed.emit(self.diagnostics)

    def _serial_metrics(self, packets: int, errors: int, last_sent: str) -> None:
        self.diagnostics.packets_sent = packets
        self.diagnostics.serial_errors = errors
        self.diagnostics_changed.emit(self.diagnostics)

    def _glove_metrics(self, packets: int, errors: int, rate: float) -> None:
        self.diagnostics.glove_packets = packets
        self.diagnostics.glove_errors = errors
        self.diagnostics.glove_rate = rate
        self.diagnostics_changed.emit(self.diagnostics)

    def _log(self, text: str) -> None:
        self.log.emit(text)

    def _error(self, source: str, text: str, toast: bool = True) -> None:
        message = f"{source}: {text}"
        self.log.emit(message)
        if toast:
            self.toast.emit("error", message)

    def shutdown(self) -> None:
        self.set_transmission(False)
        self.stop_camera()
        self.glove_thread.stop()
        self.serial_thread.stop()
        self.config.save()
