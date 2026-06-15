from __future__ import annotations

import hashlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "dist" / "release"
CHECKSUM_FILE = RELEASE_DIR / os.environ.get("RELEASE_CHECKSUM_FILE", "SHA256SUMS.txt")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    artifacts = []
    for path in sorted(RELEASE_DIR.iterdir()):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.endswith((".exe", ".zip", ".tar.gz")):
            artifacts.append(path)
    if not artifacts:
        raise SystemExit(f"No release artifacts found in {RELEASE_DIR}")

    lines = [f"{sha256(path)} *{path.name}" for path in artifacts]
    CHECKSUM_FILE.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"Checksums: {CHECKSUM_FILE}")


if __name__ == "__main__":
    main()
