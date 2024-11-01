#pragma once

#include <Adafruit_NeoPixel.h>
#include <Arduino.h>

#include <array>
#include <cstdint>

#include "keyb_status.hpp"

class BoardLED {
 public:
  virtual void begin() = 0;
  virtual void update(bool blink, const KeybStatus& status) = 0;
};

#ifdef BOARD_XIAO_ESP32

class BoardLED_XiaoEsp32 : public BoardLED {
 protected:
  const std::array<int8_t, 1> xiao_leds_{21};
  const std::array<int8_t, 4> rj45_leds_{D10, D9, D7, D3};

 public:
  void begin() override {
    for (auto led : xiao_leds_) {
      pinMode(led, OUTPUT_OPEN_DRAIN);
      digitalWrite(led, LOW);
    }
    for (auto led : rj45_leds_) {
      pinMode(led, OUTPUT_OPEN_DRAIN);
      digitalWrite(led, LOW);
    }
  }
  void update(bool blink, const KeybStatus& status) override {
    digitalWrite(xiao_leds_[0], (blink) ? LOW : HIGH);
    digitalWrite(rj45_leds_[0], (blink || status.GetStatus(EKeybStatusBit::Ble)) ? LOW : HIGH);
    digitalWrite(rj45_leds_[1], (blink || status.GetStatus(EKeybStatusBit::Left)) ? LOW : HIGH);
    digitalWrite(rj45_leds_[2], (blink || status.GetStatus(EKeybStatusBit::Right)) ? LOW : HIGH);
    digitalWrite(rj45_leds_[3], (blink || status.GetStatus(EKeybStatusBit::Emacs)) ? LOW : HIGH);
  }
};
#endif

#ifdef BOARD_XIAO_BLE

class BoardLED_Xiao : public BoardLED {
 protected:
  const std::array<int8_t, 3> xiao_leds_{LED_RED, LED_BLUE, LED_GREEN};

 public:
  void begin() override {
    for (auto led : xiao_leds_) {
      pinMode(led, OUTPUT);
    }
  }
  void update(uint16_t cnt, const KeybStatus& status) override {
    int clr = 0;
    {  // hue == ble, emacs
      if (status.GetStatus(EKeybStatusBit::Ble)) {
        if (status.GetStatus(EKeybStatusBit::Emacs)) {
          clr = 0x4;
        } else {
          clr = 0x6;
        }
      } else {
        clr = 0x1;
      }
    }
    uint16_t period;
    {  // period = sides
      int8_t sides = 0;
      if (status.GetStatus(EKeybStatusBit::Left)) sides += 1;
      if (status.GetStatus(EKeybStatusBit::Right)) sides += 1;
      period = 100 - sides * 20;
    }
    const bool blink = ((cnt % period) < (period >> 1));
    for (uint8_t n = 0; n < 3; ++n) {
      digitalWrite(xiao_leds_[n], (blink && (clr & (1 << n))) ? HIGH : LOW);
    }
  }
};
#endif

#ifdef BOARD_M5ATOM
class BoardLED_M5Atom : public BoardLED {
 protected:
  static int LED_PIN_MATRIX = 27;
  static const uint16_t NUM_MATRIX_LEDS = 25;
  Adafruit_NeoPixel matrix_strip;

  static const uint8_t val = 128;
  static const uint32_t clr_ble_ok = Adafruit_NeoPixel::ColorHSV(65535 * 4 / 6, 255, val);
  static const uint32_t clr_ble_ng = Adafruit_NeoPixel::ColorHSV(65535 * 5 / 6, 255, val);
  static const uint32_t clr_side_ok = Adafruit_NeoPixel::ColorHSV(65535 * 4 / 6, 255, val);
  static const uint32_t clr_side_ng = Adafruit_NeoPixel::ColorHSV(65535 * 1 / 6, 255, val);
  static const uint32_t clr_emacs_on = Adafruit_NeoPixel::ColorHSV(65535 * 4 / 6, 255, val);
  static const uint32_t clr_emacs_off = Adafruit_NeoPixel::ColorHSV(65535 * 3 / 6, 255, val);

 public:
  BoardLED_M5Atom() : matrix_strip(NUM_MATRIX_LEDS, LED_PIN_MATRIX, NEO_GRB + NEO_KHZ800) {}

  void begin() override { matrix_strip.begin(); }
  void update(uint16_t cnt, const KeybStatus& status) override {
    for (uint16_t n = 0; n < NUM_MATRIX_LEDS; ++n) {
      // const uint16_t hue = ((4 * cnt + n * 4) & 255) << 8;
      // const uint32_t clr = Adafruit_NeoPixel::ColorHSV(hue, 255, 20);
      // matrix_strip.setPixelColor(n, clr);
      matrix_strip.setPixelColor(n, 0);
    }
    matrix_strip.setPixelColor(0, (status.GetStatus(EKeybStatusBit::Ble)) ? clr_ble_ok : clr_ble_ng);
    matrix_strip.setPixelColor(1, (status.GetStatus(EKeybStatusBit::Left)) ? clr_side_ok : clr_side_ng);
    matrix_strip.setPixelColor(2, (status.GetStatus(EKeybStatusBit::Right)) ? clr_side_ok : clr_side_ng);
    matrix_strip.setPixelColor(3, (status.GetStatus(EKeybStatusBit::Emacs)) ? clr_emacs_on : clr_emacs_off);
    matrix_strip.show();
  }
};
#endif
