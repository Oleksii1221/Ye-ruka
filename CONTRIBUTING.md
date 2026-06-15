# Contributing to Ye-Ruka

Thank you for helping improve Ye-Ruka. Hardware-control changes require the same care as application code because an incorrect value can damage a mechanism or servo.

## Branch workflow

1. Start from `dev`.
2. Create a focused branch such as `feature/gesture-editor` or `fix/serial-reconnect`.
3. Keep commits small and descriptive.
4. Open a pull request into `dev`.
5. Run the checks and describe any hardware validation that was not performed.

Only release pull requests are merged from `dev` into `master`. Do not push feature work directly to `master`.

## Local setup

```powershell
python tools/project.py setup
python tools/project.py check
python tools/project.py run
```

For UI changes, verify Ukrainian and English plus system, dark, and light themes. For servo or protocol changes, begin with transmission disabled and document the exact ESP32, power source, servo model, and mechanical load used.

## Pull requests

Explain:

- the user-facing goal;
- the implementation and affected modules;
- automated tests and manual checks;
- camera, glove, ESP32, and powered-servo tests performed or skipped;
- configuration, protocol, safety, or migration impact.

By contributing, you agree that your contribution is licensed under the project's MIT License.
