from __future__ import annotations

from .models import AxisConfig, Gesture


def built_in_gestures(axes: list[AxisConfig]) -> list[Gesture]:
    ids = {axis.id for axis in axes}

    def values(**normalized: float) -> dict[str, int]:
        result: dict[str, int] = {}
        for axis in axes:
            if not axis.enabled:
                result[axis.id] = axis.safe_angle
                continue
            amount = normalized.get(axis.id, 0.0)
            result[axis.id] = axis.map_normalized(amount)
        return result

    gestures = [
        Gesture("Розжим", values(), 700, builtin=True),
        Gesture("Зжим", values(**{axis.id: 1.0 for axis in axes if axis.grip}), 850, builtin=True),
        Gesture("Нейтраль", {axis.id: axis.neutral_angle for axis in axes}, 600, builtin=True),
    ]
    if {"thumb_flex", "thumb_opposition", "index_flex"}.issubset(ids):
        gestures.append(Gesture("Щипкове захоплення", values(thumb_flex=0.8, thumb_base_flex=0.7, thumb_opposition=1.0, index_flex=0.8, middle_flex=0.15, ring_flex=0.15, little_flex=0.15), 700, builtin=True))
        gestures.append(Gesture("OK", values(thumb_flex=0.8, thumb_base_flex=0.65, thumb_opposition=1.0, index_flex=0.85, middle_flex=0.05, ring_flex=0.05, little_flex=0.05), 750, builtin=True))
    if "index_flex" in ids:
        gestures.append(Gesture("Вказівний жест", values(index_flex=0.0, middle_flex=1.0, ring_flex=1.0, little_flex=1.0, thumb_flex=0.55, thumb_base_flex=0.45, thumb_opposition=0.65), 750, builtin=True))
    if {"index_flex", "middle_flex"}.issubset(ids):
        gestures.append(Gesture("V", values(index_flex=0.0, middle_flex=0.0, ring_flex=1.0, little_flex=1.0, thumb_flex=0.6, thumb_base_flex=0.45, thumb_opposition=0.65), 750, builtin=True))
    if {"thumb_flex", "index_flex", "middle_flex", "ring_flex", "little_flex"}.issubset(ids):
        gestures.append(Gesture("Лайк", values(thumb_flex=0.0, thumb_opposition=0.0, index_flex=1.0, middle_flex=1.0, ring_flex=1.0, little_flex=1.0), 850, builtin=True))
        gestures.append(Gesture("Коза", values(thumb_flex=1.0, thumb_opposition=1.0, index_flex=0.0, middle_flex=1.0, ring_flex=1.0, little_flex=0.0), 850, builtin=True))
        gestures.append(Gesture("Шака", values(thumb_flex=0.0, thumb_opposition=0.0, index_flex=1.0, middle_flex=1.0, ring_flex=1.0, little_flex=0.0), 850, builtin=True))
    return gestures
