from __future__ import annotations

import math
from typing import Iterable

import numpy as np


FINGERS = {
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "little": (17, 18, 19, 20),
}


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    first = a - b
    second = c - b
    denominator = np.linalg.norm(first) * np.linalg.norm(second)
    if denominator < 1e-9:
        return 180.0
    cosine = float(np.clip(np.dot(first, second) / denominator, -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def _normalized_bend(angle: float, maximum_bend: float = 120.0) -> float:
    return float(np.clip((180.0 - angle) / maximum_bend, 0.0, 1.0))


def _finger_flex(points: np.ndarray, indices: tuple[int, int, int, int], palm_normal: np.ndarray) -> float:
    mcp, pip, dip, tip = indices
    proximal = points[pip] - points[mcp]
    proximal_norm = np.linalg.norm(proximal)
    mcp_bend = 0.0 if proximal_norm < 1e-9 else abs(float(np.dot(proximal / proximal_norm, palm_normal)))
    pip_bend = _normalized_bend(_angle(points[mcp], points[pip], points[dip]), 120.0)
    dip_bend = _normalized_bend(_angle(points[pip], points[dip], points[tip]), 100.0)
    return float(np.clip(0.25 * mcp_bend + 0.5 * pip_bend + 0.25 * dip_bend, 0.0, 1.0))


def compute_hand_values(landmarks: Iterable[Iterable[float]]) -> dict[str, float]:
    points = np.asarray(list(landmarks), dtype=np.float64)
    if points.shape != (21, 3):
        raise ValueError("Потрібно рівно 21 тривимірний орієнтир")
    palm_width = float(np.linalg.norm(points[5] - points[17]))
    palm_width = max(palm_width, 1e-6)
    palm_x = points[5] - points[17]
    palm_y = points[9] - points[0]
    normal = np.cross(palm_x, palm_y)
    normal_norm = np.linalg.norm(normal)
    if normal_norm > 1e-9:
        normal /= normal_norm
    values = {f"{name}_flex": _finger_flex(points, indices, normal) for name, indices in FINGERS.items()}
    thumb_mcp, thumb_ip, thumb_tip = points[2], points[3], points[4]
    thumb_base_flex = _normalized_bend(_angle(points[0], points[1], thumb_mcp), 85.0)
    thumb_flex = 0.45 * _normalized_bend(_angle(points[1], thumb_mcp, thumb_ip), 95.0)
    thumb_flex += 0.55 * _normalized_bend(_angle(thumb_mcp, thumb_ip, thumb_tip), 95.0)
    index_base_distance = np.linalg.norm(thumb_tip - points[5]) / palm_width
    opposition = float(np.clip(1.2 - index_base_distance, 0.0, 1.0))
    thumb_depth = abs(float(np.dot(thumb_tip - points[2], normal))) / palm_width
    opposition = float(np.clip(0.75 * opposition + 0.25 * min(1.0, thumb_depth * 3.0), 0.0, 1.0))
    finger_vectors = []
    for indices in FINGERS.values():
        base, _, _, tip = indices
        vector = points[tip] - points[base]
        vector -= normal * np.dot(vector, normal)
        norm = np.linalg.norm(vector)
        if norm > 1e-9:
            finger_vectors.append(vector / norm)
    spreads = []
    for first, second in zip(finger_vectors, finger_vectors[1:]):
        cosine = np.clip(np.dot(first, second), -1.0, 1.0)
        spreads.append(math.degrees(math.acos(float(cosine))))
    spread = float(np.clip((sum(spreads) / max(1, len(spreads)) - 4.0) / 20.0, 0.0, 1.0))
    palm_roll = math.degrees(math.atan2(float(palm_x[1]), float(palm_x[0])))
    palm_pitch = math.degrees(math.atan2(float(palm_y[2]), math.hypot(float(palm_y[0]), float(palm_y[1]))))
    values.update({
        "thumb_flex": float(np.clip(thumb_flex, 0.0, 1.0)),
        "thumb_base_flex": float(np.clip(thumb_base_flex, 0.0, 1.0)),
        "thumb_opposition": opposition,
        "finger_spread": spread,
        "wrist_flex": float(np.clip((palm_pitch + 60.0) / 120.0, 0.0, 1.0)),
        "wrist_deviation": float(np.clip((palm_roll + 90.0) / 180.0, 0.0, 1.0)),
        "wrist_rotation": 0.5,
    })
    return values
