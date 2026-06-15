from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "models" / "hand_landmarker.task"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1_000_000:
        print(f"Model already exists: {target}")
        return 0
    temp = target.with_suffix(".download")
    try:
        print(f"Downloading MediaPipe Hand Landmarker model to {target}")
        urllib.request.urlretrieve(URL, temp)
        if temp.stat().st_size < 1_000_000:
            raise RuntimeError("Downloaded model is unexpectedly small")
        temp.replace(target)
        print("Model downloaded successfully")
        return 0
    except Exception as exc:
        temp.unlink(missing_ok=True)
        print(f"Model download failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
