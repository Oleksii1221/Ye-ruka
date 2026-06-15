from __future__ import annotations

from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from ye_ruka.core.kinematics import compute_hand_values
from ye_ruka.core.models import TrackingResult


CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)


class HandTracker:
    def __init__(
        self,
        model_path: Path,
        detection_confidence: float = 0.55,
        tracking_confidence: float = 0.55,
    ) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Не знайдено модель: {model_path}")
        base = mp.tasks.BaseOptions(model_asset_path=str(model_path))
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

    def close(self) -> None:
        self.landmarker.close()

    def process(self, frame_bgr: np.ndarray, timestamp_ms: int, hand_preference: str = "auto") -> TrackingResult:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.landmarker.detect_for_video(image, timestamp_ms)
        if not result.hand_landmarks:
            return TrackingResult(False, timestamp_ms=timestamp_ms)
        candidates: list[tuple[int, str, float]] = []
        for index, categories in enumerate(result.handedness):
            category = categories[0]
            label = category.category_name.lower()
            candidates.append((index, label, float(category.score)))
        selected = max(candidates, key=lambda item: item[2])
        if hand_preference in {"left", "right"}:
            matching = [item for item in candidates if item[1] == hand_preference]
            if matching:
                selected = max(matching, key=lambda item: item[2])
            else:
                return TrackingResult(False, timestamp_ms=timestamp_ms)
        index, handedness, confidence = selected
        world = result.hand_world_landmarks[index] if result.hand_world_landmarks else result.hand_landmarks[index]
        world_points = [[float(point.x), float(point.y), float(point.z)] for point in world]
        image_points = [[float(point.x), float(point.y), float(point.z)] for point in result.hand_landmarks[index]]
        values = compute_hand_values(world_points)
        return TrackingResult(
            detected=True,
            handedness=handedness,
            confidence=confidence,
            raw_values=values,
            landmarks=image_points,
            timestamp_ms=timestamp_ms,
        )

    @staticmethod
    def draw(frame: np.ndarray, tracking: TrackingResult) -> np.ndarray:
        if not tracking.detected or len(tracking.landmarks) != 21:
            return frame
        height, width = frame.shape[:2]
        points = [(int(item[0] * width), int(item[1] * height)) for item in tracking.landmarks]
        for first, second in CONNECTIONS:
            cv2.line(frame, points[first], points[second], (43, 203, 255), 2, cv2.LINE_AA)
        for point in points:
            cv2.circle(frame, point, 4, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, point, 5, (43, 203, 255), 1, cv2.LINE_AA)
        return frame
