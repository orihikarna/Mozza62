#pragma once

#include <algorithm>
#include <array>

#include "blehid.hpp"
#include "key_event.hpp"
#include "log.h"
#include "util.hpp"

class KeyProcNkro {
 private:
  static constexpr uint8_t kNkroSize = 6;
  uint8_t mods_;
  std::array<keycode_t, kNkroSize> codes_;

  // MouseHID mouse_;

 public:
  void init() {
    mods_ = 0;
    codes_.fill(KC_NO);

    /*
    mouse_.m_report_id = 2;
    mouse_.m_buttons = 0;
    mouse_.m_x = 0;
    mouse_.m_y = 0;
    mouse_.m_wheel = 0;
    */
  }

  KeyboardReport send_key(const KeyEvent& kev) {
    LOG_DUMP("kev.code_: %04x, event = %d", kev.code_, kev.event_);
    if (is_modifier(kev.code_)) {                   // modifier keys
      const uint8_t mod_mask = MOD_BIT(kev.code_);  // 1 << (kev.code_ - KC_LCTRL);
      if (kev.event_ == EKeyEvent::Pressed) {
        mods_ |= mod_mask;
      } else {
        mods_ &= ~mod_mask;
      }
    } else {  // usual keys
      if (kev.event_ == EKeyEvent::Pressed) {
        // if no avail, discard the front (the oldest)
        if (std::find(codes_.begin(), codes_.end(), KC_NO) == codes_.end()) {
          codes_[0] = KC_NO;
        }
      } else {  // released
        for (uint8_t i = 0; i < kNkroSize; ++i) {
          if (codes_[i] == kev.code_) {
            codes_[i] = KC_NO;
          }
        }
      }
      {  // reorganize codes_
        uint8_t idx = 0;
        // bring !KC_NO keys to the front
        const auto codes = codes_;
        for (auto code : codes) {
          if (code != KC_NO) {
            codes_[idx++] = code;
          }
        }
        // push pressed
        if (kev.event_ == EKeyEvent::Pressed) {
          codes_[idx++] = kev.code_;
        }
        // fill the blanks
        while (idx < kNkroSize) {
          codes_[idx++] = KC_NO;
        }
      }
    }
    KeyboardReport kbrd;
    {
      kbrd.reserved = 0;
      kbrd.modifiers = mods_;
      for (int i = 0; i < kNkroSize; ++i) {
        kbrd.modifiers |= codes_[i] >> 8;
        kbrd.keys[i] = codes_[i] & 0xff;
      }
    }
    return kbrd;
  }

 private:
  static inline bool is_modifier(uint16_t code) {
    // return KC_LCTRL <= code && code <= KC_RGUI;
    return IS_MOD(code);
  }
};
