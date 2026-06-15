#include <Arduino.h>
#include <ESP32Servo.h>
#include <ctype.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint8_t SERVO_COUNT = 7;
constexpr uint8_t SERVO_PINS[SERVO_COUNT] = {13, 12, 14, 27, 26, 25, 33};

// Order: little, ring, middle, index, thumb flex, thumb opposition, thumb palm.
constexpr int SERVO_MIN_ANGLE[SERVO_COUNT] = {-45, -65, -40, -50, -30, 50, 50};
constexpr int SERVO_MAX_ANGLE[SERVO_COUNT] = {90, 70, 90, 90, 80, 90, 50};
constexpr int SERVO_SAFE_ANGLE[SERVO_COUNT] = {-45, 70, -40, -50, 80, 50, 50};
constexpr bool SERVO_REVERSED[SERVO_COUNT] = {false, false, false, false, false, false, false};
constexpr float US_PER_DEGREE[SERVO_COUNT] = {
  11.111f, 11.111f, 11.111f, 11.111f, 11.111f, 11.111f, 11.111f
};
constexpr int SERVO_ZERO_US[SERVO_COUNT] = {1500, 1500, 1500, 1500, 1500, 1500, 1500};

constexpr uint32_t LINK_TIMEOUT_MS = 1000;
constexpr uint32_t CONTROL_INTERVAL_MS = 20;
constexpr int MAX_STEP_DEGREES = 4;
constexpr bool SEND_ACK = false;
constexpr size_t LINE_BUFFER_SIZE = 256;

Servo servos[SERVO_COUNT];
char lineBuffer[LINE_BUFFER_SIZE];
size_t lineLength = 0;
uint32_t lastValidPacketMs = 0;
uint32_t lastControlTickMs = 0;
bool safeApplied = true;
bool parseErrorReported = false;
int currentAngles[SERVO_COUNT];
int targetAngles[SERVO_COUNT];
uint8_t activeServoIndex = 0;

