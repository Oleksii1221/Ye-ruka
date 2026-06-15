# Протокол керування роботизованою кистю «Є-Рука»

Цей документ описує, які дані PC-застосунок «Є-Рука» надсилає контролеру кисті через Serial, і яку логіку треба реалізувати у прошивці ESP32/Arduino/іншого контролера.

## Загальна схема

```text
Є-Рука на ПК -> USB-UART / Bluetooth Serial -> контролер кисті -> сервоприводи
```

ПК уже виконує:

- трекінг камери, рукавиці або ручного режиму;
- калібрування;
- фільтрацію;
- обмеження швидкості;
- clamp у механічні межі осей;
- формування фінальних кутів сервоприводів.

Контролер кисті повинен:

- приймати тільки повні валідні пакети;
- перевіряти кількість каналів;
- перевіряти CRC у захищеному режимі;
- перевіряти діапазони кутів;
- не рухати серви при помилковому пакеті;
- переходити у safe-положення при втраті зв’язку.

## Serial-параметри

Типові налаштування:

```text
baudrate: 115200
data bits: 8
parity: none
stop bits: 1
line ending: \n
send rate: 60 Hz
```

У застосунку baudrate і частота передачі налаштовуються у верхній панелі / налаштуваннях Serial. Підтримувані baudrate: `9600`, `19200`, `38400`, `57600`, `115200`, `230400`, `460800`, `921600`, `1000000`, `2000000`.

Передавання після запуску застосунку вимкнене. Користувач має окремо увімкнути `TX`.

## Стандартний порядок каналів

Актуальний стандартний профіль має 7 каналів:

| Канал | ID | Рух |
|---:|---|---|
| 0 | `thumb_flex` | згинання фаланг великого пальця |
| 1 | `thumb_opposition` | зведення великого пальця до вказівного |
| 2 | `thumb_base_flex` | згинання основи великого пальця |
| 3 | `index_flex` | згинання вказівного пальця |
| 4 | `middle_flex` | згинання середнього пальця |
| 5 | `ring_flex` | згинання безіменного пальця |
| 6 | `little_flex` | згинання мізинця |

Важливо: порядок і кількість каналів беруться з активного профілю. Вимкнена вісь не зникає з пакета: її канал лишається на місці, а застосунок відправляє для нього `safe_angle`. Завдяки цьому `SERVO_COUNT` на контролері не стрибає під час налаштування профілю.

## Значення у пакеті

Кожне число у пакеті — це фінальний цільовий кут сервопривода у градусах.

Приклад:

```text
[25,35,30,15,15,15,15]
```

Це не “відсотки згинання” і не сирі дані камери. Це вже готові кути, які контролер може подати на сервоприводи після власної перевірки безпеки.

## Простий формат

Простий формат зручний для першого налагодження:

```text
[90,45,90,90,90,90,90]\n
```

Правила:

- пакет починається з `[`;
- значення розділені комами;
- пакет закінчується `]\n`;
- кількість значень має дорівнювати `SERVO_COUNT`;
- CRC і sequence number немає.

Мінус простого формату: контролер не може перевірити контрольну суму. Для реального керування краще використовувати YR1.

## Захищений формат YR1

Рекомендований формат:

```text
@YR1,00125,7,90,45,90,90,90,90,90*D7DC\n
```

Структура:

| Частина | Значення |
|---|---|
| `@` | початок пакета |
| `YR1` | назва і версія протоколу |
| `00125` | sequence number, 5 цифр, modulo 100000 |
| `7` | кількість значень |
| `90,45,...` | кути сервоприводів |
| `*` | роздільник CRC |
| `D7DC` | CRC16-CCITT |
| `\n` | кінець пакета |

CRC рахується по payload між `@` і `*`.

Для прикладу вище payload такий:

```text
YR1,00125,7,90,45,90,90,90,90,90
```

CRC16-CCITT для цього payload:

```text
D7DC
```

## CRC16-CCITT

Параметри CRC:

```text
polynomial: 0x1021
initial: 0xFFFF
xor out: none
input reflected: false
output reflected: false
```

Приклад C/C++:

```cpp
uint16_t crc16Ccitt(const uint8_t* data, size_t length, uint16_t initial = 0xFFFF) {
  uint16_t crc = initial;
  for (size_t i = 0; i < length; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      if (crc & 0x8000) {
        crc = static_cast<uint16_t>((crc << 1) ^ 0x1021);
      } else {
        crc = static_cast<uint16_t>(crc << 1);
      }
    }
  }
  return crc;
}
```

## Рекомендована логіка контролера

1. Читати Serial до `\n`.
2. Ігнорувати `\r`.
3. Якщо рядок занадто довгий — скинути буфер і відповісти `!ERR,OVERFLOW`.
4. Якщо пакет починається з `@` — парсити YR1.
5. Якщо пакет починається з `[` — парсити простий формат.
6. Перевірити кількість значень.
7. Для YR1 перевірити CRC.
8. Перевірити кожен кут у межах `SERVO_MIN[i]..SERVO_MAX[i]`.
9. Якщо все валідно — застосувати всі кути одразу.
10. Якщо є помилка — не змінювати положення сервоприводів.
11. Якщо довго немає валідного пакета — перейти у safe-позицію.

