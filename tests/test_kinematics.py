import numpy as np

from ye_ruka.core.kinematics import compute_hand_values


def straight_hand():
    points = np.zeros((21, 3), dtype=float)
    points[0] = [0.0, 0.0, 0.0]
    points[1:5] = [[-0.25, 0.15, 0], [-0.35, 0.25, 0], [-0.45, 0.35, 0], [-0.55, 0.45, 0]]
    for base, x in ((5, -0.2), (9, 0.0), (13, 0.2), (17, 0.4)):
        points[base] = [x, 0.25, 0]
        points[base + 1] = [x, 0.5, 0]
        points[base + 2] = [x, 0.75, 0]
        points[base + 3] = [x, 1.0, 0]
    return points


def test_straight_fingers_are_open():
    values = compute_hand_values(straight_hand())
    assert values["index_flex"] < 0.05
    assert values["middle_flex"] < 0.05
    assert "thumb_base_flex" in values
    assert all(0.0 <= value <= 1.0 for value in values.values())
