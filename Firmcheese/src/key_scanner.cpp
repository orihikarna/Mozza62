#include "key_scanner.h"

#include "keyb_status.h"
#include "log.h"
#include "util.h"

namespace {

constexpr uint8_t mcp_addr[kNumSides] = {0x21, 0x20};
// in = 0, out = 1
constexpr uint16_t mcp_pin_inout[kNumSides] = {0xd802, 0x8036};

constexpr uint8_t mcp_row_bits[kNumSides][kNumRows] = {
    // Left
    {
        12,  // ROW1 = GPB4
        11,  // ROW2 = GPB3
        15,  // ROW3 = GPB7
        14,  // ROW4 = GPB6
        1,   // ROW5 = GPA1
    },
    // Right
    {
        4,   // ROW1 = GPA4
        5,   // ROW2 = GPA5
        1,   // ROW3 = GPA1
        2,   // ROW4 = GPA2
        15,  // ROW5 = GPB7
    },
};

constexpr uint8_t mcp_col_bits[kNumSides][kNumCols] = {
    // Left
    {
        13,  // COL1 = GPB5
        10,  // COL2 = GPB2
        9,   // COL3 = GPB1
        8,   // COL4 = GPB0
        7,   // COL5 = GPA7
        6,   // COL6 = GPA6
        5,   // COL7 = GPA5
        4,   // COL8 = GPA4
    },
    // Right
    {
        3,   // COL1 = GPA3
        6,   // COL2 = GPA6
        7,   // COL3 = GPA7
        8,   // COL4 = GPB0
        9,   // COL5 = GPB1
        10,  // COL6 = GPB2
        11,  // COL7 = GPB3
        12,  // COL8 = GPB4
    },
};

constexpr uint8_t mcp_rot_bits[kNumSides][kNumRots] = {
    // Left
    {
        3,  // COLA = GPA3
        2,  // COLB = GPA2
    },
    // Right
    {
        13,  // COLA = GPB5
        14,  // COLB = GPB6
    },
};

constexpr uint8_t rot_keys[kNumSides][kNumRots] = {
    {LRA, LRB},
    {RRA, RRB},
};

inline uint8_t get_col_bit(uint8_t side, uint16_t val, int8_t col) { return (val >> mcp_col_bits[side][col]) & 1; }

inline uint8_t get_rot_bit(uint8_t side, uint16_t val, int8_t rot) { return (val >> mcp_rot_bits[side][rot]) & 1; }

}  // namespace

void KeyScanner::init() {
  mcp_inited_.fill(false);
  mcp_disconnected_ms_.fill(0);
  mcp_init();

  scan_row_ = 0;
  key_state_.fill(0);
  rot_state_.fill(0);
}

void KeyScanner::mcp_init() {
  // Wire.setClock(400000);
  const uint32_t now_ms = millis();
  for (uint8_t side = 0; side < kNumSides; ++side) {
    if ((mcp_enabled_mask_ & (1 << side)) == 0) continue;
    if (mcp_inited_[side]) continue;
    if (mcp_disconnected_ms_[side] == 0) {
      mcp_disconnected_ms_[side] = now_ms;
      continue;
    }
    constexpr uint32_t recovery_wait_ms = 2000;
    if (now_ms - mcp_disconnected_ms_[side] < recovery_wait_ms) {
      continue;
    }
    mcp_disconnected_ms_[side] = 0;

    LOG_DUMP("[side=%d] begin_I2C()", side);
    if (mcp_[side].begin_I2C(mcp_addr[side]) == false) {
      LOG_WARN("[side=%d] begin_I2C() failed", side);
      continue;
    }
    for (uint8_t pin = 0; pin < 16; ++pin) {
      const uint8_t mode = (mcp_pin_inout[side] & (uint16_t(1) << pin)) ? OUTPUT : INPUT;
      // LOG_DUMP("[side=%d] set pin mode for pin = %d", side, pin);
      mcp_[side].pinMode(pin, mode);
    }
    // if (mcp_[side].set_ctrl_reg(0b00100000) == false) { continue; }
    mcp_inited_[side] = true;
  }
  GetKeybStatus().SetStatus(EKeybStatusBit::Left, mcp_inited_[0]);
  GetKeybStatus().SetStatus(EKeybStatusBit::Right, mcp_inited_[1]);
}

uint16_t KeyScanner::mcp_get_col(uint8_t side) {
  uint16_t col = 0;
  if ((mcp_enabled_mask_ & (1 << side)) == 0) {  // disabled
    // ...
  } else {  // enabled
    if (mcp_inited_[side]) {
      col = mcp_[side].readGPIOAB();
      if (col == 0xffff) {
        LOG_ERROR("side = %d, col = 0x%04x", side, col);
        mcp_inited_[side] = false;
        col = 0;
      }
    }
  }
  return col;
}

