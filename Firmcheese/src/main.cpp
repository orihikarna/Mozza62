#include <Adafruit_MCP23X17.h>
#include <Adafruit_NeoPixel.h>
#include <Adafruit_TinyUSB.h>  // for Serial
#include <Arduino.h>

#include <array>

constexpr int leds[3] = {LED_RED, LED_BLUE, LED_GREEN};

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

  if (true) {  // setup mcp
    mcp.begin_I2C(0x21);
    // in = 0, out = 1
    constexpr uint16_t pin_inout = 0xd802;
    for (uint8_t pin = 0; pin < 16; ++pin) {
      mcp.pinMode(pin, (pin_inout & (1 << pin)) ? OUTPUT : INPUT);
    }
  }

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
  // scan_I2C();
  // delay(1000);
  // put your main code here, to run repeatedly:
  cnt += 1;
  for (int n = 0; n < 3; ++n) {
    digitalWrite(leds[n], HIGH);
  }
  digitalWrite(leds[cnt % 3], LOW);
  // Serial.printf("%d\n", cnt);
  // delay(1000);
  if (true) {  // key scan
    // B4, B3, B7, B6, A1
    constexpr uint8_t row_pins[] = {12, 11, 15, 14, 1};
    // B5, B2
    constexpr uint8_t col_pins[] = {13, 10, 9, 8, 7, 6, 5, 4};
    constexpr uint8_t rot_pins[] = {3, 2};
    for (uint8_t row = 0; row < 5; ++row) {
      // printf("row %d:", row);
      mcp.digitalWrite(row_pins[row], HIGH);
      delay(2);
      const uint16_t vals = mcp.readGPIOAB();
      for (uint8_t col = 0; col < 8; ++col) {
        if ((vals & (uint16_t(1) << col_pins[col]))) {
          // if (mcp.digitalRead(col_pins[col]) == LOW) {
          //  printf(" col%d, ", col);
          printf("row %d, col %d\n", row, col);
        }
      }
      // printf("\n");
      mcp.digitalWrite(row_pins[row], LOW);
    }
    const uint16_t vals = mcp.readGPIOAB();
    for (uint8_t rot = 0; rot < 2; ++rot) {
      if ((vals & (uint16_t(1) << rot_pins[rot]))) {
        printf("rot %d\n", rot);
      }
    }
  }
  if (false) {  // LED
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
}
