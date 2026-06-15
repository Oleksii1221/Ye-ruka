import pytest

from ye_ruka.core.models import AxisConfig
from ye_ruka.core.tracking_calibration import apply_pose_calibration, stabilize_tracking_values


def test_pose_calibration_maps_open_and_closed_range():
    axes = [AxisConfig("index_flex", "Вказівний", "Index", 0, 0, source="index_flex")]
    calibration = {
        "poses": {
            "open": {"values": {"index_flex": 0.2}},
            "index_flex": {"values": {"index_flex": 0.8}},
        }
    }

    values = apply_pose_calibration({"index_flex": 0.5}, axes, calibration)

    assert values["index_flex"] == pytest.approx(0.5)


def test_tracking_stabilization_holds_dead_zone_jitter():
    values = stabilize_tracking_values(
        {"index_flex": 0.51},
        {"index_flex": 0.5},
        smoothing=0.6,
        dead_zone=0.02,
    )

    assert values["index_flex"] == 0.5


def test_pose_calibration_uses_finger_aliases():
    axes = [AxisConfig("index_flex", "Вказівний", "Index", 0, 0, source="index_flex")]
    calibration = {
        "poses": {
            "open": {"values": {"index_flex": 0.2}},
            "index": {"values": {"index_flex": 0.8}},
        }
    }

    values = apply_pose_calibration({"index_flex": 0.5}, axes, calibration)

    assert values["index_flex"] == pytest.approx(0.5)


def test_pose_calibration_falls_back_to_fist_for_non_isolated_fingers():
    axes = [AxisConfig("ring_flex", "Безіменний", "Ring", 0, 0, source="ring_flex")]
    calibration = {
        "poses": {
            "open": {"values": {"ring_flex": 0.25}},
            "fist": {"values": {"ring_flex": 0.75}},
        }
    }

    values = apply_pose_calibration({"ring_flex": 0.5}, axes, calibration)

    assert values["ring_flex"] == pytest.approx(0.5)
