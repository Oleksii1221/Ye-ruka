from __future__ import annotations

import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


VERSION = "4.4.0"
ARCHIVE_URL = (
    f"https://github.com/esp-rs/espflash/releases/download/v{VERSION}/"
    "espflash-x86_64-pc-windows-msvc.zip"
)
ARCHIVE_SHA256 = "18f83af3145a17ea670aa6a60a3a28992cc06c2799ba8b94471598d3658c1f10"
LICENSE_BASE = f"https://raw.githubusercontent.com/esp-rs/espflash/v{VERSION}"


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Ye-Ruka-build"})
    with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as output:
        shutil.copyfileobj(response, output)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "tools" / "espflash"
    executable = target / "espflash.exe"
    if executable.is_file():
        print(f"espflash {VERSION} is already available")
        return 0

    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / "espflash.zip"
        download(ARCHIVE_URL, archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != ARCHIVE_SHA256:
            raise RuntimeError(f"espflash archive hash mismatch: {digest}")
        with zipfile.ZipFile(archive) as package:
            package.extract("espflash.exe", target)

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
