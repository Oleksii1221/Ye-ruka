from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tomllib
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
VENV_PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(*args: str | Path, env: dict[str, str] | None = None) -> None:
    command = [str(arg) for arg in args]
    print("+", subprocess.list2cmdline(command))
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as source:
        return tomllib.load(source)["project"]["version"]


def require_venv() -> Path:
    if not VENV_PYTHON.is_file():
        raise SystemExit("Virtual environment is missing. Run: python tools/project.py setup")
    return VENV_PYTHON


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def clean() -> None:
    for path in (ROOT / "build", ROOT / "dist", ROOT / ".pytest_cache"):
        remove_path(path)
    for path in ROOT.rglob("__pycache__"):
        remove_path(path)
    for path in ROOT.rglob("*.pyc"):
        remove_path(path)
    print("Build artifacts removed.")


def setup() -> None:
    if sys.version_info[:2] != (3, 11):
        raise SystemExit("Python 3.11 x64 is required for the development environment.")
    if not VENV_PYTHON.is_file():
        run(sys.executable, "-m", "venv", VENV)
    run(VENV_PYTHON, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    run(VENV_PYTHON, "-m", "pip", "install", "-e", ".[build,test]")
    run(VENV_PYTHON, ROOT / "tools/download_models.py")
    check()


def check() -> None:
    python = require_venv()
    run(python, "-m", "compileall", "-q", "src", "tests", "tools")
    run(python, "-m", "pytest")
    required = (
        "AGENTS.md",
        "ARCHITECTURE.md",
        "LICENSE",
        "README.md",
        "SECURITY.md",
        "pyproject.toml",
    )
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(f"Required repository files are missing: {', '.join(missing)}")
    print("Repository checks passed.")


def copy_distribution_docs() -> None:
    target = ROOT / "dist/Ye-Ruka"
    for directory in ("docs", "examples"):
        shutil.copytree(ROOT / directory, target / directory, dirs_exist_ok=True)
    files = (
        "README.md",
        "README_EN.md",
        "LICENSE",
        "MODEL_NOTICE.md",
        "packaging/EULA_UK.txt",
        "packaging/PRIVACY_POLICY_UK.txt",
        "packaging/SAFETY_NOTICE_UK.txt",
    )
    for relative in files:
        shutil.copy2(ROOT / relative, target / Path(relative).name)


def build_app() -> None:
    python = require_venv()
    run(python, ROOT / "tools/download_models.py")
    run(python, ROOT / "tools/download_espflash.py")
    run(python, ROOT / "tools/build_firmware_images.py")
    check()
    clean()
    run(python, "-m", "PyInstaller", "--noconfirm", "--clean", "packaging/Ye-Ruka.spec")
    copy_distribution_docs()
    run(python, ROOT / "tools/collect_licenses.py")
    executable = ROOT / "dist/Ye-Ruka" / ("Ye-Ruka.exe" if os.name == "nt" else "Ye-Ruka")
    print(f"Application: {executable}")


def build_exe() -> None:
    build_app()


def create_portable() -> None:
    source = ROOT / "dist/Ye-Ruka/Ye-Ruka.exe"
    if not source.is_file():
        raise SystemExit("Application build not found. Run build-exe first.")
    release = ROOT / "dist/release"
    release.mkdir(parents=True, exist_ok=True)
    archive = release / f"Ye-Ruka-{version()}-Windows-x64-portable.zip"
    remove_path(archive)
    shutil.make_archive(str(archive.with_suffix("")), "zip", ROOT / "dist", "Ye-Ruka")
    print(f"Portable archive: {archive}")


def create_linux_archive() -> None:
    source = ROOT / "dist/Ye-Ruka/Ye-Ruka"
    if not source.is_file():
        raise SystemExit("Linux application build not found. Run build-app first on Linux.")
    release = ROOT / "dist/release"
    release.mkdir(parents=True, exist_ok=True)
    package_root = ROOT / "dist/Ye-Ruka"
    launcher = package_root / "start-ye-ruka.sh"
    launcher.write_text(
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        "APP_DIR=$(CDPATH= cd -- \"$(dirname -- \"$0\")\" && pwd)\n"
        "exec \"$APP_DIR/Ye-Ruka\" \"$@\"\n",
        encoding="utf-8",
    )
    desktop = package_root / "ye-ruka.desktop"
    desktop.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Є-Рука\n"
        "Comment=Robotic hand controller by Kico\n"
        "Exec=sh -c '\"$(dirname \"%k\")/start-ye-ruka.sh\"'\n"
        "Icon=ye-ruka\n"
        "Terminal=false\n"
        "Categories=Utility;Education;Science;\n",
        encoding="utf-8",
    )
    for executable in (source, launcher):
        mode = executable.stat().st_mode
        executable.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    archive_base = release / f"Ye-Ruka-{version()}-Ubuntu-x64"
    archive = archive_base.with_suffix(".tar.gz")
    remove_path(archive)
    shutil.make_archive(str(archive_base), "gztar", ROOT / "dist", "Ye-Ruka")
    print(f"Ubuntu archive: {archive}")


def find_inno_setup() -> Path:
    candidates = [
        shutil.which("ISCC.exe"),
        os.environ.get("ISCC_PATH"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Inno Setup 6/ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6/ISCC.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6/ISCC.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise SystemExit("Inno Setup 6 was not found. Set ISCC_PATH or install Inno Setup 6.")


def build_installer() -> None:
    if not (ROOT / "dist/Ye-Ruka/Ye-Ruka.exe").is_file():
        raise SystemExit("Application build not found. Run build-exe first.")
    python = require_venv()
    (ROOT / "dist/release").mkdir(parents=True, exist_ok=True)
    run(python, ROOT / "tools/create_installer_branding.py")
    run(find_inno_setup(), ROOT / "packaging/Ye-Ruka.iss")


def release() -> None:
    build_app()
    if os.name == "nt":
        create_portable()
        build_installer()
    else:
        create_linux_archive()
    run(require_venv(), ROOT / "tools/write_release_checksums.py")
    print(f"Release: {ROOT / 'dist/release'}")


def launch(debug: bool = False) -> None:
    python = require_venv()
    if debug:
        environment = os.environ.copy()
        environment.update(PYTHONFAULTHANDLER="1", QT_DEBUG_PLUGINS="1")
        run(python, "-X", "dev", "-m", "ye_ruka", env=environment)
    else:
        run(python, "-m", "ye_ruka")


def reset_settings() -> None:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Kico/Ye-Ruka"
    roaming = Path(os.environ.get("APPDATA", Path.home())) / "Kico/Ye-Ruka"
    for path in (local, roaming):
        remove_path(path)
    print("Ye-Ruka settings were reset.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ye-Ruka development and release commands")
    parser.add_argument(
        "command",
        choices=(
            "setup",
            "run",
            "debug",
            "check",
            "clean",
            "build-exe",
            "build-app",
            "portable",
            "linux-archive",
            "installer",
            "release",
            "reset-settings",
        ),
    )
    command = parser.parse_args().command
    actions = {
        "setup": setup,
        "run": launch,
        "debug": lambda: launch(debug=True),
        "check": check,
        "clean": clean,
        "build-exe": build_exe,
        "build-app": build_app,
        "portable": create_portable,
        "linux-archive": create_linux_archive,
        "installer": build_installer,
        "release": release,
        "reset-settings": reset_settings,
    }
    actions[command]()


if __name__ == "__main__":
    main()
