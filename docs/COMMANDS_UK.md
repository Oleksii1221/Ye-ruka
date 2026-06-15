# Команди проєкту

Усі локальні команди об'єднані в `tools/project.py` і працюють без BAT-файлів.

```powershell
python tools/project.py setup
python tools/project.py run
python tools/project.py debug
python tools/project.py check
python tools/project.py clean
python tools/project.py build-exe
python tools/project.py portable
python tools/project.py installer
python tools/project.py release
python tools/project.py reset-settings
```

`setup` створює `.venv`, встановлює залежності, завантажує модель MediaPipe та запускає тести. `release` формує EXE, portable ZIP, інсталятор і SHA-256. Для інсталятора потрібен Inno Setup 6.
