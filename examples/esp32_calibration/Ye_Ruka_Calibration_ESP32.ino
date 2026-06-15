#include <Arduino.h>
#include <ESP32Servo.h>

constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint8_t SERVO_COUNT = 7;
constexpr uint8_t SERVO_PINS[SERVO_COUNT] = {13, 12, 14, 27, 26, 25, 33};
constexpr float US_PER_DEGREE = 11.111f;
constexpr int SERVO_ZERO_US = 1500;
constexpr int MIN_RAW_ANGLE = -90;
constexpr int MAX_RAW_ANGLE = 90;

Servo servo;
int activeServo = -1;

int angleToPulse(float angle) {
  return constrain(
    static_cast<int>(lroundf(SERVO_ZERO_US + angle * US_PER_DEGREE)),
    500,
    2500
  );
}

void detachServo() {
  if (activeServo >= 0) {
    servo.detach();
    activeServo = -1;
  }
  Serial.println("!CAL,OFF");
}

void moveServo(uint8_t index, float angle) {
  if (activeServo != index) {
    if (activeServo >= 0) {
      servo.detach();
      delay(30);
    }
    servo.setPeriodHertz(50);
    servo.attach(SERVO_PINS[index], 500, 2500);
    activeServo = index;
  }

  angle = constrain(angle, MIN_RAW_ANGLE, MAX_RAW_ANGLE);
  int pulse = angleToPulse(angle);
  servo.writeMicroseconds(pulse);

  Serial.print("!CAL,MOVE,");
  Serial.print(index + 1);
  Serial.print(',');
  Serial.print(angle, 1);
  Serial.print(',');
  Serial.println(pulse);
}

void processCommand(String command) {
  command.trim();
  if (command.length() == 0) {
    return;
  }
  if (command.equalsIgnoreCase("off")) {
    detachServo();
    return;
  }
  if (command.equalsIgnoreCase("ping")) {
    Serial.println("!CAL,PONG");
    return;
  }

  int separator = command.indexOf(' ');
  if (separator < 0) {
    Serial.println("!ERR,FORMAT");
    return;
  }

  int servoNumber = command.substring(0, separator).toInt();
  float angle = command.substring(separator + 1).toFloat();
  if (servoNumber < 1 || servoNumber > SERVO_COUNT) {
    Serial.println("!ERR,SERVO");
    return;
  }
  if (angle < MIN_RAW_ANGLE || angle > MAX_RAW_ANGLE) {
    Serial.println("!ERR,ANGLE");
    return;
  }
  moveServo(servoNumber - 1, angle);
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  delay(500);
  Serial.println("!READY,CAL1");
  Serial.println("!CAL,RANGE,-90,90");
}

void loop() {
  if (Serial.available() > 0) {
    processCommand(Serial.readStringUntil('\n'));
  }
}
