#include <string>

#ifdef BOARD_XIAO_BLE
#include <Adafruit_TinyUSB.h>  // for Serial
#define LED_PIN_LEFT D0
#define LED_PIN_RIGHT D1
#endif

#ifdef BOARD_M5ATOM
#define LED_PIN_LEFT 19
#define LED_PIN_RIGHT 22
#endif

#include "key_scanner.hpp"
#include "keymaps.hpp"
#include "proc_led.hpp"
#include "util.hpp"

#ifdef abs
#undef abs
#endif

struct KeyGeometry {
  KeyGeometry(float x, float y, float angle)
      : x(round(x)),
        y(round(y)),
        r(round(std::sqrt(x * x + y * y))),
        angle(round(std::atan2(y, x) * (180 / M_PI) + 0.5f)) {}
  int8_t x;
  int8_t y;
  int8_t r;
  int8_t angle;
};

static const KeyGeometry s_sw_geos[] = {
    {59.594, 72.780, -6.000},    // &6
    {76.501, 71.003, -6.000},    // '7
    {97.155, 66.057, -24.000},   // (8
    {114.574, 58.281, -26.000},  // )9
    {129.680, 45.428, -8.000},   //  0
    {145.520, 35.992, -8.000},   // =-
    //
    {156.647, 10.051, -8.000},   // {{
    {140.806, 19.487, -8.000},   // `@
    {124.965, 28.924, -8.000},   // P
    {109.816, 41.687, -26.000},  // O
    {92.978, 49.308, -24.000},   // I
    {72.947, 54.283, -6.000},    // U
    {56.040, 56.060, -6.000},    // Y
    //
    {36.429, 50.295, -21.234},   // |¥
    {52.486, 39.340, -6.000},    // H
    {69.393, 37.563, -6.000},    // J
    {88.802, 32.558, -24.000},   // K
    {105.058, 25.094, -26.000},  // L
    {120.250, 12.419, -8.000},   // +;
    {136.091, 2.983, -8.000},    // *:
    {151.932, -6.454, -8.000},   // }}
    //
    {136.271, -20.407, -22.000},  // _Bsls
    {114.702, -8.656, -22.000},   // ?/
    {100.300, 8.500, -26.000},    // >.
    {84.626, 15.809, -24.000},    // <,
    {65.839, 20.843, -6.000},     // M
    {48.932, 22.620, -6.000},     // N
    {32.828, 33.456, -21.234},    // Entr
    //
    {11.647, -15.167, -244.000},  // Raise
    {30.440, -10.126, -256.000},  // Shift
    {49.871, -9.102, -268.000},   // Space
};
namespace NPattern {
constexpr int8_t speed_sh = 2;

void effect_linear(uint8_t* dat, uint16_t cnt) {
  const int8_t ctr = cnt >> speed_sh;
  uint8_t* dat_L = &dat[0];
  uint8_t* dat_R = &dat[kNumLeds];
  for (int16_t n = 0; n < kNumLeds; ++n) {
    dat_L[n] = ctr;
    dat_R[n] = ctr;
  }
}

void effect_fall(uint8_t* dat, uint16_t cnt) {
  const uint8_t ctr = cnt >> speed_sh;
  uint8_t* dat_L = &dat[0];
  uint8_t* dat_R = &dat[kNumLeds];
  for (uint8_t n = 0; n < kNumLeds; ++n) {
    const uint8_t v = ctr - (s_sw_geos[n].y);
    dat_L[n] = v;
    dat_R[n] = v;
  }
}

void effect_windmill(uint8_t* dat, uint16_t cnt) {
  const int8_t ctr = cnt >> speed_sh;
  uint8_t* dat_L = &dat[0];
  uint8_t* dat_R = &dat[kNumLeds];
  for (int16_t n = 0; n < kNumLeds; ++n) {
    const int8_t deg = s_sw_geos[n].angle;
    dat_L[n] = ctr - deg;
    dat_R[n] = ctr + deg - 128;
  }
}

void effect_circle(uint8_t* dat, uint16_t cnt) {
  const int8_t ctr = cnt >> speed_sh;
  uint8_t* dat_L = &dat[0];
  uint8_t* dat_R = &dat[kNumLeds];
  for (int16_t n = 0; n < kNumLeds; ++n) {
    const uint8_t d = ctr - (s_sw_geos[n].r >> 2);
    dat_L[n] = d;
    dat_R[n] = d;
  }
}
}  // namespace NPattern
namespace NColor {  // color conversion

void set_hue(uint32_t* rgb, const uint8_t* dat, uint8_t sat = 255, uint8_t vis = 24) {
  for (uint8_t n = 0; n < kNumLeds; ++n) {
    rgb[n] = Adafruit_NeoPixel::ColorHSV(dat[n] << 8, sat, vis);
  }
}

void set_sat(uint32_t* rgb, const uint8_t* dat, uint8_t hue, uint8_t vis = 24) {
  for (uint8_t n = 0; n < kNumLeds; ++n) {
    int16_t val = static_cast<int8_t>(dat[n]);
    val = std::abs(val);
    val = std::min<int16_t>(std::max<int16_t>((val << 2) - 256, 0), 255);
    rgb[n] = Adafruit_NeoPixel::ColorHSV(hue << 8, val, vis);
  }
}

void set_rgb(uint32_t* rgb, const uint8_t* dat, bool red, bool green, bool blue) {
  const uint8_t r_mask = (red) ? 0xff : 0;
  const uint8_t g_mask = (green) ? 0xff : 0;
  const uint8_t b_mask = (blue) ? 0xff : 0;
  for (uint8_t n = 0; n < kNumLeds; ++n) {
    int8_t val = static_cast<int8_t>(dat[n]);
    val = std::abs(val) - 96;
    val = std::max<int8_t>(val, 0);
    rgb[n] = Adafruit_NeoPixel::Color(r_mask & val, g_mask & val, b_mask & val);
  }
}
}  // namespace NColor
namespace {
void effect_keydown(uint8_t* data, uint16_t counter, const uint8_t* sw_state) {
  for (uint8_t n = 0; n < EKeySW::NumSWs; ++n) {
    const uint8_t idx = g_sw2led_index[n];
    if (idx == 255) continue;
    if (sw_state[n] & ESwitchState::IsPressed) {
      data[idx] = 96;
    } else if ((counter & 3) == 0) {  // fade
      uint8_t v = data[idx];
      if (v > 0) {
        v -= 2;
      }
      data[idx] = v;
    }
  }
}

inline uint32_t color_max(uint32_t rgb1, uint32_t rgb2) {
  const uint32_t r = std::max(rgb1 & 0xff0000, rgb2 & 0xff0000);
  const uint32_t g = std::max(rgb1 & 0x00ff00, rgb2 & 0x00ff00);
  const uint32_t b = std::max(rgb1 & 0x0000ff, rgb2 & 0x0000ff);
  return r | g | b;
}

inline uint32_t color_overlay_white(uint32_t rgb, uint8_t mag) {
  const uint32_t r = std::max(static_cast<uint8_t>(rgb >> 16), mag);
  const uint32_t g = std::max(static_cast<uint8_t>(rgb >> 8), mag);
  const uint32_t b = std::max(static_cast<uint8_t>(rgb), mag);
  return (r << 16) | (g << 8) | b;
}
}  // namespace

