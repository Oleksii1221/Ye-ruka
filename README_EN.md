# Ye-Ruka

Ye-Ruka is a Windows application for controlling a seven-servo robotic hand through an ESP32, camera-based gestures, manual controls, or a sensor glove.

**[Download the latest release](https://github.com/Oleksii1221/Ye-ruka/releases/latest)** · **[Project website](https://oleksii1221.github.io/Ye-ruka/)**

## Highlights

- MediaPipe camera hand tracking and gesture control;
- manual controls and configurable gesture presets;
- independent sensor-glove COM connection;
- built-in production and service firmware flashing for ESP32;
- guarded raw DS3225 testing from `-90°` to `+90°`;
- Ukrainian and English UI with system, dark, and light themes;
- Windows installer, portable archive, uninstaller, and desktop shortcut.

## Development

Python 3.11 x64 is required.

```powershell
python tools/project.py setup
python tools/project.py run
python tools/project.py check
```

`master` contains stable releases. Active development happens on `dev`. See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete workflow.

## License

Original source code is available under the [MIT License](LICENSE). Third-party components retain their own licenses; see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
