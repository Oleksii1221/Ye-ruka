#include <Arduino.h>

constexpr uint32_t BAUDRATE = 115200;
constexpr uint32_t SEND_INTERVAL_MS = 20;
constexpr uint8_t SENSOR_COUNT = 7;
constexpr uint8_t SENSOR_PINS[SENSOR_COUNT] = {32, 33, 34, 35, 36, 39, 25};

uint32_t lastSend = 0;

void setup() {
  Serial.begin(BAUDRATE);
  analogReadResolution(12);
  for (uint8_t i = 0; i < SENSOR_COUNT; ++i) {
    pinMode(SENSOR_PINS[i], INPUT);
  }
}

void loop() {
  const uint32_t now = millis();
  if (now - lastSend < SEND_INTERVAL_MS) return;
  lastSend = now;

  Serial.print('[');
  for (uint8_t i = 0; i < SENSOR_COUNT; ++i) {
    if (i) Serial.print(',');
    Serial.print(analogRead(SENSOR_PINS[i]));
  }
  Serial.println(']');
}
