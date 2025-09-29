#pragma once

#include <array>
#include <cstdint>

#include "key_event.h"
#include "key_switch.h"
#include "keymaps.h"
#include "qmk/keycode_jp.h"

class KeyProcEmacs {
 private:
  struct SModTapHold {
    uint8_t modcode;
    uint8_t state;
    uint16_t time;
  };

 public:
  KeyProcEmacs();
  void init();
  bool process(KeyEventBuffer& kevb_in, KeyEventBuffer& kevb_out);

 private:
  KeyEventBuffer* keyb_out_;
  int16_t ev_time_;

 private:
  uint8_t map_table_index;
  uint8_t next_map_table_index_;
  uint8_t pressed_mods_;
  uint8_t pressed_keycode_;
  uint8_t registered_mods_;
  uint8_t mapped_mods_;
  uint8_t mapped_keycode_;
  std::array<SModTapHold, 4> mod_taps_;

 private:  // utilities
  void register_code(keycode_t kc);
  void unregister_code(keycode_t kc);
  inline void tap_code(keycode_t kc) {
    register_code(kc);
    unregister_code(kc);
  }

  void register_mods(uint8_t mods);
  void unregister_mods(uint8_t mods);
  void swap_mods(uint8_t new_mods, uint8_t old_mods);

 private:  // map tables
  void on_enter_map_table(uint8_t table_index);
  void on_search_map_table(uint8_t table_index, uint8_t entry_index);

 private:  // key mapping
  bool match_mods(uint8_t pressed, uint8_t mods, uint8_t* any_mods);
  void map_key(uint8_t mods, uint8_t keycode);
  bool unmap_key();

 private:  // mod tap
  void modtap_on_press(const KeyEvent& kev);
  void modtap_on_release(const KeyEvent& kev);
  void modtap_hold_mods_if_pressed(uint8_t mods_mask);
  static inline bool modtap_is_tap(const SModTapHold* tap, const KeyEvent& kev) {
    const int16_t tdiff = kev.tick_ms_ - tap->time;
    return (10 <= tdiff && tdiff < 300);
  }
};
