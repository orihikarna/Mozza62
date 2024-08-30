#pragma once
#include <array>

#include "key_event.hpp"
#include "key_switch.hpp"

enum EKeyLayer { Default = 0, Lower, Misc, NumLayers };

enum ERGB {
  Off = 0,
  KeyDown,
  Snake,
  Fall,
  Knight,
  Windmill,
  Circle,
};

enum ECLR {
  Rainbow = 0,
  Red,
  Green,
  Blue,
  White,
  RedSat,
  GreenSat,
  BlueSat,
};

#define CFG_SET_VAL(addr, x) ((addr) | (x))
#define CFG_GET_VAL(kc) ((kc) & 0x0f)
#define CFG_ADDR(kc) (((kc) - ConfigStart) >> 4)

enum custom_keycodes {
  // layers
  LayerStart = 0x8000,
  KL_Lowr = LayerStart,
  KL_Raiz,
  LayerEnd,
  NumLayerKeys = LayerEnd - LayerStart,
  // config memories
  ConfigStart = 0x9000,
  CFG_RGB_TYPE = 0x9000,
  CFG_CLR_TYPE = 0x9010,
  ConfigEnd = 0x9020,
  NumConfigAddrs = CFG_ADDR(ConfigEnd),
  // RGB_TYPE
  CF_LOFF = CFG_SET_VAL(CFG_RGB_TYPE, ERGB::Off),
  CF_LKEY = CFG_SET_VAL(CFG_RGB_TYPE, ERGB::KeyDown),
  CF_LSNK = CFG_SET_VAL(CFG_RGB_TYPE, ERGB::Snake),
  CF_LFAL = CFG_SET_VAL(CFG_RGB_TYPE, ERGB::Fall),
  CF_LKNT = CFG_SET_VAL(CFG_RGB_TYPE, ERGB::Knight),
  CF_LWML = CFG_SET_VAL(CFG_RGB_TYPE, ERGB::Windmill),
  CF_LCRL = CFG_SET_VAL(CFG_RGB_TYPE, ERGB::Circle),
  // CLR_TYPE
  CF_CRBW = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::Rainbow),
  CF_CRED = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::Red),
  CF_CGRN = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::Green),
  CF_CBLU = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::Blue),
  CF_CWHT = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::White),
  CF_CRDS = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::RedSat),
  CF_CGRS = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::GreenSat),
  CF_CBLS = CFG_SET_VAL(CFG_CLR_TYPE, ECLR::BlueSat),
  // RESET
  SC_REST = 0xa000,
};

#define CONFIG_DATA(ADDR) g_config_data[CFG_ADDR(ADDR)]

class ConfigData {
 private:
  std::array<uint8_t, NumConfigAddrs> config_data_;

 public:
  void init();
  uint8_t& operator[](uint16_t kc) { return config_data_[CFG_ADDR(kc)]; }
};

extern std::array<uint8_t, NumConfigAddrs> g_config_data;
// extern ConfigData g_config_data;

void init_config_data();

extern const keycode_t keymaps[EKeyLayer::NumLayers][EKeySW::NumSWs];