void KeyScanner::mcp_set_row(uint8_t row) {
  for (uint8_t side = 0; side < kNumSides; ++side) {
    if ((mcp_enabled_mask_ & (1 << side)) == 0) {  // disabled
      // ...
    } else {  // enabled
      if (mcp_inited_[side]) {
        mcp_[side].writeGPIOAB(1 << mcp_row_bits[side][row]);
        // if (mcp_[side].mcp_write(MCP23017::Port::B, val) == false) {
        //   mcp_inited_[side] = false;
        // }
      }
    }
  }
}

void KeyScanner::scan(KeyEventBuffer *fifo) {
  const uint8_t num_vacant = fifo->can_push();
  if (num_vacant < kNumCols) {
    LOG_ERROR("buffer vacancy is not enough: num_vacant = %d", num_vacant);
    return;
  }
  ElapsedTimer et;

  mcp_init();  // init mcp if timed out last time

  // increment row index
  const uint8_t curr_row = scan_row_;
  scan_row_ += 1;
  if (scan_row_ >= kNumRows) {
    scan_row_ = 0;
  }
  const uint8_t next_row = scan_row_;

  // minimize delay between read and write to allow the debounce circuit for
  // more settling time
  const uint16_t bits[kNumSides] = {
      mcp_get_col(ESide::Left),
      mcp_get_col(ESide::Right),
  };
  mcp_set_row(next_row);

  for (uint8_t side = 0; side < kNumSides; ++side) {
    {  // read col lines
      const auto &key_row = key_matrices[side][curr_row];
      for (uint8_t col = 0; col < kNumCols; ++col) {
        update_key_state(fifo, key_row[col], get_col_bit(side, bits[side], col));
      }
    }
    {  // read rot values
      // extract rotary encoder bits
      uint8_t rot_bits = 0;
      for (uint8_t rot = 0; rot < kNumRots; ++rot) {
        const uint8_t rot_bit = 1 << rot;
        if (get_rot_bit(side, bits[side], rot)) {
          rot_bits |= rot_bit;
        }
      }
      // dir = the first non-zero value
      //   A : 0 -> (1) -> [2] -> 0
      //   B : 0 -> (2) -> [1] -> 0
      // - rot_state_ keeps (the first non-zero value)
      // - the key state will be ON when [the second value] is observed
      // - the key state will be OFF when the final 0 is observed
      uint8_t dir = 0;
      if (rot_state_[side] == 0) {
        rot_state_[side] = rot_bits;
      } else {
        if (rot_bits == 0) {
          // released
          rot_state_[side] = 0;
        } else if ((rot_state_[side] | rot_bits) == 3) {
          dir = rot_state_[side];
        }
      }
      update_key_state(fifo, rot_keys[side][0], (dir == 2) ? 1 : 0);
      update_key_state(fifo, rot_keys[side][1], (dir == 1) ? 1 : 0);
    }
  }
  if (LOG_LEVEL <= LL_DEBUG) {  // elapsed time
    static uint32_t max_elapsed = 0;
    const uint32_t elapsed = et.getElapsedMicroSec();
    if (max_elapsed < elapsed) {
      max_elapsed = elapsed;
      LOG_DEBUG("elapsed = %ld us", max_elapsed);
    }
    max_elapsed -= 1;
  }
}

void KeyScanner::update_key_state(KeyEventBuffer *evbuf, uint8_t key, uint8_t val) {
  if (key >= 255) return;  // no key

  const uint8_t old_state = key_state_[key];
  const uint8_t is_on = (val) ? ESwitchState::IsON : 0;
  // keysw was on for continuous two times
  const uint8_t is_pressed = ((old_state & 1) == 1 && is_on) ? ESwitchState::IsPressed : 0;
  const uint8_t new_state = is_pressed | ((old_state << 1) & ~ESwitchState::IsPressed) | is_on;
  key_state_[key] = new_state;

  // push to fifo
  if ((~old_state & new_state) & ESwitchState::IsPressed) {
    LOG_DUMP("Pressed: key = %02x", key);
    evbuf->push_back(KeyEvent(key, EKeyEvent::Pressed, millis()));
  } else if ((old_state & ~new_state) & ESwitchState::IsPressed) {
    LOG_DUMP("Released: key = %02x", key);
    evbuf->push_back(KeyEvent(key, EKeyEvent::Released, millis()));
  }
}
