#include "proc_layer.hpp"

#include "key_event.hpp"
#include "keymaps.hpp"
#include "qmk/keycode_jp.h"

void KeyProcLayer::init() {
  layer_ = EKeyLayer::Default;
  layer_key_counts_.fill(0);
  keycodes_.fill(KC_NO);
}

bool KeyProcLayer::process(KeyEventBuffer& kevb_in, KeyEventBuffer& kevb_out) {
  if (kevb_in.can_pop() == 0) return false;
  if (kevb_out.can_push() < 2) return false;
  const auto kev_raw = kevb_in.pop_front();
  keycode_t keycode = keymaps[layer_][kev_raw.code_];  // translate
  if (keycode == KC_TRNS) {
    keycode = keymaps[0][kev_raw.code_];  // default layer
  }
  LOG_DEBUG("keycode = %d, event = %d", keycode, kev_raw.event_);
  if (keycode == SC_REST) {
    // NVIC_SystemReset();
  }
  if (ConfigStart <= keycode && keycode < ConfigEnd) {
    // CONFIG_DATA(keycode) = CFG_GET_VAL(keycode);
  } else if (LayerStart <= keycode && keycode < LayerEnd) {
    {  // increment / decrement counts
      const uint8_t layer = keycode - LayerStart;
      if (kev_raw.isPressed()) {
        layer_key_counts_[layer] += 1;
      } else {
        layer_key_counts_[layer] -= 1;
      }
    }
    {  // change the layer
      const bool is_lower = (layer_key_counts_[KL_Lowr - LayerStart] > 0);
      const bool is_raise = (layer_key_counts_[KL_Raiz - LayerStart] > 0);
      if (is_lower && is_raise) {
        layer_ = EKeyLayer::Misc;
      } else if (is_lower || is_raise) {
        layer_ = EKeyLayer::Lower;
      } else {
        layer_ = EKeyLayer::Default;
      }
    }
    LOG_DEBUG("layer = %d", layer_);
  } else {
    auto kev_out = kev_raw;
    if (kev_raw.isPressed()) {
      // pressed
      kev_out.code_ = keycode;
      keycodes_[kev_raw.code_] = keycode;  // remember
    } else {
      // released
      kev_out.code_ = keycodes_[kev_raw.code_];  // recall
      keycodes_[kev_raw.code_] = KC_NO;          // forget
    }
    kevb_out.push_back(kev_out);
  }
  return true;
}
