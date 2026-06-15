from __future__ import annotations

import json
import shutil
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from .models import AxisConfig, Gesture


class ConfigError(RuntimeError):
    pass


DEFAULT_GLOVE = {
    "port": "",
    "baudrate": 115200,
    "format": "auto",
    "channel_count": 7,
    "auto_reconnect": True,
    "line_timeout_ms": 750,
    "smoothing": 0.22,
    "input_min": 0.0,
    "input_max": 4095.0,
}

CURRENT_SCHEMA_VERSION = 4
DEFAULT_TRACKING = {
    "value_smoothing": 0.62,
    "value_dead_zone": 0.018,
}


class ConfigManager:
    def __init__(self, bundled_default: Path, app_name: str = "Ye-Ruka") -> None:
        self.bundled_default = bundled_default
        self.root = Path(user_config_dir(app_name, "Kico"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "profile.json"
        self.backup_dir = self.root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.data: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            shutil.copy2(self.bundled_default, self.path)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            changed = self._migrate(self.data)
            self.validate(self.data)
            if changed:
                self.save()
        except Exception as exc:
            broken = self.root / f"profile_broken_{datetime.now():%Y%m%d_%H%M%S}.json"
            if self.path.exists():
                shutil.copy2(self.path, broken)
            shutil.copy2(self.bundled_default, self.path)
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            self._migrate(self.data)
            raise ConfigError(f"Конфігурацію відновлено після помилки: {exc}") from exc
        return self.data

    def _migrate(self, data: dict[str, Any]) -> bool:
        changed = False
        version = int(data.get("schema_version", 1))
        if version < 2:
            data["schema_version"] = 2
            changed = True
        if "glove" not in data:
            data["glove"] = dict(DEFAULT_GLOVE)
            changed = True
        else:
            for key, value in DEFAULT_GLOVE.items():
                if key not in data["glove"]:
                    data["glove"][key] = value
                    changed = True
        tracking = data.setdefault("tracking", {})
        for key, value in DEFAULT_TRACKING.items():
            if key not in tracking:
                tracking[key] = value
                changed = True
        for raw in data.get("axes", []):
            defaults = {
                "glove_channel": int(raw.get("channel", -1)),
                "glove_min": float(data["glove"].get("input_min", 0.0)),
                "glove_max": float(data["glove"].get("input_max", 4095.0)),
                "glove_inverted": False,
            }
            for key, value in defaults.items():
                if key not in raw:
                    raw[key] = value
                    changed = True
        if version < 3:
            if self._add_thumb_base_axis(data):
                changed = True
            data["schema_version"] = 3
            changed = True
        if version < 4:
            bundled = json.loads(self.bundled_default.read_text(encoding="utf-8"))
            data["axes"] = deepcopy(bundled["axes"])
            data["profile_name"] = bundled.get("profile_name", data.get("profile_name", "Ye-Ruka"))
            data.setdefault("glove", dict(DEFAULT_GLOVE))["channel_count"] = 7
            data["schema_version"] = 4
            changed = True
        return changed

    @staticmethod
    def _add_thumb_base_axis(data: dict[str, Any]) -> bool:
        axes = data.get("axes", [])
        if not isinstance(axes, list) or any(raw.get("id") == "thumb_base_flex" for raw in axes if isinstance(raw, dict)):
            return False
        thumb = next((raw for raw in axes if isinstance(raw, dict) and raw.get("id") == "thumb_flex"), None)
        if not isinstance(thumb, dict):
            return False
        used_channels = [int(raw.get("channel", -1)) for raw in axes if isinstance(raw, dict)]
        used_servos = [int(raw.get("servo", -1)) for raw in axes if isinstance(raw, dict)]
        next_channel = max(used_channels, default=-1) + 1
        next_servo = max(used_servos, default=-1) + 1
        glove = data.setdefault("glove", dict(DEFAULT_GLOVE))
        glove["channel_count"] = max(int(glove.get("channel_count", 0)), next_channel + 1)
        axes.append(
            {
                "id": "thumb_base_flex",
                "name_uk": "Великий: основа",
                "name_en": "Thumb base flexion",
                "channel": next_channel,
                "servo": next_servo,
                "min_angle": int(thumb.get("min_angle", 15)),
                "max_angle": int(thumb.get("max_angle", 165)),
                "neutral_angle": int(thumb.get("neutral_angle", 30)),
                "safe_angle": int(thumb.get("safe_angle", 30)),
                "inverted": False,
                "speed_limit": 190.0,
                "smoothing": 0.27,
                "dead_zone": float(thumb.get("dead_zone", 1.0)),
                "source": "thumb_base_flex",
                "grip": True,
                "grip_weight": 0.75,
                "enabled": False,
                "verified": False,
                "glove_channel": next_channel,
                "glove_min": float(glove.get("input_min", 0.0)),
                "glove_max": float(glove.get("input_max", 4095.0)),
                "glove_inverted": False,
            }
        )
        return True

    def save(self, data: dict[str, Any] | None = None) -> None:
        if data is not None:
            self.data = data
        self._migrate(self.data)
        self.validate(self.data)
        if self.path.exists():
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(self.path, self.backup_dir / f"profile_{stamp}.json")
            backups = sorted(self.backup_dir.glob("profile_*.json"), reverse=True)
            for item in backups[10:]:
                item.unlink(missing_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def reset(self) -> None:
        shutil.copy2(self.bundled_default, self.path)
        self.load()

    def export_to(self, target: Path) -> None:
        self.save()
        shutil.copy2(self.path, target)

    def import_from(self, source: Path) -> None:
        data = json.loads(source.read_text(encoding="utf-8"))
        self._migrate(data)
        self.validate(data)
        self.data = data
        self.save()

    def axes(self) -> list[AxisConfig]:
        return [AxisConfig(**item) for item in self.data.get("axes", [])]

    def gestures(self) -> list[Gesture]:
        return [Gesture(**item) for item in self.data.get("gestures", [])]

    def set_axes(self, axes: list[AxisConfig]) -> None:
        self.data["axes"] = [asdict(axis) for axis in axes]

    def set_gestures(self, gestures: list[Gesture]) -> None:
        self.data["gestures"] = [asdict(gesture) for gesture in gestures]

    @staticmethod
    def validate(data: dict[str, Any]) -> None:
        if data.get("schema_version") != CURRENT_SCHEMA_VERSION:
            raise ConfigError("Непідтримувана версія конфігурації")
        axes = data.get("axes")
        if not isinstance(axes, list) or not axes:
            raise ConfigError("Профіль не містить осей")
        glove = data.get("glove")
        if not isinstance(glove, dict):
            raise ConfigError("Профіль не містить конфігурації рукавиці")
        ids: set[str] = set()
        channels: set[int] = set()
        for raw in axes:
            axis = AxisConfig(**raw)
            if axis.id in ids:
                raise ConfigError(f"Повторний ID осі: {axis.id}")
            if axis.channel in channels:
                raise ConfigError(f"Повторний канал: {axis.channel}")
            if axis.min_angle == axis.max_angle:
                raise ConfigError(f"Нульовий діапазон осі: {axis.id}")
            if not 0 <= axis.smoothing <= 1:
                raise ConfigError(f"Некоректне згладжування: {axis.id}")
            if axis.glove_min == axis.glove_max:
                raise ConfigError(f"Нульовий діапазон рукавиці для осі: {axis.id}")
            ids.add(axis.id)
            channels.add(axis.channel)
