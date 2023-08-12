#include <Arduino.h>
#include <Adafruit_TinyUSB.h> // for Serial
#include <Adafruit_NeoPixel.h>
#include <Adafruit_MCP23X17.h>

#include <array>

constexpr int leds[3] = { LED_RED, LED_BLUE, LED_GREEN };

constexpr uint16_t NUM_LEDS = 30;
std::array<Adafruit_NeoPixel, 2> strips = {
  Adafruit_NeoPixel(NUM_LEDS, D0, NEO_GRB + NEO_KHZ800),
  Adafruit_NeoPixel(NUM_LEDS, D1, NEO_GRB + NEO_KHZ800),
};

// GPIO4(SDA)  <-> SDA
// GPIO5(SCL)  <-> SCL
Adafruit_MCP23X17 mcp;

void scan_I2C() {
  Serial.println("I2C Scan");
  for (int address = 1; address < 0x80; address++) {
    const int error = mcp.begin_I2C(address);
    if (error != 0) {
      Serial.printf("%02X", address);
    } else {
      Serial.print(" .");
    }

    if (address % 16 == 0) {
      Serial.print("\n");
    }
    delay(20);
  }
  Serial.print("end\n\n");
}

int cnt = 0;

void setup() {
  // Serial.begin(9600);
  Serial.begin(115200);
  // while (!Serial) delay(100);

  scan_I2C();

  // put your setup code here, to run once:
  for (int n = 0; n < 3; ++n) {
    pinMode(leds[n], OUTPUT);
  }

  for (auto& strip : strips) {
    strip.begin();
    strip.show();
  }
}

void loop() {
  scan_I2C();
  delay(1000);
  return;

  // put your main code here, to run repeatedly:
  cnt += 1;
  for (int n = 0; n < 3; ++n) {
    digitalWrite(leds[n], HIGH);
  }
  digitalWrite(leds[cnt % 3], LOW);
  delay(1000);
  Serial.printf("%d\n", cnt);
  for (uint16_t n = 0; n < NUM_LEDS; ++n) {
    const uint16_t hue = ((16 * cnt + n * 4) & 255) << 8;
    for (auto& strip : strips) {
      strip.setPixelColor(n, Adafruit_NeoPixel::ColorHSV(hue, 255, 10));
    }
  }
  for (auto& strip : strips) {
    strip.show();
  }
}