## Діапазони для стандартного профілю

Початкові межі стандартного профілю:

```cpp
constexpr uint8_t SERVO_COUNT = 7;

constexpr int SERVO_MIN[SERVO_COUNT] = {
  10, 20, 15, 5, 5, 5, 5
};

constexpr int SERVO_MAX[SERVO_COUNT] = {
  170, 150, 165, 175, 175, 175, 175
};

constexpr int SERVO_SAFE[SERVO_COUNT] = {
  25, 35, 30, 15, 15, 15, 15
};
```

Ці значення треба підлаштувати під реальну механіку кисті. Не копіюйте їх як остаточні без фізичної перевірки.

## Відповіді контролера

Контролер може надсилати текстові повідомлення назад у Serial. Застосунок показує їх у діагностиці.

Рекомендовані відповіді:

```text
!READY,YR1
!ACK,00125
!ERR,CRC
!ERR,COUNT
!ERR,RANGE
!ERR,FORMAT
!ERR,OVERFLOW
!SAFE,TIMEOUT
```

Значення:

| Відповідь | Коли надсилати |
|---|---|
| `!READY,YR1` | контролер стартував |
| `!ACK,00125` | пакет прийнято, ACK опціональний |
| `!ERR,CRC` | CRC не збігається |
| `!ERR,COUNT` | кількість каналів неправильна |
| `!ERR,RANGE` | хоча б один кут поза межами |
| `!ERR,FORMAT` | пакет неможливо розпарсити |
| `!ERR,OVERFLOW` | вхідний рядок перевищив буфер |
| `!SAFE,TIMEOUT` | контролер перейшов у safe через втрату зв’язку |

ACK краще вимкнути при 30-50 пакетах/с, якщо він не потрібен для налагодження.

## Мінімальний приклад парсингу YR1

```cpp
bool parseExtended(char* line, int* values, uint32_t& sequence) {
  if (line[0] != '@') return false;

  char* star = strrchr(line, '*');
  if (!star) return false;

  *star = '\0';
  char* crcText = star + 1;

  char* endCrc = nullptr;
  unsigned long receivedCrc = strtoul(crcText, &endCrc, 16);
  if (endCrc == crcText || *endCrc != '\0') return false;

  const char* payload = line + 1;
  uint16_t expectedCrc = crc16Ccitt(
    reinterpret_cast<const uint8_t*>(payload),
    strlen(payload)
  );

  if (receivedCrc != expectedCrc) {
    Serial.println("!ERR,CRC");
    return false;
  }

  char* save = nullptr;
  char* token = strtok_r(line + 1, ",", &save);
  if (!token || strcmp(token, "YR1") != 0) return false;

  token = strtok_r(nullptr, ",", &save);
  if (!token) return false;
  sequence = strtoul(token, nullptr, 10);

  token = strtok_r(nullptr, ",", &save);
  if (!token) return false;

  int count = atoi(token);
  if (count != SERVO_COUNT) {
    Serial.println("!ERR,COUNT");
    return false;
  }

  for (uint8_t i = 0; i < SERVO_COUNT; ++i) {
    token = strtok_r(nullptr, ",", &save);
    if (!token) return false;

    char* end = nullptr;
    long value = strtol(token, &end, 10);
    if (end == token || *end != '\0') return false;

    if (value < SERVO_MIN[i] || value > SERVO_MAX[i]) {
      Serial.println("!ERR,RANGE");
      return false;
    }

    values[i] = static_cast<int>(value);
  }

  return strtok_r(nullptr, ",", &save) == nullptr;
}
```

## Safe timeout

Контролер не повинен нескінченно тримати останню команду, якщо зв’язок з ПК зник.

Рекомендовано:

```cpp
constexpr uint32_t LINK_TIMEOUT_MS = 1000;
```

Логіка:

```cpp
if (!safeApplied && millis() - lastValidPacketMs > LINK_TIMEOUT_MS) {
  applySafePosition();
}
```

Safe-позиція має бути механічно безпечною для кожної осі.

## Правила безпеки

- Не рухайте серви при CRC error.
- Не застосовуйте частину пакета.
- Не довіряйте тільки ПК: контролер теж має clamp/validate.
- Після старту контролера застосуйте safe або neutral.
- Перед першим TX перевірте кожен канал без навантаження або з від’єднаними тягами.
- Для сервоприводів використовуйте окреме живлення і спільну землю з контролером.

## Де дивитися готовий приклад

Готовий приклад прошивки:

```text
examples/esp32/Ye_Ruka_ESP32.ino
```

Він уже підтримує:

- простий формат;
- YR1;
- CRC16-CCITT;
- перевірку кількості каналів;
- перевірку діапазонів;
- safe timeout;
- опціональний ACK.
