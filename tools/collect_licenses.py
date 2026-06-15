from __future__ import annotations

import importlib.metadata
import shutil
from pathlib import Path

PACKAGES = [
    "PySide6",
    "shiboken6",
    "opencv-python",
    "mediapipe",
    "numpy",
    "pyserial",
    "platformdirs",
    "PyInstaller",
    "Pillow",
]
NAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "COPYING.txt", "NOTICE", "NOTICE.txt")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "dist" / "Ye-Ruka" / "licenses"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "THIRD_PARTY_LICENSES.md", target / "THIRD_PARTY_LICENSES.md")
    for name in ("LICENSE-MIT", "LICENSE-APACHE", "VERSION.txt"):
        source = root / "tools" / "espflash" / name
        if source.is_file():
            shutil.copy2(source, target / f"espflash-{name}")
    for package in PACKAGES:
        try:
            distribution = importlib.metadata.distribution(package)
        except importlib.metadata.PackageNotFoundError:
            continue
        package_dir = Path(distribution.locate_file(""))
        copied = False
        for name in NAMES:
            candidates = list(package_dir.glob(name)) + list(package_dir.glob(f"*/{name}"))
            for source in candidates[:5]:
                if source.is_file():
                    destination = target / f"{package}-{source.name}"
                    shutil.copy2(source, destination)
                    copied = True
        if not copied:
            metadata = distribution.metadata
            text = f"Package: {package}\nVersion: {distribution.version}\nLicense: {metadata.get('License', 'See package metadata')}\n"
            (target / f"{package}-METADATA.txt").write_text(text, encoding="utf-8")
    print(f"Licenses collected in {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
