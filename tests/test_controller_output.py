from types import SimpleNamespace

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.models import AxisConfig, Gesture


def test_disabled_axis_keeps_output_channel_count_with_safe_angle():
    axes = [
        AxisConfig("a", "A", "A", 0, 0, neutral_angle=90, safe_angle=10, enabled=True),
        AxisConfig("b", "B", "B", 1, 1, neutral_angle=90, safe_angle=20, enabled=False),
    ]
    controller = SimpleNamespace(axes=axes, current_values={"a": 111, "b": 122})

    assert ApplicationController.ordered_values(controller) == [111, 20]


def test_gesture_switches_to_manual_mode_before_transition():
    events = []
    controller = SimpleNamespace(
        set_mode=lambda mode: events.append(("mode", mode)),
        start_transition=lambda values, duration: events.append(("transition", values, duration)),
        toast=SimpleNamespace(emit=lambda level, message: events.append(("toast", level, message))),
    )
    gesture = Gesture("Test", {"a": 42}, 500)

    ApplicationController.apply_gesture(controller, gesture)

    assert events == [
        ("mode", "manual"),
        ("transition", {"a": 42}, 500),
        ("toast", "success", "Жест: Test"),
    ]
