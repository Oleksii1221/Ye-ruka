from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from statistics import median

from .models import AxisConfig


@dataclass(slots=True)
class AxisFilter:
    config: AxisConfig
    value: float | None = None
    samples: deque[float] = field(default_factory=lambda: deque(maxlen=3))

    def reset(self, value: float | None = None) -> None:
        self.value = value
        self.samples.clear()

    def update(self, target: float, dt: float) -> float:
        target = float(self.config.clamp(target))
        self.samples.append(target)
        target = median(self.samples)
        if self.value is None:
            self.value = target
            return target
        alpha = max(0.0, min(1.0, self.config.smoothing))
        smoothed = self.value + alpha * (target - self.value)
        if abs(smoothed - self.value) < self.config.dead_zone:
            smoothed = self.value
        max_delta = max(0.0, self.config.speed_limit) * max(0.0, dt)
        delta = max(-max_delta, min(max_delta, smoothed - self.value))
        self.value = self.config.clamp(self.value + delta)
        return self.value


class FilterBank:
    def __init__(self, axes: list[AxisConfig]) -> None:
        self.filters = {axis.id: AxisFilter(axis) for axis in axes}

    def rebuild(self, axes: list[AxisConfig]) -> None:
        old = self.filters
        self.filters = {axis.id: AxisFilter(axis) for axis in axes}
        for axis in axes:
            if axis.id in old:
                self.filters[axis.id].value = old[axis.id].value

    def reset(self, values: dict[str, float] | None = None) -> None:
        values = values or {}
        for axis_id, axis_filter in self.filters.items():
            axis_filter.reset(values.get(axis_id))

    def update(self, targets: dict[str, float], dt: float) -> dict[str, int]:
        result: dict[str, int] = {}
        for axis_id, axis_filter in self.filters.items():
            target = targets.get(axis_id, axis_filter.config.neutral_angle)
            result[axis_id] = int(round(axis_filter.update(target, dt)))
        return result
