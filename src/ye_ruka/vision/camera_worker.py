from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
from PySide6.QtCore import QThread, Signal

from ye_ruka.core.models import TrackingResult
from .tracker import HandTracker


class CameraThread(QThread):
    frame_ready = Signal(object)
    tracking_ready = Signal(object)
    state_changed = Signal(str)
    metrics = Signal(float, float)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._stop_event = threading.Event()
        self.settings: dict[str, object] = {}

    def configure(self, settings: dict[str, object], model_path: Path) -> None:
        self.settings = dict(settings)
        self.settings["model_path"] = model_path

    def stop(self) -> None:
        self._stop_event.set()
        self.wait(2500)

    def run(self) -> None:
        self._stop_event.clear()
        index = int(self.settings.get("index", 0))
        capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not capture.isOpened():
            capture = cv2.VideoCapture(index)
        if not capture.isOpened():
            self.error.emit(f"Не вдалося відкрити камеру {index}")
            self.state_changed.emit("error")
            return
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.settings.get("width", 1280)))
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.settings.get("height", 720)))
        capture.set(cv2.CAP_PROP_FPS, int(self.settings.get("fps", 30)))
        tracker: HandTracker | None = None
        try:
            tracker = HandTracker(
                Path(self.settings["model_path"]),
                float(self.settings.get("detection_confidence", 0.55)),
                float(self.settings.get("tracking_confidence", 0.55)),
            )
        except Exception as exc:
            self.error.emit(str(exc))
        self.state_changed.emit("running")
        frames = 0
        fps = 0.0
        fps_start = time.monotonic()
        start_clock = time.monotonic()
        while not self._stop_event.is_set():
            ok, frame = capture.read()
            if not ok:
                self.error.emit("Камера перестала повертати кадри")
                break
            if bool(self.settings.get("mirror", True)):
                frame = cv2.flip(frame, 1)
            processing_start = time.perf_counter()
            timestamp_ms = int((time.monotonic() - start_clock) * 1000)
            tracking = TrackingResult(False, timestamp_ms=timestamp_ms)
            if tracker is not None:
                try:
                    tracking = tracker.process(frame, timestamp_ms, str(self.settings.get("hand_preference", "auto")))
                    if bool(self.settings.get("draw_landmarks", True)):
                        frame = tracker.draw(frame, tracking)
                except Exception as exc:
                    self.error.emit(f"Помилка трекера: {exc}")
            processing_ms = (time.perf_counter() - processing_start) * 1000.0
            frames += 1
            elapsed = time.monotonic() - fps_start
            if elapsed >= 0.75:
                fps = frames / elapsed
                frames = 0
                fps_start = time.monotonic()
            self.frame_ready.emit(frame)
            self.tracking_ready.emit(tracking)
            self.metrics.emit(fps, processing_ms)
        capture.release()
        if tracker is not None:
            tracker.close()
        self.state_changed.emit("stopped")


class CameraScanThread(QThread):
    completed = Signal(list)

    def __init__(self, limit: int = 10) -> None:
        super().__init__()
        self.limit = limit

    def run(self) -> None:
        found: list[dict[str, object]] = []
        for index in range(self.limit):
            if self.isInterruptionRequested():
                break
            capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not capture.isOpened():
                capture.release()
                continue
            ok, _ = capture.read()
            if ok:
                width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                found.append({"index": index, "name": f"Camera {index}", "resolution": f"{width}×{height}"})
            capture.release()
        self.completed.emit(found)

    def stop(self) -> None:
        self.requestInterruption()
        self.wait(3000)
