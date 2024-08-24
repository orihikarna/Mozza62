#include <Adafruit_MCP23X17.h>
#include <Adafruit_NeoPixel.h>
#include <Arduino.h>

#include <array>

#include "key_event.hpp"
#include "key_scanner.hpp"
#include "proc_layer.hpp"
#include "ringbuf.hpp"

// #define BOARD_XIAO_BLE
#define BOARD_M5ATOM

#ifdef BOARD_XIAO_BLE
#include <Adafruit_TinyUSB.h>  // for Serial
constexpr std::array<int, 3> leds = {LED_RED, LED_BLUE, LED_GREEN};
#define LED_PIN_LEFT D0
#define LED_PIN_RIGHT D1
#endif

#ifdef BOARD_M5ATOM
// #include <M5Atom.h>
#define LED_PIN_MATRIX 27
#define LED_PIN_LEFT 19
#define LED_PIN_RIGHT 22
constexpr uint16_t NUM_MATRIX_LEDS = 25;
Adafruit_NeoPixel matrix_strip(NUM_MATRIX_LEDS, LED_PIN_MATRIX, NEO_GRB + NEO_KHZ800);
#endif

constexpr uint16_t NUM_LEDS = 30;
std::array<Adafruit_NeoPixel, 2> strips = {
    Adafruit_NeoPixel(NUM_LEDS, LED_PIN_LEFT, NEO_GRB + NEO_KHZ800),
    Adafruit_NeoPixel(NUM_LEDS, LED_PIN_RIGHT, NEO_GRB + NEO_KHZ800),
};

void scan_I2C() {
  Adafruit_MCP23X17 mcp;
  Serial.println("I2C Scan");
  for (int address = 1; address < 0x80; address++) {
    const bool ret = mcp.begin_I2C(address);
    if (ret) {
      Serial.printf("%02X", address);
    } else {
      Serial.print(" .");
    }
    if (address % 16 == 0) {
      Serial.print("\n");
    }
    delay(10);
  }
  Serial.print("end\n\n");
}

namespace NScanTest {
Adafruit_MCP23X17 mcp;

void scan_test_setup() {
  uint16_t pin_inout = 0;
  if (false) {  // left
    mcp.begin_I2C(0x21);
    pin_inout = 0xd802;  // in = 0, out = 1
  } else {               // right
    mcp.begin_I2C(0x20);
    pin_inout = 0x8036;  // in = 0, out = 1
  }
  for (uint8_t pin = 0; pin < 16; ++pin) {
    mcp.pinMode(pin, (pin_inout & (1 << pin)) ? OUTPUT : INPUT);
  }
}

void scan_test_loop() {
  // key scan left
  // B4, B3, B7, B6, A1
  // constexpr uint8_t row_pins[] = {12, 11, 15, 14, 1};
  // B5, B2
  // constexpr uint8_t col_pins[] = {13, 10, 9, 8, 7, 6, 5, 4};
  // constexpr uint8_t rot_pins[] = {3, 2};

  // key scan right
  // A4, A5, A1, A2, B7
  constexpr uint8_t row_pins[] = {4, 5, 1, 2, 15};
  // A3, A6, A7, B0
  constexpr uint8_t col_pins[] = {3, 6, 7, 8, 9, 10, 11, 12};
  constexpr uint8_t rot_pins[] = {13, 14};
  for (uint8_t row = 0; row < 5; ++row) {
    // printf("row %d:", row);
    mcp.digitalWrite(row_pins[row], HIGH);
    delay(3);
    const uint16_t vals = mcp.readGPIOAB();
    for (uint8_t col = 0; col < 8; ++col) {
      if ((vals & (uint16_t(1) << col_pins[col]))) {
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
}  // namespace NScanTest

KeyScanner scanner;

void setup() {
  // Serial.begin(9600);
  Serial.begin(115200);
  // while (!Serial) delay(100);

#ifdef BOARD_M5ATOM
  Wire.begin(25, 21, 100000UL);
#endif

  scan_I2C();

  if (true) {  // LED
#ifdef BOARD_XIAO_BLE
    for (auto led : leds) {
      pinMode(led, OUTPUT);
    }
#endif
#ifdef BOARD_M5ATOM
    matrix_strip.begin();
#endif
  }
  if (true) {  // full color LED
    for (auto &strip : strips) {
      strip.begin();
      // strip.show();
    }
  }
  scanner.init();
  // NScanTest::scan_test_setup();
}

std::array<KeyEvent, 12> keva_input;  // 1 rows + extra
std::array<KeyEvent, 12> keva_layer;
std::array<KeyEvent, 12> keva_emacs;
std::array<KeyEvent, 6> keva_unmod;

KeyEventBuffer kevb_input(keva_input.data(), keva_input.size());
KeyEventBuffer kevb_layer(keva_layer.data(), keva_layer.size());
KeyEventBuffer kevb_emacs(keva_emacs.data(), keva_emacs.size());
KeyEventBuffer kevb_unmod(keva_unmod.data(), keva_unmod.size());

// LedProc led_proc;
KeyProcLayer proc_layer;
// KeyEmacsProc proc_emacs;
// KeyUnmodProc proc_unmod;
// KeyNkroProc proc_nkro;

void loop() {
  // return;
  static int cnt = 0;
  cnt += 1;
  if (true) {  // board LED
#ifdef BOARD_XIAO_BLE
    for (auto led : leds) {
      digitalWrite(led, HIGH);
    }
    digitalWrite(leds[cnt % leds.size()], LOW);
#endif
#ifdef BOARD_M5ATOM
    for (uint16_t n = 0; n < NUM_MATRIX_LEDS; ++n) {
      const uint16_t hue = ((4 * cnt + n * 4) & 255) << 8;
      for (auto &strip : strips) {
        const uint32_t clr = Adafruit_NeoPixel::ColorHSV(hue, 255, 20);
        matrix_strip.setPixelColor(n, clr);
      }
    }
#endif
  }
  if (true) {  // key scan
    // NScanTest::scan_test_loop();
    scanner.scan(&kevb_input);
  }

  KeyEventBuffer *pkevb_in = nullptr;
  KeyEventBuffer *pkevb_out = &kevb_input;

#define _set_kevb(kevb) \
  pkevb_in = pkevb_out; \
  pkevb_out = &kevb
  _set_kevb(kevb_layer);
  while (proc_layer.process(*pkevb_in, *pkevb_out));
  // _set_kevb( kevb_emacs ); while (proc_emacs.process( *pkevb_in, *pkevb_out )) {}
  // _set_kevb( kevb_unmod ); while (proc_unmod.process( *pkevb_in, *pkevb_out )) {}
#undef _set_kevb
  if (true) {  // full color LED
    for (uint16_t n = 0; n < NUM_LEDS; ++n) {
      const uint16_t hue = ((cnt * 1 + n * 4) & 255) << 8;
      for (auto &strip : strips) {
        const uint32_t clr = Adafruit_NeoPixel::ColorHSV(hue, 255, 10);
        strip.setPixelColor(n, clr);
      }
    }
    for (auto &strip : strips) {
      strip.show();
    }
  }
  delay(1);
}
