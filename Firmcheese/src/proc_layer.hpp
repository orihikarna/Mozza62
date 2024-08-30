#pragma once

#include <array>

#include "key_event.hpp"
#include "key_switch.hpp"
#include "keymaps.hpp"

class KeyProcLayer {
 public:
  void init();
  bool process(KeyEventBuffer& kevb_in, KeyEventBuffer& kevb_out);

 protected:
  uint8_t layer_;
  std::array<uint8_t, NumLayerKeys> layer_key_counts_;  // pressed counter
  std::array<uint16_t, EKeySW::NumSWs> keycodes_;       // remember the last translation
};