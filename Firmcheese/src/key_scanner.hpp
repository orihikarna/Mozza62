#pragma once

#include <Adafruit_MCP23X17.h>

#include <array>
#include <cstdint>

#include "key_event.hpp"
#include "key_switch.hpp"

enum ESide {
  Left = 0,
  Right = 1,
};

enum ESwitchState : uint8_t {
  IsON = 0x01,
  // 0x02-0x40 = old IsOn
  IsPressed = 0x80,
};

class KeyScanner {
 private:
  std::array<Adafruit_MCP23X17, kNumSides> mcp_;
  std::array<bool, kNumSides> mcp_inited_;

  void mcp_init();
  uint16_t mcp_get_col(uint8_t side);
  void mcp_set_row(uint8_t row);

 private:
  static constexpr uint8_t mcp_enabled_mask_ = 0x02;
  uint8_t scan_row_ = 0;
  std::array<uint8_t, EKeySW::NumSWs> key_state_;
  std::array<uint8_t, kNumSides> rot_state_;

 public:
  void init();
  void scan(KeyEventBuffer *evbuf);
#if 0
  inline bool is_pressed(uint8_t swidx) const {
    return key_state_[swidx] & static_cast<int>(ESwitchState::IsPressed);
  }
  inline uint8_t *getSwitchStateData() { return key_state_.data(); }
#endif

 private:
  void update_key_state(KeyEventBuffer *fifo, uint8_t key, uint8_t val);
};
