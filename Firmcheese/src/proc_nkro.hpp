#pragma once

#include <qmk/keycode.h>

#include <algorithm>
#include <array>

#include "key_event.hpp"
#include "log.h"
#include "util.hpp"

class KeyProcNkro {
 private:
  static constexpr uint8_t kNkroSize = 6;
  uint8_t mods_;
  std::array<keycode_t, kNkroSize> codes_;
  // KeyboardHID kbrd_;
  // MouseHID mouse_;

 public:
  void init() {
    mods_ = 0;
    codes_.fill(KC_NO);

    /*
    //kbrd_.m_report_id = 1;
    kbrd_.m_modifiers = 0;
    kbrd_.m_reserved = 0;
    for (int i = 0; i < SIZE_HID_KEYS; ++i) {
      kbrd_.m_keys[i] = 0;
    }
    */
    /*
    mouse_.m_report_id = 2;
    mouse_.m_buttons = 0;
    mouse_.m_x = 0;
    mouse_.m_y = 0;
    mouse_.m_wheel = 0;
    */
  }

  void send_key(const KeyEvent& kev) {
    LOG_DEBUG("kev.code_: %04x, event = %d", kev.code_, kev.event_);
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
      {  // bring !KC_NO keys to the front
        uint8_t idx = 0;
        const auto codes = codes_;
        for (auto code : codes) {
          if (code != KC_NO) {
            codes_[idx++] = code;
          }
        }
        if (kev.event_ == EKeyEvent::Pressed) {  // pressed
          codes_[idx++] = kev.code_;
        }
        while (idx < kNkroSize) {
          codes_[idx++] = KC_NO;
        }
      }
    }
    {  // send
       // KeyboardHID kbrd;
       // // kbrd.m_report_id = 1;
       // kbrd.m_reserved = 0;
       // kbrd.m_modifiers = mods_;
       // for (int i = 0; i < SIZE_HID_KEYS; ++i) {
       //   kbrd.m_modifiers |= codes_[i] >> 8;
       //   kbrd.m_keys[i] = codes_[i] & 0xff;
       // }
       // set_keyboard_report(&kbrd);
    }
  }

 private:
  static inline bool is_modifier(uint16_t code) {
    // return KC_LCTRL <= code && code <= KC_RGUI;
    return IS_MOD(code);
  }
};
