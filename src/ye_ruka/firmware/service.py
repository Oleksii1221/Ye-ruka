from __future__ import annotations

import queue
import subprocess
import threading
import time
from pathlib import Path

import serial
from PySide6.QtCore import QThread, Signal

from ye_ruka.core.paths import project_root, resource_path


def flash_arguments(port: str, bundle: Path, baudrate: int = 460800) -> list[str]:
    image = bundle / "merged.bin"
    if not image.is_file():
        raise FileNotFoundError(f"Відсутній файл прошивки: {image}")
    return [
        "--skip-update-check",
        "write-bin",
        "--port",
        port,
        "--baud",
        str(baudrate),
        "--chip",
        "esp32",
        "--non-interactive",
        "0x0",
        str(image),
    ]


def flasher_path() -> Path:
    bundled = resource_path("tools", "espflash.exe")
    if bundled.is_file():
        return bundled
    return project_root() / "tools" / "espflash" / "espflash.exe"


class FirmwareFlashThread(QThread):
    log = Signal(str)
    completed = Signal(bool, str)

    def __init__(self, port: str, bundle: Path) -> None:
        super().__init__()
        self.port = port
        self.bundle = bundle

    def run(self) -> None:
        try:
            arguments = flash_arguments(self.port, self.bundle)
            executable = flasher_path()
            if not executable.is_file():
                raise FileNotFoundError(f"Відсутній інструмент прошивання: {executable}")
            flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            process = subprocess.Popen(
                [str(executable), *arguments],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags,
            )
            if process.stdout:
                for line in process.stdout:
                    if line.strip():
                        self.log.emit(line.rstrip())
            code = process.wait()
            if code == 0:
                self.completed.emit(True, "Прошивання завершено")
            else:
                self.completed.emit(False, f"espflash завершився з кодом {code}")
        except BaseException as exc:
            self.completed.emit(False, str(exc))


class CalibrationSerialThread(QThread):
    state_changed = Signal(str)
    received = Signal(str)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._stop_event = threading.Event()
        self._commands: queue.Queue[tuple[str, object | None]] = queue.Queue()
        self._port = ""

    def connect_device(self, port: str) -> None:
        self._port = port
        if not self.isRunning():
            self.start()
        self._commands.put(("connect", port))

    def disconnect_device(self) -> None:
        self._commands.put(("disconnect", None))

    def send(self, command: str) -> None:
        self._commands.put(("send", command.strip() + "\n"))

    def stop(self) -> None:
        self._stop_event.set()
        self._commands.put(("stop", None))
        self.wait(2000)

    def run(self) -> None:
        self._stop_event.clear()
        device: serial.Serial | None = None
        while not self._stop_event.is_set():
            try:
                action, payload = self._commands.get(timeout=0.02)
            except queue.Empty:
                action, payload = "", None

            if action in {"disconnect", "connect", "stop"} and device is not None:
                try:
                    device.write(b"off\n")
                    device.flush()
                    time.sleep(0.03)
                    device.close()
                except Exception:
                    pass
                device = None
                self.state_changed.emit("disconnected")

            if action == "connect":
                try:
                    device = serial.Serial(str(payload), 115200, timeout=0.02, write_timeout=0.3)
                    time.sleep(1.8)
                    device.reset_input_buffer()
                    device.write(b"ping\n")
                    self.state_changed.emit("connected")
                except Exception as exc:
                    device = None
                    self.state_changed.emit("error")
                    self.error.emit(str(exc))

            if action == "send" and device is not None:
                try:
                    device.write(str(payload).encode("ascii"))
                    device.flush()
                except Exception as exc:
                    self.error.emit(str(exc))

            if device is not None:
                try:
                    line = device.readline().decode("utf-8", errors="replace").strip()
                    if line:
                        self.received.emit(line)
                except Exception as exc:
                    self.error.emit(str(exc))
                    try:
                        device.close()
                    except Exception:
                        pass
                    device = None
                    self.state_changed.emit("disconnected")

        if device is not None:
            try:
                device.write(b"off\n")
                device.close()
            except Exception:
                pass
        self.state_changed.emit("disconnected")
