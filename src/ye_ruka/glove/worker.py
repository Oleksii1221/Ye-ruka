from __future__ import annotations

import queue
import threading
import time
from collections import deque

import serial
from PySide6.QtCore import QThread, Signal

from .protocol import GloveProtocol, GloveProtocolError


class GloveSerialThread(QThread):
    state_changed = Signal(str)
    line_received = Signal(str)
    values_received = Signal(list)
    metrics = Signal(int, int, float)
    error = Signal(str)
    log = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._stop_event = threading.Event()
        self._commands: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._port = ""
        self._baudrate = 115200
        self._auto_reconnect = True
        self._format = "auto"
        self._channels = 6
        self._connect_requested = False

    def configure(self, port: str, baudrate: int, auto_reconnect: bool, packet_format: str, channels: int) -> None:
        with self._lock:
            self._port = port
            self._baudrate = baudrate
            self._auto_reconnect = auto_reconnect
            self._format = packet_format
            self._channels = max(1, channels)
        self._commands.put("reconfigure")

    def connect_device(self) -> None:
        self._connect_requested = True
        self._commands.put("connect")

    def disconnect_device(self) -> None:
        self._connect_requested = False
        self._commands.put("disconnect")

    def stop(self) -> None:
        self._stop_event.set()
        self._commands.put("stop")
        self.wait(2500)

    def run(self) -> None:
        self._stop_event.clear()
        device: serial.Serial | None = None
        packets = 0
        errors = 0
        reconnect_at = 0.0
        timestamps: deque[float] = deque(maxlen=120)
        buffer = bytearray()
        while not self._stop_event.is_set():
            try:
                command = self._commands.get(timeout=0.015)
            except queue.Empty:
                command = ""
            if command in {"disconnect", "reconfigure"} and device is not None:
                try:
                    device.close()
                finally:
                    device = None
                    buffer.clear()
                    self.state_changed.emit("disconnected")
            if command == "connect":
                reconnect_at = 0.0
            if self._connect_requested and device is None and time.monotonic() >= reconnect_at:
                with self._lock:
                    port = self._port
                    baudrate = self._baudrate
                    auto_reconnect = self._auto_reconnect
                if port:
                    try:
                        device = serial.Serial(port, baudrate, timeout=0.05, write_timeout=0.2)
                        device.reset_input_buffer()
                        self.state_changed.emit("connected")
                        self.log.emit(f"Рукавицю підключено: {port} @ {baudrate}")
                    except Exception as exc:
                        errors += 1
                        self.state_changed.emit("error")
                        self.error.emit(str(exc))
                        reconnect_at = time.monotonic() + (2.0 if auto_reconnect else 3600.0)
            if device is None:
                continue
            try:
                chunk = device.read(max(1, min(1024, device.in_waiting or 1)))
                if chunk:
                    buffer.extend(chunk)
                while b"\n" in buffer:
                    raw, _, tail = buffer.partition(b"\n")
                    buffer = bytearray(tail)
                    line = raw.decode("utf-8", errors="replace").strip("\r \t")
                    if not line:
                        continue
                    self.line_received.emit(line)
                    with self._lock:
                        packet_format = self._format
                        channels = self._channels
                    try:
                        values = GloveProtocol(packet_format).parse(line, channels)
                    except GloveProtocolError as exc:
                        errors += 1
                        self.error.emit(str(exc))
                        continue
                    packets += 1
                    now = time.monotonic()
                    timestamps.append(now)
                    rate = 0.0
                    if len(timestamps) > 1:
                        span = timestamps[-1] - timestamps[0]
                        if span > 0:
                            rate = (len(timestamps) - 1) / span
                    self.values_received.emit(values)
                    self.metrics.emit(packets, errors, rate)
            except Exception as exc:
                errors += 1
                self.error.emit(str(exc))
                try:
                    device.close()
                except Exception:
                    pass
                device = None
                buffer.clear()
                self.state_changed.emit("disconnected")
                with self._lock:
                    auto_reconnect = self._auto_reconnect
                reconnect_at = time.monotonic() + (2.0 if auto_reconnect else 3600.0)
        if device is not None:
            device.close()
        self.state_changed.emit("disconnected")
