from ye_ruka.core.models import AxisConfig


def axis(inverted=False):
    return AxisConfig("x", "Вісь", "Axis", 0, 0, 10, 170, 90, 90, inverted)


def test_map_normalized():
    item = axis()
    assert item.map_normalized(0.0) == 10
    assert item.map_normalized(0.5) == 90
    assert item.map_normalized(1.0) == 170


def test_inversion():
    item = axis(True)
    assert item.map_normalized(0.0) == 170
    assert item.map_normalized(1.0) == 10


def test_clamp():
    item = axis()
    assert item.clamp(-200) == 10
    assert item.clamp(999) == 170


def test_glove_normalization():
    item = AxisConfig("g", "G", "G", 0, 0, glove_channel=0, glove_min=100.0, glove_max=1100.0)
    assert item.normalize_glove(100.0) == 0.0
    assert item.normalize_glove(600.0) == 0.5
    assert item.normalize_glove(1100.0) == 1.0
