#pragma once

#include <cstdint>

// void hsv2grb(uint16_t h, uint8_t s, uint8_t v, uint8_t* prgb);
// void hsv2grbw(uint16_t h, uint8_t s, uint8_t v, uint8_t white, uint8_t* pgrbw);

class ElapsedTimer {
 public:
  ElapsedTimer() : start_us_(micros()) {}
  uint32_t getElapsedMicroSec() const { return micros() - start_us_; }

 private:
  const uint32_t start_us_;
};
