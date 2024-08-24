#pragma once

#include <cstdint>

#include "log.h"

template <typename T>
class RingBuffer {
 public:
  using size_t = uint8_t;
  using ssize_t = int8_t;

 private:
  T* buff_;
  size_t size_;
  size_t read_idx_ = 0;
  size_t write_idx_ = 0;
  size_t max_used_size_ = 0;

 public:
  RingBuffer(T* buff, size_t size) : buff_(buff), size_(size) {}

  size_t getMaxUsedSize() const { return max_used_size_; }

  void push_back(const T& v) {
    if (can_push() == 0) LOG_ERROR("buffer is FULL!");
    if (false) {
      ssize_t used = write_idx_ - read_idx_;
      if (used < 0) used += size_;
      if (max_used_size_ < used) {
        max_used_size_ = used;
      }
    }
    buff_[write_idx_] = v;
    write_idx_ = incr(write_idx_);
  }

  T pop_front() {
    if (can_pop() == 0) LOG_ERROR("buffer is EMPTY!");
    const T ret = buff_[read_idx_];
    read_idx_ = incr(read_idx_);
    return ret;
  }

  size_t can_pop() const {
    ssize_t avail = write_idx_ - read_idx_;
    if (avail < 0) {
      avail += size_;
    }
    return avail;
  }

  size_t can_push() const {
    const size_t write_next = incr(write_idx_);
    ssize_t vacant = read_idx_ - write_next;
    if (vacant < 0) {
      vacant += size_;
    }
    return vacant;
  }

 private:
  inline size_t incr(size_t idx) const {
    idx += 1;
    if (idx == size_) {
      idx = 0;
    }
    return idx;
  }
};
