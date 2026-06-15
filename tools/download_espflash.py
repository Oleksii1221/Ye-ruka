from __future__ import annotations

import hashlib
import os
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


VERSION = "4.4.0"
ARCHIVES = {
    "win32": {
        "name": "espflash-x86_64-pc-windows-msvc.zip",
        "sha256": "18f83af3145a17ea670aa6a60a3a28992cc06c2799ba8b94471598d3658c1f10",
        "executable": "espflash.exe",
    },
    "linux": {
        "name": "espflash-x86_64-unknown-linux-gnu.zip",
        "sha256": "ac2031bd1f04c9107d9ba0e977535daa885a9f533f937dc369debd77f83665cd",
        "executable": "espflash",
    },
}
LICENSE_BASE = f"https://raw.githubusercontent.com/esp-rs/espflash/v{VERSION}"


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Ye-Ruka-build"})
    with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as output:
        shutil.copyfileobj(response, output)


def platform_archive() -> dict[str, str]:
    if sys.platform.startswith("linux"):
        return ARCHIVES["linux"]
    if sys.platform == "win32":
        return ARCHIVES["win32"]
    raise SystemExit(f"Unsupported espflash build platform: {sys.platform}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "tools" / "espflash"
    archive_info = platform_archive()
    executable = target / archive_info["executable"]
    if executable.is_file():
        print(f"espflash {VERSION} is already available")
        return 0

    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / "espflash.zip"
        archive_url = (
            f"https://github.com/esp-rs/espflash/releases/download/v{VERSION}/"
            f"{archive_info['name']}"
        )
        download(archive_url, archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != archive_info["sha256"]:
            raise RuntimeError(f"espflash archive hash mismatch: {digest}")
        with zipfile.ZipFile(archive) as package:
            package.extract(archive_info["executable"], target)
    if os.name != "nt":
        mode = executable.stat().st_mode
        executable.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    download(f"{LICENSE_BASE}/LICENSE-MIT", target / "LICENSE-MIT")
    download(f"{LICENSE_BASE}/LICENSE-APACHE", target / "LICENSE-APACHE")
    (target / "VERSION.txt").write_text(
        f"espflash {VERSION}\nhttps://github.com/esp-rs/espflash\n",
        encoding="ascii",
    )
    print(f"Downloaded espflash {VERSION} to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
