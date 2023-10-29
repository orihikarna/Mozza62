// #define LOG_LEVEL LL_DEBUG
// #include "main.h"
#include "key_scanner.hpp"

#include "log.h"

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

inline uint8_t get_col_bit(uint8_t side, uint16_t val, int8_t col) {
  return (val >> mcp_col_bits[side][col]) & 1;
}

inline uint8_t get_rot_bit(uint8_t side, uint16_t val, int8_t rot) {
  return (val >> mcp_rot_bits[side][rot]) & 1;
}

}  // namespace

void KeyScanner::mcp_init() {
  for (size_t side = 0; side < kNumSides; ++side) {
    if ((mcp_enabled_mask_ & (1 << side)) == 0) {
      continue;
    }
    if (mcp_inited_[side]) {
      continue;
    }
    // mcp_[side].disable();
    delay(1);
    // mcp_[side].enable();
    delay(1);

    mcp_[side].begin_I2C(mcp_addr[side]);
    for (uint8_t pin = 0; pin < 16; ++pin) {
      const uint8_t mode =
          (mcp_pin_inout[side] & (uint16_t(1) << pin)) ? OUTPUT : INPUT;
      mcp_[side].pinMode(pin, mode);
    }
    // if (mcp_[side].set_ctrl_reg(0b00100000) == false) { continue; }
    // LOG_DEBUG("(mcp_init) side = %d", side);
    mcp_inited_[side] = true;
  }
}

uint16_t KeyScanner::mcp_get_col(size_t side) {
  uint16_t col = 0;
  if ((mcp_enabled_mask_ & (1 << side)) == 0) {
    return col;
  }
  if (mcp_inited_[side]) {
    col = mcp_[side].readGPIOAB();
    // LOG_DEBUG("col = 0x%04x\n", col);
    if (col == 0xffff) {
      mcp_inited_[side] = false;
    }
  }
  return col;
}

void KeyScanner::mcp_set_row(uint8_t row) {
  for (size_t side = 0; side < kNumSides; ++side) {
    if ((mcp_enabled_mask_ & (1 << side)) == 0) {
      continue;
    }
    if (mcp_inited_[side]) {
      mcp_[side].writeGPIOAB(1 << mcp_row_bits[side][row]);
      // if (mcp_[side].mcp_write(MCP23017::Port::B, val) == false) {
      //   mcp_inited_[side] = false;
      // }
    }
  }
}

void KeyScanner::init() {
  mcp_inited_.fill(false);
  mcp_init();

  sw_state_.fill(0);
  row_idx_ = 0;
}

void KeyScanner::scan(/*KeyEventBuffer *fifo*/) {
  // if (fifo->can_push() < kNumCols) {
  //   return;
  // }  // buffer vacancy is not enough
  // ElapsedTimer et;

  mcp_init();  // init mcp if timed out last time

  // increment row index
  const uint8_t curr_row = row_idx_;
  row_idx_ += 1;
  if (row_idx_ >= kNumRows) {
    row_idx_ = 0;
  }
  const uint8_t next_row = row_idx_;

  // minimize delay between read and write to allow the debounce circuit for
  // more settling time
  const uint16_t bits_L = mcp_get_col(ESide::Left);
  const uint16_t bits_R = mcp_get_col(ESide::Right);
  if (curr_row == 1) {
    // printf("%bits_R = %04x\n", bits_R);
  }
  mcp_set_row(next_row);
  {  // read col lines
    const uint8_t *key_line_L = key_matrix_L[curr_row];
    const uint8_t *key_line_R = key_matrix_R[curr_row];
    for (uint8_t col = 0; col < kNumCols; ++col) {
      update_key_state(/*fifo,*/ key_line_L[col],
                       get_col_bit(ESide::Left, bits_L, col));
      update_key_state(/*fifo,*/ key_line_R[col],
                       get_col_bit(ESide::Right, bits_R, col));
    }
  }
  {  // read rot values
    for (uint8_t rot = 0; rot < kNumRots; ++rot) {
      // update_key_state(fifo, , get_rot_bit(side, bits_L, rot));
      // update_key_state(fifo, , get_rot_bit(side, bits_R, rot));
    }
  }
  // LOG_DEBUG("elapsed = %ld us", et.getElapsedMicroSec());
}

void KeyScanner::update_key_state(/*KeyEventBuffer *fifo, */ uint8_t key,
                                  uint8_t val) {
  if (key >= 255) {  // no key
    return;
  }
  const uint8_t old_state = sw_state_[key];
  const uint8_t is_on = (val) ? ESwitchState::IsON : 0;
  // keysw was on for continuous two times
  const uint8_t is_pressed =
      ((old_state & 1) == 1 && is_on) ? ESwitchState::IsPressed : 0;
  const uint8_t new_state =
      is_pressed | ((old_state << 1) & ~ESwitchState::IsPressed) | is_on;
  sw_state_[key] = new_state;
  if (val != 0 && (old_state & 1) == 0) {
    printf("key %d on\n", key);
  }
  if (val == 0 && (old_state & 1) == 1) {
    printf("key %d off\n", key);
  }

  // push to fifo
  if ((~old_state & new_state) & ESwitchState::IsPressed) {
    // printf( "[%s] Pressed: key = %x\n", __FUNCTION__, key );
    // fifo->push_back(KeyEvent(idx, EKeyEvent::Pressed, 0/*_LL_GetTick()*/));
  } else if ((old_state & ~new_state) & ESwitchState::IsPressed) {
    // printf( "[%s] Released: key = %x\n", __FUNCTION__, key );
    // fifo->push_back(KeyEvent(idx, EKeyEvent::Released, 0/*_LL_GetTick()*/));
  }
}
