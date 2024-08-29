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

#include "key_layer.hpp"
#include "key_scanner.hpp"
#include "proc_led.hpp"

struct KeyGeometry {
  KeyGeometry(float x, float y, float angle, float w, float h, int idx, const char* name)
      : x(x), y(y) {}
  float x;
  float y;
  //   float angle;
  //   float width;
  //   float height;
  //   int idx;
  //   const char* name;
};

static const KeyGeometry s_sw_geos[] = {
    {59.594, 72.780, -6.000, 17.000, 17.000, 9, "&6"},
    {76.501, 71.003, -6.000, 17.000, 17.000, 17, "'7"},
    {97.155, 66.057, -24.000, 17.000, 17.000, 25, "(8"},
    {114.574, 58.281, -26.000, 17.000, 17.000, 33, ")9"},
    {129.680, 45.428, -8.000, 17.000, 17.000, 40, " 0"},
    {145.520, 35.992, -8.000, 17.000, 17.000, 46, "=-"},
    //
    {156.647, 10.051, -8.000, 17.000, 17.000, 51, "{{"},
    {140.806, 19.487, -8.000, 17.000, 17.000, 45, "`@"},
    {124.965, 28.924, -8.000, 17.000, 17.000, 39, "P"},
    {109.816, 41.687, -26.000, 17.000, 17.000, 32, "O"},
    {92.978, 49.308, -24.000, 17.000, 17.000, 24, "I"},
    {72.947, 54.283, -6.000, 17.000, 17.000, 16, "U"},
    {56.040, 56.060, -6.000, 17.000, 17.000, 8, "Y"},
    //
    {36.429, 50.295, -21.234, 17.000, 17.000, 59, "|¥"},
    {52.486, 39.340, -6.000, 17.000, 17.000, 7, "H"},
    {69.393, 37.563, -6.000, 17.000, 17.000, 15, "J"},
    {88.802, 32.558, -24.000, 17.000, 17.000, 23, "K"},
    {105.058, 25.094, -26.000, 17.000, 17.000, 31, "L"},
    {120.250, 12.419, -8.000, 17.000, 17.000, 38, "+;"},
    {136.091, 2.983, -8.000, 17.000, 17.000, 44, "*:"},
    {151.932, -6.454, -8.000, 17.000, 17.000, 50, "}}"},
    //
    {136.271, -20.407, -22.000, 26.000, 17.000, 56, "_Bsls"},
    {114.702, -8.656, -22.000, 22.800, 17.000, 54, "?/"},
    {100.300, 8.500, -26.000, 17.000, 17.000, 30, ">."},
    {84.626, 15.809, -24.000, 17.000, 17.000, 22, "<,"},
    {65.839, 20.843, -6.000, 17.000, 17.000, 14, "M"},
    {48.932, 22.620, -6.000, 17.000, 17.000, 6, "N"},
    {32.828, 33.456, -21.234, 17.000, 17.000, 58, "Entr"},
    //
    {11.647, -15.167, -244.000, 22.000, 17.000, 4, "Raise"},
    {30.440, -10.126, -256.000, 22.000, 17.000, 2, "Shift"},
    {49.871, -9.102, -268.000, 22.000, 17.000, 0, "Space"},
};
namespace NImpl {  // RGB effect patterns

constexpr int16_t maxv = 255;

// [0, kNumLeds) --> [0, 256)
// void effect_snake(uint8_t* dat, uint16_t cnt) {
//   constexpr int16_t N = 1024;  // period
//   constexpr int16_t scale = int16_t(256.0f * 256 / kNumLeds + 0.5f);
//   const uint16_t ctr = cnt & (N - 1);
//   for (int16_t n = 0; n < kNumLeds; ++n) {
//     dat[n] = ((ctr + 2) >> 2) + ((scale * n + 128) >> 8);
//   }
// }

// void effect_fall(uint8_t* dat, uint16_t cnt) {
//   const uint8_t ctr = cnt >> 2;
//   uint8_t* dat_L = &dat[0];
//   uint8_t* dat_R = &dat[kNumLeds];
//   for (uint8_t n = 0; n < kNumLeds; ++n) {
//     const uint8_t v = ctr - (s_sw_geos[n].y >> 1);
//     dat_L[n] = v;
//     dat_R[n] = v;
//   }
// }

// void effect_knight(uint8_t* dat, uint16_t cnt) {
//   constexpr int16_t N = 1024;  // period
//   int16_t ctr = cnt & (N - 1);
//   ctr = ((ctr >= N / 2) ? (N - ctr) : ctr) - N / 4;  // +/- 256

//   uint8_t* dat_L = &dat[0];
//   uint8_t* dat_R = &dat[kNumLeds];
//   for (int8_t n = 0; n < kNumLeds; ++n) {
//     const int16_t x = int16_t(s_sw_geo[n][0]) - 127;  // [-254, 0]
//     const int16_t dL = (ctr - x) >> 2;  // [-256, +510] /2 --> [-128, 255] /2 --> [-64, 127]
//     const int16_t dR = (ctr + x) >> 2;  // [-510, +256] /2 --> [-255, 128] /2 --> [-128, 64]
//     dat_L[n] = 128 + dL;
//     dat_R[n] = 128 + dR;
//   }
// }

// void effect_windmill(uint8_t* dat, uint16_t cnt) {
//   const int8_t ctr = cnt >> 2;
//   uint8_t* dat_L = &dat[0];
//   uint8_t* dat_R = &dat[kNumLeds];
//   for (int16_t n = 0; n < kNumLeds; ++n) {
//     const int8_t deg = s_sw_geo[n][3];
//     dat_L[n] = ctr - deg;
//     dat_R[n] = ctr + deg - 128;
//   }
// }

// void effect_circle(uint8_t* dat, uint16_t cnt) {
//   const int8_t ctr = cnt >> 1;
//   uint8_t* dat_L = &dat[0];
//   uint8_t* dat_R = &dat[kNumLeds];
//   for (int16_t n = 0; n < kNumLeds; ++n) {
//     const uint8_t d = ctr - (s_sw_geos[n][2] << 1);
//     dat_L[n] = d;
//     dat_R[n] = d;
//   }
// }
}  // namespace NImpl
namespace {  // color conversion

void set_hue(uint8_t* rgb, const uint8_t* dat, uint8_t sat = 255, uint8_t vis = 12) {
  for (uint8_t n = 0; n < kNumLeds; ++n) {
    // hsv2grb(dat[n] >> 1, sat, vis, rgb);
    rgb += kNumPixelBytes;
  }
}

void set_sat(uint8_t* rgb, const uint8_t* dat, uint8_t hue, uint8_t vis = 12) {
  for (uint8_t n = 0; n < kNumLeds; ++n) {
    int16_t val = (int8_t)dat[n];
    val = std::abs(val);
    val = std::min<int16_t>(std::max<int16_t>((val << 2) - 256, 0), 255);
    // hsv2grb(hue, val, vis, rgb);
    rgb += kNumPixelBytes;
  }
}

void set_rgb(uint8_t* rgb, const uint8_t* dat, bool red, bool green, bool blue) {
  const uint8_t r_mask = (red) ? 0xff : 0;
  const uint8_t g_mask = (green) ? 0xff : 0;
  const uint8_t b_mask = (blue) ? 0xff : 0;
  for (uint8_t n = 0; n < kNumLeds; ++n) {
    int8_t val = (int8_t)dat[n];
    val = std::abs(val) - 96;
    val = std::max<int8_t>(val, 0);
    *rgb++ = g_mask & val;
    *rgb++ = r_mask & val;
    *rgb++ = b_mask & val;
  }
}
}  // namespace

