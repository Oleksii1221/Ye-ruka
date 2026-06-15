from __future__ import annotations

from PySide6.QtWidgets import QAbstractButton, QComboBox, QLabel, QLineEdit, QTabWidget, QTableWidget, QWidget


EN = {
    "Є-Рука": "Ye-Ruka",
    "Рукавиця": "Glove",
    "Рух людини — у механіку кисті": "Human motion into hand mechanics",
    "Камера або сенсорна рукавиця формують єдиний потік керування. Є-Рука згладжує, калібрує та безпечно передає його на ESP32.": "A camera or sensor glove creates a unified control stream. Ye-Ruka filters, calibrates and safely sends it to ESP32.",
    "Відкрити камеру": "Open camera",
    "Підключити рукавицю": "Connect glove",
    "Ручний режим": "Manual mode",
    "Перейти до калібрування": "Open calibration",
    "Калібрування руки": "Hand calibration",
    "Передавання не запускається автоматично. Кути DS3225 обмежуються у застосунку та на ESP32.": "Transmission does not start automatically. DS3225 angles are limited in both the app and ESP32 firmware.",
    "Живе зчитування датчиків згину та передавання руху на роботизовану кисть": "Live flex-sensor input and motion transfer to the robotic hand",
    "Підключити рукавицю": "Connect glove",
    "Автовизначення": "Auto detect",
    "Префіксований": "Prefixed",
    "Режим рукавиці активується при відкритті цієї сторінки": "Glove mode is activated when this page is opened",
    "Точне керування кожною віссю та швидкий запуск жестів": "Precise control of every axis and quick gesture launch",
    "Зберегти поточне положення": "Save current position",
    "MediaPipe відстежує кисть, а Є-Рука перетворює анатомічні кути на серво-команди": "MediaPipe tracks the hand while Ye-Ruka converts anatomical angles into servo commands",
    "Оновити список камер": "Refresh camera list",
    "Дзеркальне відображення": "Mirror view",
    "Кисть / Serial": "Hand / Serial",
    "Формат RX": "RX format",
    "Кількість каналів": "Channel count",
    "Глобальний мінімум": "Global minimum",
    "Глобальний максимум": "Global maximum",
    "Згладжування візуалізації": "Visualization smoothing",
    "Відповідність каналів рукавиці осям кисті": "Glove channel to hand axis mapping",
    "Для кожної осі можна задати окремий канал датчика, діапазон та інверсію.": "Each axis can use its own sensor channel, range and inversion.",
    "Зберегти зміни": "Save changes",
    "Керування роботизованою кистю через камеру, сенсорну рукавицю або ручну панель.": "Robotic hand control through a camera, sensor glove or manual panel.",
    "Головна": "Home",
    "Автоматичне керування": "Automatic control",
    "Ручне керування": "Manual control",
    "Ручне керування та жести": "Manual control and gestures",
    "Калібрування": "Calibration",
    "Діагностика": "Diagnostics",
    "Налаштування": "Settings",
    "Керування роботизованою кистю через камеру, ручну панель і Serial": "Robotic hand control through camera, manual panel and Serial",
    "Камера": "Camera",
    "Зупинена": "Stopped",
    "Розпізнавання": "Tracking",
    "Очікування": "Waiting",
    "ESP / COM": "ESP / COM",
    "Відключено": "Disconnected",
    "Передано пакетів": "Packets sent",
    "Канали": "Channels",
    "Швидкий запуск": "Quick start",
    "Ручне керування та жести": "Manual control and gestures",
    "Передавання після запуску завжди вимкнене. До першого руху перевірте межі сервоприводів, інверсію та безпечні положення.": "Transmission is always disabled after startup. Verify servo limits, inversion and safe positions before the first movement.",
    "Запустити камеру": "Start camera",
    "Зупинити": "Stop",
    "Оновити": "Refresh",
    "Камера й трекінг": "Camera and tracking",
    "Роздільна здатність": "Resolution",
    "Бажаний FPS": "Target FPS",
    "Рука": "Hand",
    "Відображення": "View",
    "Дзеркально": "Mirror",
    "Автоматично": "Automatic",
    "Ліва": "Left",
    "Права": "Right",
    "Обробка": "Processing",
    "Впевненість": "Confidence",
    "Розраховані осі": "Calculated axes",
    "Вісь": "Axis",
    "Нормалізовано": "Normalized",
    "Серво": "Servo",
    "Загальне стискання кисті": "Global hand grip",
    "Жести": "Gestures",
    "Застосувати": "Apply",
    "Перейменувати": "Rename",
    "Видалити": "Delete",
    "Зберегти поточне положення": "Save current position",
    "Назва": "Name",
    "Перехід": "Transition",
    "Гаряча клавіша": "Hotkey",
    "Зберегти як жест": "Save as gesture",
    "Механічні межі сервоприводів": "Servo mechanical limits",
    "Перед увімкненням передачі перевірте кожен канал на малих змінах. Значення Safe мають бути безпечними навіть після втрати зв’язку.": "Before enabling transmission, verify each channel using small changes. Safe values must remain safe after communication loss.",
    "Зберегти межі й позначки перевірки": "Save limits and verification marks",
    "Калібрування руки користувача": "User hand calibration",
    "Зафіксувати позу": "Capture pose",
    "Скинути калібрування": "Reset calibration",
    "Рука не знайдена": "Hand not found",
    "Експорт журналу": "Export log",
    "Очистити": "Clear",
    "Трекер": "Tracker",
    "Обробка кадру": "Frame processing",
    "COM-порт": "COM port",
    "Пакетів": "Packets",
    "Помилок": "Errors",
    "Дані обробки": "Processing data",
    "Журнал": "Log",
    "Загальні": "General",
    "Serial": "Serial",
    "Відстеження": "Tracking",
    "Безпека": "Safety",
    "Про програму": "About",
    "Імпорт профілю": "Import profile",
    "Експорт профілю": "Export profile",
    "Скинути": "Reset",
    "Зберегти": "Save",
    "Назва профілю": "Profile name",
    "Тема": "Theme",
    "Мова": "Language",
    "Темна": "Dark",
    "Світла": "Light",
    "Системна": "System",
    "Обслуговування": "Service",
    "Прошивання ESP32, відновлення робочого режиму та сервісна перевірка приводів": "ESP32 flashing, production recovery and servo service testing",
    "ПРОШИВКА КОНТРОЛЕРА": "CONTROLLER FIRMWARE",
    "Готові бінарні прошивки вже входять до програми. Arduino IDE та PlatformIO не потрібні.": "Ready-to-flash firmware is bundled with the app. Arduino IDE and PlatformIO are not required.",
    "Оновити порти": "Refresh ports",
    "Встановити робочу прошивку": "Install production firmware",
    "Встановити сервісну прошивку": "Install service firmware",
    "Готово до роботи": "Ready",
    "СИРИЙ ТЕСТ СЕРВОПРИВОДІВ": "RAW SERVO TEST",
    "Сервісна прошивка обходить кути профілю. Одночасно активна лише одна серва, але механізм може рухнути різко. Тримайте руки поза зоною руху.": "Service firmware bypasses profile angles. Only one servo is active at a time, but the mechanism may move suddenly. Keep hands outside its travel area.",
    "Я розумію ризик і прибрав руки від механізму": "I understand the risk and have cleared the mechanism",
    "Підключити сервісний режим": "Connect service mode",
    "Подати кут": "Apply angle",
    "Центр 0°": "Center 0°",
    "Журнал прошивання та сервісного порту": "Firmware and service-port log",
    "Файли та обслуговування програми": "Application files and maintenance",
    "Відкрити папку програми": "Open application folder",
    "Відкрити папку налаштувань": "Open settings folder",
    "Ліцензія": "License",
    "Конфіденційність": "Privacy",
    "Видалити Є-Рука з комп'ютера": "Uninstall Ye-Ruka",
    "Індекс камери": "Camera index",
    "Швидкість": "Baud rate",
    "Протокол": "Protocol",
    "Частота": "Rate",
    "Автоперепідключення": "Auto reconnect",
    "Захищений YR1 + CRC16": "Protected YR1 + CRC16",
    "Простий масив": "Simple array",
    "Втрата руки": "Hand loss",
    "Утримувати останнє": "Hold last position",
    "Перейти в нейтраль": "Move to neutral",
    "Перейти в безпечне": "Move to safe position",
    "Зупинити передачу": "Stop transmission",
    "Таймаут": "Timeout",
    "Показувати орієнтири": "Show landmarks",
    "Плавний перехід": "Smooth transition",
    "Вимагати перевірені осі": "Require verified axes",
    "Таймаут ESP": "ESP timeout",
    "Настільний застосунок керування роботизованою кистю через ESP32.": "Desktop application for controlling a robotic hand through ESP32.",
    "Власний код: MIT License. Qt/PySide6 та інші залежності мають окремі ліцензії.": "Original code: MIT License. Qt/PySide6 and other dependencies retain their own licenses.",
    "Автор: Kico": "Author: Kico",
    "Підключити": "Connect",
    "Відключити": "Disconnect",
    "Передавання": "Transmission",
    "АВАРІЙНА ЗУПИНКА": "EMERGENCY STOP",
    "Скинути E-STOP": "Reset E-STOP",
    "Камера: —": "Camera: —",
    "Рука: —": "Hand: —",
    "Serial: —": "Serial: —",
    "TX: вимкнено": "TX: disabled",
}


