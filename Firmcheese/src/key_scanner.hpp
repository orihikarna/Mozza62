#pragma once

#include <Adafruit_MCP23X17.h>

#include <array>
#include <cstdint>

#include "keyevent.hpp"
#include "keyswitch.hpp"

static constexpr size_t kNumSides = 2;

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
  uint16_t mcp_read(size_t side);
  void mcp_write_all(uint8_t row, uint8_t value);

 private:
  uint8_t row_idx_;
  std::array<uint8_t, EKeySW::NumSWs> sw_state_;

 public:
  void init();
  void scan(/*KeyEventBuffer *fifo*/);
#if 0
  inline bool is_pressed(uint8_t swidx) const {
    return sw_state_[swidx] & static_cast<int>(ESwitchState::IsPressed);
  }
  inline uint8_t *getSwitchStateData() { return sw_state_.data(); }
#endif

 private:
  void update_key_state(/*KeyEventBuffer *fifo,*/ uint8_t key, uint8_t val);
};