ProcLed::ProcLed()
    : nxp_L_(kNumLeds, LED_PIN_LEFT, NEO_GRB + NEO_KHZ800),
      nxp_R_(kNumLeds, LED_PIN_RIGHT, NEO_GRB + NEO_KHZ800) {}

void ProcLed::init() {
  nxp_L_.begin();
  nxp_R_.begin();

  stage_ = ES_UpdateLed;
  counter_ = 0;

#if 0
  for (uint8_t n = 0; n < EKeySW::NumSWs; ++n) {
    s_sw2led_index[s_led2sw_index[n]] = n;
  }
  for (uint8_t n = 0; n < EKeySW::NumSWs; ++n) {
    printf( "%d, ", s_sw2led_index[n] );
  }
  printf( "\n" );
#endif
}

// output [0, 128)
void ProcLed::update_led(const uint8_t* sw_state) {
  switch (uint8_t(CONFIG_DATA(CFG_RGB_TYPE))) {
    case ERGB::KeyDown:
      for (uint8_t n = 0; n < EKeySW::NumSWs; ++n) {
        const uint8_t idx = g_sw2led_index[n];
        if (idx == 255) continue;
        if (sw_state[n] & ESwitchState::IsPressed) {
          data_[idx] = 127;
        } else if ((counter_ & 3) == 0) {  // fade
          uint8_t v = data_[idx];
          if (v > 0) {
            v -= 1;
          }
          data_[idx] = v;
        }
      }
      break;

    case ERGB::Snake:
      //   effect_snake(data_.data(), counter_);
      break;
    case ERGB::Fall:
      //   effect_fall(data_.data(), counter_);
      break;
    case ERGB::Knight:
      //   effect_knight(data_.data(), counter_);
      break;
    case ERGB::Windmill:
      //   effect_windmill(data_.data(), counter_);
      break;
    case ERGB::Circle:
      //   effect_circle(data_.data(), counter_);
      break;
  }
  counter_ += 1;
}

void ProcLed::update_color(bool is_left) {
  if (CONFIG_DATA(CFG_RGB_TYPE) == ERGB::Off) {
    rgb_.fill(0);
    return;
  }
  const uint8_t* src = &data_[(is_left) ? 0 : kNumLeds];
  uint8_t* dst = rgb_.data();
  switch (uint8_t(CONFIG_DATA(CFG_CLR_TYPE))) {
    case ECLR::Rainbow:
      set_hue(dst, src);
      break;
    case ECLR::Red:
      set_rgb(dst, src, true, false, false);
      break;
    case ECLR::Green:
      set_rgb(dst, src, false, true, false);
      break;
    case ECLR::Blue:
      set_rgb(dst, src, false, false, true);
      break;
    case ECLR::White:
      set_rgb(dst, src, true, true, true);
      break;
    case ECLR::RedSat:
      set_sat(dst, src, 0);
      break;
    case ECLR::GreenSat:
      set_sat(dst, src, 43);
      break;
    case ECLR::BlueSat:
      set_sat(dst, src, 85);
      break;
  }
}

void ProcLed::process(const uint8_t* sw_state) {
  // ElapsedTimer et;
  switch (stage_) {
    case ES_UpdateLed:
      update_led(sw_state);
      break;
    case ES_UpdateColorLeft:
      update_color(true);
      break;
    case ES_SendLeft:
      nxp_L_.show();
      break;
    case ES_UpdateColorRight:
      update_color(false);
      break;
    case ES_SendRight:
      nxp_R_.show();
      break;
  }
  if (stage_ == ES_UpdateLed) {
    // LOG_DEBUG("stage_ = %d, elapsed = %ld us", stage_, 0 /*et.getElapsedMicroSec()*/);
  }
  // update stage
  stage_ += 1;
  if (stage_ == ES_Num) {
    stage_ = ES_UpdateLed;
  }
}
