# Architecture

## Data sources

Є-Рука has three mutually selected command sources:

1. Camera: OpenCV frame capture → MediaPipe landmarks → kinematics → normalized axes.
2. Sensor glove: independent COM port → line parser → per-axis calibration → normalized axes.
3. Manual mode: sliders, global grip, and gestures.

All sources converge in `ApplicationController`, which maps values to configured axes, applies filters and safety limits, and publishes the latest target state.

## Output path

`ApplicationController` → ordered axis values → `SerialProtocol` → `SerialThread` → robotic-hand controller.

The GUI thread never performs blocking camera or Serial work. Camera, glove Serial, and robot Serial use separate workers and communicate with Qt signals.

## Configuration

`ConfigManager` stores the user profile under the platform-specific application configuration directory. `config/default_profile.json` is the bundled recovery profile. Schema migrations must be backward-compatible and validated before replacing the active file.

## Safety boundary

The desktop app clamps and rate-limits commands. The ESP32 example independently validates packet framing, channel count, CRC, ranges, and connection timeout. Neither side should rely exclusively on the other for safe behavior.

## UI

`MainWindow` owns the frameless shell, navigation, robot-link command bar, global E-STOP, stacked pages, and status strip. Pages own only their local controls and workers. Dense pages use scroll areas or splitters so widgets are never compressed into unreadable geometry.
