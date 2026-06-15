import json
from pathlib import Path

from ye_ruka.core.gestures import built_in_gestures
from ye_ruka.core.models import AxisConfig


def calibrated_axes():
    path = Path(__file__).resolve().parents[1] / "config" / "default_profile.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return [AxisConfig(**raw) for raw in data["axes"]]


def test_requested_gestures_use_calibrated_endpoints():
    gestures = {gesture.name: gesture for gesture in built_in_gestures(calibrated_axes())}

    assert gestures["Розжим"].values["little_flex"] == -45
    assert gestures["Зжим"].values["ring_flex"] == -65
    assert gestures["Лайк"].values["thumb_flex"] == 80
    assert gestures["Лайк"].values["index_flex"] == 90
    assert gestures["Коза"].values["index_flex"] == -50
    assert gestures["Коза"].values["little_flex"] == -45
    assert gestures["Шака"].values["thumb_flex"] == 80
    assert gestures["Шака"].values["little_flex"] == -45
    assert all(gesture.values["thumb_base_flex"] == 50 for gesture in gestures.values())
