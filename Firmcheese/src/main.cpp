#define ENABLE_BLE
// #define ENABLE_USB
#define ENABLE_LED

#include <Adafruit_MCP23X17.h>
#include <Adafruit_NeoPixel.h>
#ifdef BOARD_XIAO_NRF52
#include <Adafruit_TinyUSB.h>  // for Serial
#endif
#include <Arduino.h>
#include <Wire.h>
#ifdef ENABLE_USB
#include <USB.h>
#endif

#include <array>

#include "board_led.h"
#include "key_event.h"
#include "key_scanner.h"
#include "keyb_status.h"
#include "proc_emacs.h"
#include "proc_layer.h"
#include "proc_led.h"
#include "proc_nkro.h"
#include "proc_unmod.h"
#include "ringbuf.h"

#ifdef ENABLE_USB
#include "_USBHIDKeyboard.h"
#endif

KeybStatus &GetKeybStatus() {
  static KeybStatus keyb_status;
  return keyb_status;
}

void scan_I2C() {
  Adafruit_MCP23X17 mcp;
  Serial.println("I2C Scan");
  for (int address = 1; address < 0x80; address++) {
    const bool ret = mcp.begin_I2C(address);
    if (ret) {
      Serial.printf("%02X", address);
    } else {
      Serial.print(" .");
    }
    if (address % 16 == 0) {
      Serial.print("\n");
    }
    delay(10);
  }
  Serial.print("end\n\n");
}

namespace NKeyScanTest {
Adafruit_MCP23X17 mcp;

void scan_test_setup() {
  uint16_t pin_inout = 0;
  if (false) {
    mcp.begin_I2C(0x21);  // left
    pin_inout = 0xd802;   // in = 0, out = 1
  } else {
    mcp.begin_I2C(0x20);  // rightt
    pin_inout = 0x8036;   // in = 0, out = 1
  }
  for (uint8_t pin = 0; pin < 16; ++pin) {
    mcp.pinMode(pin, (pin_inout & (1 << pin)) ? OUTPUT : INPUT);
  }
}

void scan_test_loop() {
  // key scan left
  // B4, B3, B7, B6, A1
  // constexpr uint8_t row_pins[] = {12, 11, 15, 14, 1};
  // B5, B2
  // constexpr uint8_t col_pins[] = {13, 10, 9, 8, 7, 6, 5, 4};
  // constexpr uint8_t rot_pins[] = {3, 2};

  // key scan right
  // A4, A5, A1, A2, B7
  constexpr uint8_t row_pins[] = {4, 5, 1, 2, 15};
  // A3, A6, A7, B0
  constexpr uint8_t col_pins[] = {3, 6, 7, 8, 9, 10, 11, 12};
  constexpr uint8_t rot_pins[] = {13, 14};
  for (uint8_t row = 0; row < 5; ++row) {
    // printf("row %d:", row);
    mcp.digitalWrite(row_pins[row], HIGH);
    delay(3);
    const uint16_t vals = mcp.readGPIOAB();
    for (uint8_t col = 0; col < 8; ++col) {
      if ((vals & (uint16_t(1) << col_pins[col]))) {
        printf("row %d, col %d\n", row, col);
      }
    }
    // printf("\n");
    mcp.digitalWrite(row_pins[row], LOW);
  }
  const uint16_t vals = mcp.readGPIOAB();
  for (uint8_t rot = 0; rot < 2; ++rot) {
    if ((vals & (uint16_t(1) << rot_pins[rot]))) {
      printf("rot %d\n", rot);
    }
  }
}
}  // namespace NKeyScanTest

KeybStatus g_keyb_status;
KeyScanner scanner;

#ifdef ENABLE_LED
ProcLed proc_led;
#endif
KeyProcLayer proc_layer;
KeyProcUnmod proc_unmod1;
KeyProcEmacs proc_emacs;
KeyProcUnmod proc_unmod2;
KeyProcNkro proc_nkro;

#ifdef BOARD_XIAO_NRF52
BleConnectorNRF52 ble_kbrd;
BoardLED_Xiao brd_led;
#endif
#ifdef BOARD_M5ATOM
// BleKeyboard ble_kbrd("Mozza62 keyb");
BoardLED_M5Atom brd_led;
#endif
#if defined(BOARD_XIAO_ESP32) || defined(BOARD_XIAO_ESP32_NIMBLE)
BoardLED_XiaoEsp32 brd_led;
#ifdef ENABLE_BLE
BleConnectorESP32 ble_kbrd;
#endif
#ifdef ENABLE_USB
USBHIDKeyboard Keyboard;
#endif
#endif

