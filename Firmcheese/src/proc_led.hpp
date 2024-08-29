#pragma once

#include <Adafruit_NeoPixel.h>

#include "key_switch.hpp"

// #include "keyscanner.hpp"

constexpr uint8_t kNumPixelBytes = 3;

class ProcLed {
 private:
  enum EStage {
    ES_UpdateLed,
    ES_UpdateColorLeft,
    ES_SendLeft,
    ES_UpdateColorRight,
    ES_SendRight,
    ES_Num,
  };

 public:
  ProcLed();
  void init();
  void process(const uint8_t* sw_state);

 private:
  void update_led(const uint8_t* sw_state);
  void update_color(uint8_t side);

 private:
  uint8_t stage_;
  uint16_t counter_;
  std::array<Adafruit_NeoPixel, 2> npx_;

  std::array<uint8_t, kNumLeds * 2> data_;  // both hands
};