uint16_t crc16Ccitt(const uint8_t* data, size_t length, uint16_t initial = 0xFFFF) {
  uint16_t crc = initial;
  for (size_t i = 0; i < length; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000)
        ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
        : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

int angleToPulse(uint8_t index, int angle) {
  float signedAngle = SERVO_REVERSED[index] ? -angle : angle;
  return static_cast<int>(lroundf(
    SERVO_ZERO_US[index] + signedAngle * US_PER_DEGREE[index]
  ));
}

bool validateAngles(const int* values) {
  for (uint8_t i = 0; i < SERVO_COUNT; ++i) {
    if (values[i] < SERVO_MIN_ANGLE[i] || values[i] > SERVO_MAX_ANGLE[i]) {
      Serial.print("!ERR,RANGE,");
      Serial.println(i + 1);
      parseErrorReported = true;
      return false;
    }
  }
  return true;
}

void setTargetAngles(const int* values) {
  for (uint8_t i = 0; i < SERVO_COUNT; ++i) {
    targetAngles[i] = constrain(values[i], SERVO_MIN_ANGLE[i], SERVO_MAX_ANGLE[i]);
  }
}

void updateServoMotion() {
  uint32_t now = millis();
  if (now - lastControlTickMs < CONTROL_INTERVAL_MS) {
    return;
  }
  lastControlTickMs = now;

  for (uint8_t offset = 0; offset < SERVO_COUNT; ++offset) {
    uint8_t index = (activeServoIndex + offset) % SERVO_COUNT;
    int delta = targetAngles[index] - currentAngles[index];
    if (delta == 0) {
      continue;
    }

    int step = constrain(delta, -MAX_STEP_DEGREES, MAX_STEP_DEGREES);
    currentAngles[index] += step;
    servos[index].writeMicroseconds(angleToPulse(index, currentAngles[index]));

    // Finish one servo before starting the next to avoid a simultaneous current spike.
    activeServoIndex = currentAngles[index] == targetAngles[index]
      ? (index + 1) % SERVO_COUNT
      : index;
    return;
  }
}

void applySafePosition(bool notify) {
  setTargetAngles(SERVO_SAFE_ANGLE);
  safeApplied = true;
  if (notify) {
    Serial.println("!SAFE,TIMEOUT");
  }
}

bool parseInteger(char* text, int& value) {
  while (isspace(static_cast<unsigned char>(*text))) {
    ++text;
  }
  char* end = nullptr;
  long parsed = strtol(text, &end, 10);
  if (end == text) {
    return false;
  }
  while (isspace(static_cast<unsigned char>(*end))) {
    ++end;
  }
  if (*end != '\0') {
    return false;
  }
  value = static_cast<int>(parsed);
  return true;
}

bool parseSimple(char* line, int* values) {
  size_t length = strlen(line);
  if (length < 2 || line[0] != '[' || line[length - 1] != ']') {
    return false;
  }

  line[length - 1] = '\0';
  char* save = nullptr;
  char* token = strtok_r(line + 1, ",", &save);
  uint8_t count = 0;
  while (token != nullptr) {
    if (count >= SERVO_COUNT || !parseInteger(token, values[count])) {
      return false;
    }
    ++count;
    token = strtok_r(nullptr, ",", &save);
  }
  return count == SERVO_COUNT && validateAngles(values);
}

bool parseExtended(char* line, int* values, uint32_t& sequence) {
  if (line[0] != '@') {
    return false;
  }

  char* star = strrchr(line, '*');
  if (star == nullptr || strlen(star + 1) != 4) {
    return false;
  }

  char* crcEnd = nullptr;
  unsigned long receivedCrc = strtoul(star + 1, &crcEnd, 16);
  if (crcEnd == star + 1 || *crcEnd != '\0' || receivedCrc > 0xFFFFUL) {
    return false;
  }

  const char* payload = line + 1;
  size_t payloadLength = static_cast<size_t>(star - payload);
  uint16_t expectedCrc = crc16Ccitt(
    reinterpret_cast<const uint8_t*>(payload),
    payloadLength
  );
  if (static_cast<uint16_t>(receivedCrc) != expectedCrc) {
    Serial.println("!ERR,CRC");
    parseErrorReported = true;
    return false;
  }

  *star = '\0';
  char* save = nullptr;
  char* token = strtok_r(line + 1, ",", &save);
  if (token == nullptr || strcmp(token, "YR1") != 0) {
    return false;
  }

  token = strtok_r(nullptr, ",", &save);
  if (token == nullptr) {
    return false;
  }
  sequence = strtoul(token, nullptr, 10);

  token = strtok_r(nullptr, ",", &save);
  if (token == nullptr || atoi(token) != SERVO_COUNT) {
    Serial.println("!ERR,COUNT");
    parseErrorReported = true;
    return false;
  }

  for (uint8_t i = 0; i < SERVO_COUNT; ++i) {
    token = strtok_r(nullptr, ",", &save);
    if (token == nullptr || !parseInteger(token, values[i])) {
      return false;
    }
  }
  if (strtok_r(nullptr, ",", &save) != nullptr) {
    return false;
  }
  return validateAngles(values);
}

void processLine(char* line) {
  int values[SERVO_COUNT];
  uint32_t sequence = 0;
  parseErrorReported = false;
  bool valid = line[0] == '@'
    ? parseExtended(line, values, sequence)
    : parseSimple(line, values);
  if (!valid) {
    if (!parseErrorReported) {
      Serial.println("!ERR,FORMAT");
    }
    return;
  }

  setTargetAngles(values);
  lastValidPacketMs = millis();
  safeApplied = false;
  if (SEND_ACK) {
    Serial.print("!ACK,");
    Serial.println(sequence);
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  delay(500);
  for (uint8_t i = 0; i < SERVO_COUNT; ++i) {
    currentAngles[i] = SERVO_SAFE_ANGLE[i];
    targetAngles[i] = SERVO_SAFE_ANGLE[i];
    servos[i].setPeriodHertz(50);
    servos[i].attach(SERVO_PINS[i], 100, 4000);
    servos[i].writeMicroseconds(angleToPulse(i, SERVO_SAFE_ANGLE[i]));
    delay(100);
  }

  lastValidPacketMs = millis();
  lastControlTickMs = millis();
  Serial.println("!READY,YR1");
}

void loop() {
  while (Serial.available() > 0) {
    char value = static_cast<char>(Serial.read());
    if (value == '\r') {
      continue;
    }
    if (value == '\n') {
      lineBuffer[lineLength] = '\0';
      if (lineLength > 0) {
        processLine(lineBuffer);
      }
      lineLength = 0;
      continue;
    }
    if (lineLength + 1 < LINE_BUFFER_SIZE) {
      lineBuffer[lineLength++] = value;
    } else {
      lineLength = 0;
      Serial.println("!ERR,OVERFLOW");
    }
  }

  if (!safeApplied && millis() - lastValidPacketMs > LINK_TIMEOUT_MS) {
    applySafePosition(true);
  }

  updateServoMotion();
}
