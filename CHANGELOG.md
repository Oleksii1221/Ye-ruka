# Changelog

## 2.2.1 — 2026-06-16

- Added Ubuntu x64 release packaging as a `.tar.gz` archive with launcher and desktop metadata.
- Added Linux `espflash` bundling so ESP32 firmware installation works in Ubuntu builds.
- Updated GitHub release automation to publish Windows and Ubuntu artifacts.
- Updated the website with separate direct download buttons for Windows and Ubuntu.

## 2.2.0 — 2026-06-15

- Added a dedicated Service page for ESP32 firmware installation and recovery.
- Bundled production and calibration firmware images; Arduino IDE and PlatformIO are not required on the target PC.
- Added a guarded raw DS3225 test mode for one servo at a time with explicit OFF control.
- Added System theme support, application/configuration folder actions, privacy and license access, and in-app uninstall.
- Expanded Ukrainian and English interface coverage for maintenance workflows.
- Added a public project website, polished repository documentation, support/security/privacy policies, and issue templates.
- Replaced Windows BAT helpers with a cross-platform Python command tool and automated CI, Pages, and release workflows.
- Established `dev` for active development and protected `master` for stable releases.

## Unreleased

- стандартний профіль переведено на фізичний порядок серв 1–7 і калібровані підписані кути DS3225;
- прибрано редактор механічних меж: обмеження тепер однаково зашиті у профіль застосунку та ESP32;
- додано жести «Розжим», «Зжим», «Лайк», «Коза» та «Шака»;
- сьомий канал згину великого пальця до долоні зафіксовано на 50°;
- ESP32-прошивку переведено на `1500 + angle × 11.111 мкс` і 50 Гц.
- додано стабілізацію значень камери до мапінгу в серви: EMA та поріг дребезгу налаштовуються у вкладці «Відстеження»;
- калібрування пози руки тепер зберігає медіану з 12 кадрів замість одного кадру;
- збережені пози open/fist/окремих пальців використовуються для нормалізації згинання пальців у camera mode.
- на сторінку калібрування додано live-preview камери;
- окремі пози пальців тепер є уточненнями, а для пальців, які не згинаються ізольовано, використовується fallback на позу «кулак».
- додано popup Serial Terminal по `F12` для перегляду повідомлень від мікроконтролерів і Serial-подій.
- стандартну частоту TX збільшено до 60 Гц, максимальну частоту в налаштуваннях — до 200 Гц;
- додано baudrate `1000000` і `2000000`, а Serial worker прибрано з 10-мс циклу очікування під час активного TX.

## 2.1.0 — 2026-06-06

- перероблено сторінку камери: права панель більше не стискає і не обрізає елементи;
- додано внутрішнє прокручування інспектора та загальне прокручування сторінки для малих вікон і високого DPI;
- параметри камери згруповано у компактну адаптивну сітку;
- метрики трекінгу оформлено без вертикального накладання тексту;
- додано індикатор упевненості розпізнавання;
- візуалізатори каналів отримали компактний адаптивний режим без обрізання підписів і графіків;
- додано `AGENTS.md`, `.codex/config.toml`, `PLANS.md`, архітектурний опис і документацію для Codex;
- додано `codex_check.bat`, `codex_open.bat`, GitHub Actions та шаблони issue/pull request;
- проєкт підготовлено для локальної роботи Codex, IDE-розширення та Codex Cloud через GitHub.

## 2.0.0 — 2026-06-06

- повністю перероблено верхню панель без macOS-подібних кольорових кнопок;
- додано сучасну навігаційну панель із намальованими Qt-іконками;
- замінено класичний блоковий Qt-дизайн на легкі напівпрозорі поверхні, типографіку й адаптивні панелі;
- перероблено головну сторінку зі схемою потоку камера/рукавиця → Є-Рука → роботизована кисть;
- додано режим «Рукавиця» з окремим COM-портом, baudrate, автоперепідключенням і вибором формату;
- додано парсер масиву, CSV та префіксованих пакетів рукавиці;
- додано окремі налаштування каналу, Min, Max та інверсії рукавиці для кожної осі;
- додано сегментні live-візуалізатори, історію сигналу та анімовану модель кисті;
- інтегровано рукавицю як третє джерело керування разом із камерою та ручним режимом;
- жести залишено всередині ручного керування та оформлено як горизонтальну стрічку;
- додано приклад прошивки ESP32 для сенсорної рукавиці;
- додано документацію протоколу рукавиці та гайд по BAT-файлах;
- конфігурацію оновлено до schema version 2 з автоматичною міграцією старого профілю;
- розширено діагностику та набір тестів до 13.
