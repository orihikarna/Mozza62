#pragma once

#include <cstdint>

using status_t = uint8_t;

enum class EKeybStatusBit : status_t {
  Ble,
  Left,
  Right,
  Emacs,
};

class KeybStatus {
 private:
  status_t status_ = 0;

 public:
  status_t GetAllStatus() const { return status_; }
  bool GetStatus(EKeybStatusBit bit) const {
    return (status_ & (1 << static_cast<status_t>(bit))) != 0;
  }
  void SetStatus(EKeybStatusBit bit, bool status) {
    const status_t mask = 1 << static_cast<status_t>(bit);
    if (status) {
      status_ |= mask;
    } else {
      status_ &= ~mask;
    }
  }
};

extern KeybStatus& GetKeybStatus();
