from pathlib import Path

import pytest

from ye_ruka.firmware.service import flash_arguments


def test_flash_arguments_include_complete_esp32_image(tmp_path: Path):
    image = tmp_path / "merged.bin"
    image.write_bytes(b"test")

    arguments = flash_arguments("COM42", tmp_path)

    assert arguments[:4] == ["--skip-update-check", "write-bin", "--port", "COM42"]
    assert "--non-interactive" in arguments
    assert arguments[-2:] == ["0x0", str(image)]


def test_flash_arguments_reject_incomplete_bundle(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        flash_arguments("COM42", tmp_path)


def test_release_contains_both_firmware_modes():
    root = Path(__file__).resolve().parents[1] / "firmware"
    for mode in ("production", "calibration"):
        path = root / mode / "merged.bin"
        assert path.is_file()
        assert path.stat().st_size > 0