ProcLed::ProcLed()
    : npx_{
          Adafruit_NeoPixel(kNumLeds, LED_PIN_LEFT, NEO_GRB + NEO_KHZ800),
          Adafruit_NeoPixel(kNumLeds, LED_PIN_RIGHT, NEO_GRB + NEO_KHZ800),
      } {}

void ProcLed::init() {
  for (uint8_t side = 0; side < kNumSides; ++side) {
    npx_[side].begin();
  }

  stage_ = ES_UpdateLedColor;
  counter_ = 0;
  overlay_.fill(0);

#if 0
  for (uint8_t n = 0; n < EKeySW::NumSWs; ++n) {
    s_sw2led_index[s_led2sw_index[n]] = n;
  }
  for (uint8_t n = 0; n < EKeySW::NumSWs; ++n) {
    printf("%d, ", s_sw2led_index[n]);
  }
  printf("\n");
#endif
}

// output [0, 128)
void ProcLed::update_pattern(const uint8_t* sw_state) {
  effect_keydown(overlay_.data(), counter_, sw_state);
  switch (static_cast<EPattern>(g_config_data[CFG_PAT_TYPE])) {
    case EPattern::Linear:
      NPattern::effect_linear(data_.data(), counter_);
      break;
    case EPattern::Fall:
      NPattern::effect_fall(data_.data(), counter_);
      break;
    case EPattern::Windmill:
      NPattern::effect_windmill(data_.data(), counter_);
      break;
    case EPattern::Circle:
      NPattern::effect_circle(data_.data(), counter_);
      break;
  }
  counter_ += 1;
}

