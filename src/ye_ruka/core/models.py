from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AxisConfig:
    id: str
    name_uk: str
    name_en: str
    channel: int
    servo: int
    min_angle: int = 0
    max_angle: int = 180
    neutral_angle: int = 90
    safe_angle: int = 90
    inverted: bool = False
    speed_limit: float = 240.0
    smoothing: float = 0.3
    dead_zone: float = 1.0
    source: str = ""
    grip: bool = True
    grip_weight: float = 1.0
    enabled: bool = True
    verified: bool = False
    glove_channel: int = -1
    glove_min: float = 0.0
    glove_max: float = 4095.0
    glove_inverted: bool = False

    def clamp(self, value: float) -> int:
        low, high = sorted((self.min_angle, self.max_angle))
        return int(round(max(low, min(high, value))))

    def map_normalized(self, value: float) -> int:
        value = max(0.0, min(1.0, value))
        if self.inverted:
            value = 1.0 - value
        return self.clamp(self.min_angle + value * (self.max_angle - self.min_angle))

    def normalize_glove(self, value: float) -> float:
        span = self.glove_max - self.glove_min
        if abs(span) < 1e-9:
            normalized = 0.0
        else:
            normalized = (value - self.glove_min) / span
        normalized = max(0.0, min(1.0, normalized))
        if self.glove_inverted:
            normalized = 1.0 - normalized
        return normalized

    def name(self, language: str) -> str:
        return self.name_en if language == "en" else self.name_uk


@dataclass(slots=True)
class Gesture:
    name: str
    values: dict[str, int]
    duration_ms: int = 700
    hotkey: str = ""
    builtin: bool = False


@dataclass(slots=True)
class TrackingResult:
    detected: bool
    handedness: str = ""
    confidence: float = 0.0
    raw_values: dict[str, float] = field(default_factory=dict)
    calibration_values: dict[str, float] = field(default_factory=dict)
    landmarks: list[list[float]] = field(default_factory=list)
    timestamp_ms: int = 0


@dataclass(slots=True)
class DiagnosticsSnapshot:
    camera_state: str = "stopped"
    tracker_state: str = "idle"
    serial_state: str = "disconnected"
    glove_state: str = "disconnected"
    camera_fps: float = 0.0
    processing_ms: float = 0.0
    tx_rate: float = 0.0
    packets_sent: int = 0
    serial_errors: int = 0
    last_packet: str = ""
    raw_values: dict[str, float] = field(default_factory=dict)
    filtered_values: dict[str, float] = field(default_factory=dict)
    servo_values: list[int] = field(default_factory=list)
    glove_packets: int = 0
    glove_errors: int = 0
    glove_rate: float = 0.0
    glove_last_packet: str = ""
    glove_raw_values: list[float] = field(default_factory=list)
    glove_normalized_values: list[float] = field(default_factory=list)


def dataclass_dict(value: Any) -> dict[str, Any]:
    return asdict(value)
