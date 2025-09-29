#pragma once

#include <Adafruit_NeoPixel.h>

#include "key_switch.h"

constexpr uint8_t kNumPixelBytes = 3;

class ProcLed {
 private:
  enum EStage {
    ES_UpdateLedColor,
    ES_SendLeft,
    ES_SendRight,
    ES_Num,
  };

 public:
  ProcLed();
  void init();
  void process(const uint8_t* sw_state);

 private:
  void update_pattern(const uint8_t* sw_state);
  void update_color();

 private:
  uint8_t stage_;
  uint16_t counter_;
  std::array<Adafruit_NeoPixel, 2> npx_;
  std::array<uint8_t, kNumLeds * 2> data_;  // both hands
  std::array<uint8_t, kNumLeds * 2> overlay_;
};
