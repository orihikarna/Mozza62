#include <Arduino.h>
#include <Adafruit_TinyUSB.h> // for Serial
#include <Adafruit_NeoPixel.h>

#include <array>

constexpr uint16_t NUM_LEDS = 30;
std::array<Adafruit_NeoPixel, 2> strips = {
  Adafruit_NeoPixel(NUM_LEDS, D0, NEO_GRB + NEO_KHZ800),
  Adafruit_NeoPixel(NUM_LEDS, D1, NEO_GRB + NEO_KHZ800),
};

constexpr int leds[3] = { LED_RED, LED_BLUE, LED_GREEN };

int cnt = 0;

void setup() {
  // Serial.begin(9600);
  Serial.begin(115200);
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
