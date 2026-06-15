from __future__ import annotations

from .models import AxisConfig


def apply_pose_calibration(
    raw_values: dict[str, float],
    axes: list[AxisConfig],
    calibration: dict,
) -> dict[str, float]:
    poses = calibration.get("poses", {}) if isinstance(calibration, dict) else {}
    open_values = _pose_values(poses.get("open"))
    fist_values = _pose_values(poses.get("fist"))
    if not open_values:
        return dict(raw_values)
    calibrated = dict(raw_values)
    for axis in axes:
        source = axis.source
        if not source or source not in raw_values or source not in open_values:
            continue
        closed_values = _closed_pose_values(poses, axis) or fist_values
        if source not in closed_values:
            continue
        low = float(open_values[source])
        high = float(closed_values[source])
        span = high - low
        if abs(span) < 1e-6:
            continue
        normalized = (float(raw_values[source]) - low) / span
        calibrated[source] = max(0.0, min(1.0, normalized))
    return calibrated


def stabilize_tracking_values(
    raw_values: dict[str, float],
    previous_values: dict[str, float],
    smoothing: float,
    dead_zone: float,
) -> dict[str, float]:
    smoothing = max(0.0, min(0.98, smoothing))
    dead_zone = max(0.0, dead_zone)
    alpha = 1.0 - smoothing
    stabilized: dict[str, float] = {}
    for key, value in raw_values.items():
        current = float(value)
        if key not in previous_values:
            stabilized[key] = current
            continue
        previous = previous_values[key]
        if abs(current - previous) < dead_zone:
            stabilized[key] = previous
        else:
            stabilized[key] = previous + alpha * (current - previous)
    return stabilized


def _pose_values(pose: object) -> dict[str, float]:
    if not isinstance(pose, dict):
        return {}
    values = pose.get("values")
    if not isinstance(values, dict):
        return {}
    return {str(key): float(value) for key, value in values.items()}


def _closed_pose_values(poses: dict, axis: AxisConfig) -> dict[str, float]:
    for key in _pose_keys(axis):
        values = _pose_values(poses.get(key))
        if values:
            return values
    return {}


def _pose_keys(axis: AxisConfig) -> tuple[str, ...]:
    if axis.id.endswith("_flex"):
        return (axis.id, axis.id.removesuffix("_flex"))
    return (axis.id,)
