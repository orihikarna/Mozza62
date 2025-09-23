#pragma once

#include <qmk/keycode_jp.h>

#include <array>

#include "key_event.hpp"
#include "key_switch.hpp"

enum EKeyLayer { Default = 0, Lower, Misc, NumLayers };

enum EPattern {
  Linear = 0,
  Fall,
  Windmill,
  Circle,
};

enum EColor {
  Off = 0,
  Rainbow,
  Red,
  Green,
  Blue,
  White,
  RedSat,
  GreenSat,
  BlueSat,
};

#define CFG_SET_VAL(addr, x) ((addr) | (x))
#define CFG_ADDR(kc) (((kc) - ConfigStart) >> 4)
#define CFG_VALUE(kc) ((kc) & 0x0f)

enum custom_keycodes {
  TGLEMAC = LCTL(LALT(LSFT(KC_Q))),
  // layers
  LayerStart = 0x8000,
  KL_Lowr = LayerStart,
  KL_Raiz,
  LayerEnd,
  NumLayerKeys = LayerEnd - LayerStart,
  // config memories
  ConfigStart = 0x9000,
  CFG_PAT_TYPE = 0x9000,
  CFG_CLR_TYPE = 0x9010,
  ConfigEnd = 0x9020,
  NumConfigAddrs = CFG_ADDR(ConfigEnd),
  // PAT_TYPE
  CF_LLNR = CFG_SET_VAL(CFG_PAT_TYPE, EPattern::Linear),
  CF_LFAL = CFG_SET_VAL(CFG_PAT_TYPE, EPattern::Fall),
  CF_LWML = CFG_SET_VAL(CFG_PAT_TYPE, EPattern::Windmill),
  CF_LCRL = CFG_SET_VAL(CFG_PAT_TYPE, EPattern::Circle),
  // CLR_TYPE
  CF_COFF = CFG_SET_VAL(CFG_CLR_TYPE, EColor::Off),
  CF_CRBW = CFG_SET_VAL(CFG_CLR_TYPE, EColor::Rainbow),
  CF_CRED = CFG_SET_VAL(CFG_CLR_TYPE, EColor::Red),
  CF_CGRN = CFG_SET_VAL(CFG_CLR_TYPE, EColor::Green),
  CF_CBLU = CFG_SET_VAL(CFG_CLR_TYPE, EColor::Blue),
  CF_CWHT = CFG_SET_VAL(CFG_CLR_TYPE, EColor::White),
  CF_CRDS = CFG_SET_VAL(CFG_CLR_TYPE, EColor::RedSat),
  CF_CGRS = CFG_SET_VAL(CFG_CLR_TYPE, EColor::GreenSat),
  CF_CBLS = CFG_SET_VAL(CFG_CLR_TYPE, EColor::BlueSat),
  // RESET
  SC_REST = 0xa000,
};

class ConfigData {
 private:
  std::array<uint8_t, NumConfigAddrs> config_data_;

 public:
  void init();
  void apply(uint16_t kc) { config_data_[CFG_ADDR(kc)] = CFG_VALUE(kc); }
  uint8_t& operator[](uint16_t kc) { return config_data_[CFG_ADDR(kc)]; }
};

extern ConfigData g_config_data;

extern const keycode_t keymaps[EKeyLayer::NumLayers][EKeySW::NumSWs];
