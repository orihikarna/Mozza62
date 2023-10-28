#pragma once

#include <cstdint>

#include "log.h"

template <typename T>
class RingBuffer {
 private:
  T* m_buff = nullptr;
  uint8_t size_ = 0;
  uint8_t read_idx_ = 0;
  uint8_t write_idx_ = 0;
  uint8_t max_used_size_ = 0;

 public:
  RingBuffer(T* buff, uint8_t size)
      : m_buff(buff),
        size_(size){
            // assert( size < 128 );
        };

  uint8_t getMaxUsedSize() const { return max_used_size_; }

  void push_back(const T& v) {
    if (can_push() == 0) LOG_ERROR("buffer is FULL!");
    if (false) {
      int8_t used = write_idx_ - read_idx_;
      if (used < 0) used += size_;
      if (max_used_size_ < used) {
        max_used_size_ = used;
      }
    }
    m_buff[write_idx_] = v;
    write_idx_ = incr(write_idx_);
  }

  T pop_front() {
    if (can_pop() == 0) LOG_ERROR("buffer is EMPTY!");
    const T ret = m_buff[read_idx_];
    read_idx_ = incr(read_idx_);
    return ret;
  }

  uint8_t can_pop() const {
    int8_t avail = write_idx_ - read_idx_;
    if (avail < 0) {
      avail += size_;
    }
    return avail;
  }

  uint8_t can_push() const {
    const uint8_t write_next = incr(write_idx_);
    int8_t vacant = read_idx_ - write_next;
    if (vacant < 0) {
      vacant += size_;
    }
    return vacant;
  }

 private:
  inline uint8_t incr(uint8_t idx) const {
    idx += 1;
    if (idx == size_) {
      idx = 0;
    }
    return idx;
  }
};
