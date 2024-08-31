#pragma once

#include "ringbuf.hpp"

enum class EKeyEvent {
  None = 0x00,
  Released = 0x01,
  Pressed = 0x02,
};

using keycode_t = uint16_t;

struct KeyEvent {
  KeyEvent(keycode_t code = 0, EKeyEvent event = EKeyEvent::None, uint32_t tick_ms = 0)
      : code_(code), event_(event), tick_ms_(tick_ms) {}
  keycode_t code_;
  EKeyEvent event_;
  uint32_t tick_ms_;

  inline bool isPressed() const { return event_ == EKeyEvent::Pressed; }
};

using KeyEventBuffer = RingBuffer<KeyEvent>;
