#pragma once

#include "key_event.hpp"
#include "log.h"

class KeyProcUnmod {
 public:
  void init() {};
  bool process(KeyEventBuffer& kevb_in, KeyEventBuffer& kevb_out) {
    if (kevb_in.can_pop() == 0) return false;
    if (kevb_out.can_push() < 5) return false;
    const auto kev = kevb_in.pop_front();
    const keycode_t kc = kev.code_;
    const uint8_t mod = kc >> 8;
    auto kev_mod = kev;
    auto kev_key = kev;
    kev_key.code_ &= 0xff;
    if (kev.event_ == EKeyEvent::Pressed) {
      if (mod) {
        LOG_DEBUG("pressed: kc = %x, mod = %04x", kc, mod);
        // clang-format off
        if (mod & (QK_LCTL >> 8)) { kev_mod.code_ = KC_LCTL; kevb_out.push_back( kev_mod ); }
        if (mod & (QK_LSFT >> 8)) { kev_mod.code_ = KC_LSFT; kevb_out.push_back( kev_mod ); }
        if (mod & (QK_LALT >> 8)) { kev_mod.code_ = KC_LALT; kevb_out.push_back( kev_mod ); }
        if (mod & (QK_LGUI >> 8)) { kev_mod.code_ = KC_LGUI; kevb_out.push_back( kev_mod ); }
        // clang-format on
      }
      kevb_out.push_back(kev_key);
    } else {
      kevb_out.push_back(kev_key);
      if (mod) {
        LOG_DEBUG("released: kc = %x, mod = %04x", kc, mod);
        // clang-format off
        if (mod & (QK_LGUI >> 8)) { kev_mod.code_ = KC_LGUI; kevb_out.push_back( kev_mod ); }
        if (mod & (QK_LALT >> 8)) { kev_mod.code_ = KC_LALT; kevb_out.push_back( kev_mod ); }
        if (mod & (QK_LSFT >> 8)) { kev_mod.code_ = KC_LSFT; kevb_out.push_back( kev_mod ); }
        if (mod & (QK_LCTL >> 8)) { kev_mod.code_ = KC_LCTL; kevb_out.push_back( kev_mod ); }
        // clang-format on
      }
    }
    return true;
  }
};