void ProcLed::update_color() {
  std::array<uint32_t, kNumLeds> _rgb;
  uint32_t* rgb = _rgb.data();
  for (uint8_t side = 0; side < kNumSides; ++side) {
    const uint8_t* dat = &data_[(side == 0) ? 0 : kNumLeds];
    const uint8_t* overlay = &overlay_[(side == 0) ? 0 : kNumLeds];
    switch (static_cast<EColor>(g_config_data[CFG_CLR_TYPE])) {
      case EColor::Off:
        _rgb.fill(0);
        break;
      case EColor::Rainbow:
        NColor::set_hue(rgb, dat);
        break;
      case EColor::Red:
        NColor::set_rgb(rgb, dat, true, false, false);
        break;
      case EColor::Green:
        NColor::set_rgb(rgb, dat, false, true, false);
        break;
      case EColor::Blue:
        NColor::set_rgb(rgb, dat, false, false, true);
        break;
      case EColor::White:
        NColor::set_rgb(rgb, dat, true, true, true);
        break;
      case EColor::RedSat:
        NColor::set_sat(rgb, dat, 0);
        break;
      case EColor::GreenSat:
        NColor::set_sat(rgb, dat, 43);
        break;
      case EColor::BlueSat:
        NColor::set_sat(rgb, dat, 85);
        break;
    }
    {  // set color
      Adafruit_NeoPixel& npx = npx_[side];
      for (uint8_t n = 0; n < kNumLeds; ++n) {
        const uint32_t ovl = overlay[n];
        // const uint32_t clr = color_max(rgb[n], (ovl << 16) | (ovl << 8) | ovl);
        const uint32_t clr = color_overlay_white(rgb[n], ovl);
        npx.setPixelColor(n, clr);
      }
    }
  }
}

void ProcLed::process(const uint8_t* sw_state) {
  ElapsedTimer et;
  switch (stage_) {
    case ES_UpdateLedColor:
      update_pattern(sw_state);
      update_color();
      break;
    case ES_SendLeft:
      npx_[0].show();
      break;
    case ES_SendRight:
      npx_[1].show();
      break;
  }
  // if (stage_ == ES_UpdateLed || stage_ == ES_UpdateColor) {
  if (stage_ == ES_SendLeft || stage_ == ES_SendRight) {
    static uint32_t max_elapsed_us = 0;
    const uint32_t elapsed_us = et.getElapsedMicroSec();
    if (max_elapsed_us < elapsed_us) {
      max_elapsed_us = elapsed_us;
      LOG_DEBUG("stage_ = %d, elapsed = %ld us", stage_, max_elapsed_us);
    }
    // max_elapsed_us -= 1;
  }
  // update stage
  stage_ += 1;
  if (stage_ == ES_Num) {
    stage_ = ES_UpdateLedColor;
  }
}
