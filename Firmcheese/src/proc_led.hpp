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
  void update_color(bool is_left);

 private:
  uint8_t stage_;
  uint16_t counter_;
  Adafruit_NeoPixel nxp_L_;
  Adafruit_NeoPixel nxp_R_;

  std::array<uint8_t, kNumLeds * 2> data_;              // both hands
  std::array<uint8_t, kNumLeds * kNumPixelBytes> rgb_;  // one hand
};
