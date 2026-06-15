import json
from pathlib import Path

from ye_ruka.core.config import ConfigManager


def test_default_profile_valid():
    path = Path(__file__).resolve().parents[1] / "config" / "default_profile.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ConfigManager.validate(data)
    assert len(data["axes"]) == 7
    assert data["schema_version"] == 4
    assert data["glove"]["channel_count"] == 7
    assert [axis["id"] for axis in data["axes"]] == [
        "little_flex",
        "ring_flex",
        "middle_flex",
        "index_flex",
        "thumb_flex",
        "thumb_opposition",
        "thumb_base_flex",
    ]
    assert [axis["safe_angle"] for axis in data["axes"]] == [-45, 70, -40, -50, 80, 50, 50]


def test_thumb_base_axis_migration_is_safe_for_existing_profiles():
    path = Path(__file__).resolve().parents[1] / "config" / "default_profile.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema_version"] = 2
    data["axes"] = [axis for axis in data["axes"] if axis["id"] != "thumb_base_flex"]
    data["glove"]["channel_count"] = 6

    assert ConfigManager._add_thumb_base_axis(data)

    added = next(axis for axis in data["axes"] if axis["id"] == "thumb_base_flex")
    assert not added["enabled"]
    assert not added["verified"]
    assert data["glove"]["channel_count"] >= added["glove_channel"] + 1


def test_schema_three_profile_migrates_to_calibrated_hand(tmp_path):
    path = Path(__file__).resolve().parents[1] / "config" / "default_profile.json"
    old = json.loads(path.read_text(encoding="utf-8"))
    old["schema_version"] = 3
    old["axes"] = list(reversed(old["axes"]))
    old_path = tmp_path / "profile.json"
    old_path.write_text(json.dumps(old), encoding="utf-8")

    manager = ConfigManager(path, app_name="Ye-Ruka-Test")
    manager.root = tmp_path
    manager.path = old_path
    manager.backup_dir = tmp_path / "backups"
    manager.backup_dir.mkdir()
    data = manager.load()

    assert data["schema_version"] == 4
    assert data["axes"][0]["id"] == "little_flex"
    assert data["axes"][6]["safe_angle"] == 50