def apply_language(root: QWidget, language: str) -> None:
    widgets = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        if isinstance(widget, (QLabel, QAbstractButton)):
            if widget.property("uk_text") is None:
                widget.setProperty("uk_text", widget.text())
            original = widget.property("uk_text")
            widget.setText(EN.get(original, original) if language == "en" else original)
        if isinstance(widget, QLineEdit):
            if widget.property("uk_placeholder") is None:
                widget.setProperty("uk_placeholder", widget.placeholderText())
            original = widget.property("uk_placeholder")
            widget.setPlaceholderText(EN.get(original, original) if language == "en" else original)
        if isinstance(widget, QComboBox):
            if widget.property("uk_items") is None:
                widget.setProperty("uk_items", [widget.itemText(index) for index in range(widget.count())])
            originals = widget.property("uk_items") or []
            for index, original in enumerate(originals):
                if index < widget.count():
                    widget.setItemText(index, EN.get(original, original) if language == "en" else original)
        if isinstance(widget, QTabWidget):
            if widget.property("uk_tabs") is None:
                widget.setProperty("uk_tabs", [widget.tabText(index) for index in range(widget.count())])
            originals = widget.property("uk_tabs") or []
            for index, original in enumerate(originals):
                widget.setTabText(index, EN.get(original, original) if language == "en" else original)
        if isinstance(widget, QTableWidget):
            if widget.property("uk_headers") is None:
                widget.setProperty("uk_headers", [widget.horizontalHeaderItem(index).text() if widget.horizontalHeaderItem(index) else "" for index in range(widget.columnCount())])
            originals = widget.property("uk_headers") or []
            for index, original in enumerate(originals):
                item = widget.horizontalHeaderItem(index)
                if item:
                    item.setText(EN.get(original, original) if language == "en" else original)