void setup() {
  Serial.begin(115200);
  // while (!Serial) delay(10); // wait for serial monitor...

#ifdef BOARD_M5ATOM
  Wire.begin(25, 21, 100000UL);
#endif

  scan_I2C();

  g_config_data.init();
  brd_led.begin();
  scanner.init();
#ifdef ENABLE_LED
  proc_led.init();
#endif
  proc_layer.init();
  proc_unmod1.init();
  proc_emacs.init();
  proc_unmod2.init();
  proc_nkro.init();
  // NScanTest::scan_test_setup();

#ifdef ENABLE_USB
  USB.begin();
  Keyboard.begin();
#endif
#ifdef ENABLE_BLE
  ble_kbrd.begin();
#endif
}

std::array<KeyEvent, 12 * 2> keva_input;
std::array<KeyEvent, 12 * 2> keva_layer;
std::array<KeyEvent, 12 * 2> keva_unmod1;
std::array<KeyEvent, 12 * 2> keva_emacs;
std::array<KeyEvent, 12 * 2> keva_unmod2;

KeyEventBuffer kevb_input(keva_input.data(), keva_input.size());
KeyEventBuffer kevb_layer(keva_layer.data(), keva_layer.size());
KeyEventBuffer kevb_unmod1(keva_unmod1.data(), keva_unmod1.size());
KeyEventBuffer kevb_emacs(keva_emacs.data(), keva_emacs.size());
KeyEventBuffer kevb_unmod2(keva_unmod2.data(), keva_unmod2.size());

KeyboardReport kbrd_report = {0};

void loop() {
  // return;
  static uint16_t cnt = 0;
  cnt += 1;
#ifdef ENABLE_BLE
  {  // ble
    const bool ble_conn = GetKeybStatus().GetStatus(EKeybStatusBit::Ble);
    if (ble_kbrd.isConnected()) {
      if (ble_conn == false) {
        GetKeybStatus().SetStatus(EKeybStatusBit::Ble, true);
        LOG_INFO("BLE: Connected");
      }
    } else {
      if (ble_conn) {
        GetKeybStatus().SetStatus(EKeybStatusBit::Ble, false);
        LOG_INFO("BLE: Disconnected");
      }
    }
  }
#endif
  if (true) {  // board LED
    static bool last_blink = false;
    static status_t last_status = -1;
    const bool curr_blink = ((millis() & (1 << 9)) == 0);
    const KeybStatus curr_status = GetKeybStatus();
    if (last_status != curr_status.GetAllStatus() || last_blink != curr_blink) {
      last_status = curr_status.GetAllStatus();
      last_blink = curr_blink;
      brd_led.update(curr_blink, curr_status);
    }
  }
  if (true) {  // key scan
    // NScanTest::scan_test_loop();
    scanner.scan(&kevb_input);
#ifdef ENABLE_LED
    proc_led.process(scanner.getSwitchStateData());
#endif
  }

  KeyEventBuffer *ptr_kevb_in = nullptr;
  KeyEventBuffer *ptr_kevb_out = &kevb_input;

  // clang-format off
#define _set_kevb(kevb)  ptr_kevb_in = ptr_kevb_out;  ptr_kevb_out = &(kevb)
  _set_kevb(kevb_layer); while (proc_layer.process(*ptr_kevb_in, *ptr_kevb_out));
  _set_kevb(kevb_unmod1); while (proc_unmod1.process(*ptr_kevb_in, *ptr_kevb_out));
  _set_kevb(kevb_emacs); while (proc_emacs.process(*ptr_kevb_in, *ptr_kevb_out));
  _set_kevb(kevb_unmod2); while (proc_unmod2.process(*ptr_kevb_in, *ptr_kevb_out));
#undef _set_kevb
  // clang-format on

  // send one event every 8ms
  if (ptr_kevb_out->can_pop()) {
    const auto kev = ptr_kevb_out->pop_front();
    if (kev.event_ == EKeyEvent::Pressed) {
      LOG_DUMP("%d, %d, %u", kev.code_, kev.event_, kev.tick_ms_);
// LOG_INFO("key code = %d, 0x%04x", kev.code_, kev.code_);
#ifdef ENABLE_BLE
      if (kev.code_ == KC_ENTER) {
        ble_kbrd.enumBonds();
      }
      if (kev.code_ == KC_DELETE) {
        ble_kbrd.deleteAllBonds();
      }
#endif
    }
    kbrd_report = proc_nkro.send_key(kev);

    if (GetKeybStatus().GetStatus(EKeybStatusBit::Ble)) {
#ifdef ENABLE_BLE
      ble_kbrd.sendKeyboardReport(kbrd_report);
#endif
    } else {
#ifdef ENABLE_USB
      Keyboard.sendReport(reinterpret_cast<KeyReport *>(&kbrd_report));
#endif
    }
  }
  delay(1);
}
