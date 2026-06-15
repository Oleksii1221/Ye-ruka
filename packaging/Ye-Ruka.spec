from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPEC).resolve().parents[1]
src = root / "src"

datas = [
    (str(root / "resources"), "resources"),
    (str(root / "translations"), "translations"),
    (str(root / "config"), "config"),
    (str(root / "models"), "models"),
    (str(root / "firmware"), "firmware"),
    (str(root / "tools" / "espflash"), "tools"),
    (str(root / "LICENSE"), "."),
    (str(root / "THIRD_PARTY_LICENSES.md"), "."),
]
binaries = []
hiddenimports = []


def include_mediapipe_module(name: str) -> bool:
    excluded = (
        ".benchmark",
        ".metadata",
        ".test",
        ".genai.converter",
    )
    return not any(part in name for part in excluded)


mp_datas, mp_binaries, mp_hidden = collect_all(
    "mediapipe",
    filter_submodules=include_mediapipe_module,
)
datas += mp_datas
binaries += mp_binaries
hiddenimports += mp_hidden

a = Analysis(
    [str(src / "ye_ruka" / "main.py")],
    pathex=[str(src)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + ["serial.tools.list_ports_windows", "numpy", "cv2"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Ye-Ruka",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(root / "resources" / "icons" / "ye-ruka.ico"),
    version=str(root / "packaging" / "version_info.txt"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="Ye-Ruka",
)
