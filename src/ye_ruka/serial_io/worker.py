from __future__ import annotations

import queue
import threading
import time
from datetime import datetime

import serial
from PySide6.QtCore import QThread, Signal


class SerialThread(QThread):
    state_changed = Signal(str)
    log = Signal(str)
    received = Signal(str)
    metrics = Signal(int, int, str)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._stop_event = threading.Event()
        self._commands: queue.Queue[tuple[str, object | None]] = queue.Queue()
        self._lock = threading.Lock()
        self._packet = ""
        self._port = ""
        self._baudrate = 115200
        self._rate_hz = 60
        self._auto_reconnect = True
        self._enabled = False
        self._connect_requested = False

    def configure(self, port: str, baudrate: int, rate_hz: int, auto_reconnect: bool) -> None:
        with self._lock:
            self._port = port
            self._baudrate = baudrate
            self._rate_hz = max(1, rate_hz)
            self._auto_reconnect = auto_reconnect
        self._commands.put(("reconfigure", None))

    def connect_device(self) -> None:
        self._connect_requested = True
        self._commands.put(("connect", None))

    def disconnect_device(self) -> None:
        self._connect_requested = False
        self._commands.put(("disconnect", None))

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_packet(self, packet: str) -> None:
        with self._lock:
            self._packet = packet

    def send_once(self, packet: str) -> None:
        self._commands.put(("send_once", packet))

    def stop(self) -> None:
        self._stop_event.set()
        self._commands.put(("stop", None))
        self.wait(2500)

    def run(self) -> None:
        self._stop_event.clear()
        device: serial.Serial | None = None
        packets = 0
        errors = 0
        last_sent = "—"
        next_send = time.monotonic()
        next_metrics = time.monotonic()
        reconnect_at = 0.0
        while not self._stop_event.is_set():
            command_timeout = 0.01
            if self._enabled:
                command_timeout = 0.001
            try:
                command, payload = self._commands.get(timeout=command_timeout)
            except queue.Empty:
                command, payload = "", None
            if command in {"disconnect", "reconfigure"} and device is not None:
                device.close()
                device = None
                self.state_changed.emit("disconnected")
            if command == "connect":
                reconnect_at = 0.0
            if command == "send_once" and device is not None and device.is_open:
                try:
                    device.write(str(payload).encode("ascii"))
                    device.flush()
                    packets += 1
                    last_sent = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                except Exception as exc:
                    errors += 1
                    self.error.emit(str(exc))
            if self._connect_requested and device is None and time.monotonic() >= reconnect_at:
                with self._lock:
                    port, baudrate = self._port, self._baudrate
                if port:
                    try:
                        device = serial.Serial(port, baudrate, timeout=0, write_timeout=0.2)
                        self.state_changed.emit("connected")
                        self.log.emit(f"Підключено {port} @ {baudrate}")
                        next_send = time.monotonic()
                    except Exception as exc:
                        errors += 1
                        self.state_changed.emit("error")
                        self.error.emit(str(exc))
                        reconnect_at = time.monotonic() + (2.0 if self._auto_reconnect else 3600.0)
            if device is not None:
                try:
                    waiting = device.in_waiting
                    if waiting:
                        line = device.readline().decode("utf-8", errors="replace").strip()
                        if line:
                            self.received.emit(line)
                    now = time.monotonic()
                    with self._lock:
                        rate, packet = self._rate_hz, self._packet
                    if self._enabled and packet and now >= next_send:
                        device.write(packet.encode("ascii"))
                        packets += 1
                        last_sent = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        period = 1.0 / max(1, rate)
                        next_send = max(next_send + period, now + period)
                    if now >= next_metrics:
                        self.metrics.emit(packets, errors, last_sent)
                        next_metrics = now + 0.2
                except Exception as exc:
                    errors += 1
                    self.error.emit(str(exc))
                    try:
                        device.close()
                    except Exception:
                        pass
                    device = None
                    self.state_changed.emit("disconnected")
                    reconnect_at = time.monotonic() + (2.0 if self._auto_reconnect else 3600.0)
        if device is not None:
            device.close()
        self.state_changed.emit("disconnected")
