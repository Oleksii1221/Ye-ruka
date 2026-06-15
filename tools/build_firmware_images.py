from __future__ import annotations

import subprocess
import sys
from pathlib import Path


OFFSETS = (
    ("0x1000", "bootloader.bin"),
    ("0x8000", "partitions.bin"),
    ("0xe000", "boot_app0.bin"),
    ("0x10000", "firmware.bin"),
)


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "firmware"
    for mode in ("production", "calibration"):
        bundle = root / mode
        arguments = [
            sys.executable,
            "-m",
            "esptool",
            "--chip",
            "esp32",
            "merge_bin",
            "-o",
            str(bundle / "merged.bin"),
            "--flash_mode",
            "dio",
            "--flash_freq",
            "40m",
            "--flash_size",
            "4MB",
        ]
        for offset, filename in OFFSETS:
            path = bundle / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            arguments.extend((offset, str(path)))
        subprocess.run(arguments, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
