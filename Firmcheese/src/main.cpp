#include <Adafruit_MCP23X17.h>
#include <Adafruit_NeoPixel.h>
#ifdef BOARD_XIAO_BLE
#include <Adafruit_TinyUSB.h>  // for Serial
#endif
#include <Arduino.h>
#include <Wire.h>

#include <array>

#include "board_led.hpp"
#include "key_event.hpp"
#include "key_scanner.hpp"
#include "keyb_status.hpp"
#include "proc_emacs.hpp"
#include "proc_layer.hpp"
#include "proc_led.hpp"
#include "proc_nkro.hpp"
#include "proc_unmod.hpp"
#include "ringbuf.hpp"

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

ProcLed proc_led;
KeyProcLayer proc_layer;
KeyProcEmacs proc_emacs;
KeyProcUnmod proc_unmod;
KeyProcNkro proc_nkro;

#ifdef BOARD_XIAO_BLE
BleConnectorNRF ble_kbrd;
BoardLED_Xiao brd_led;
#endif
#ifdef BOARD_M5ATOM
// BleKeyboard ble_kbrd("Mozza62 keyb");
BoardLED_M5Atom brd_led;
#endif
#ifdef BOARD_XIAO_ESP32
BleConnectorESP32 ble_kbrd;
BoardLED_XiaoEsp32 brd_led;
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
  proc_led.init();
  proc_layer.init();
  proc_emacs.init();
  proc_unmod.init();
  proc_nkro.init();
  // NScanTest::scan_test_setup();

  ble_kbrd.begin();
}

std::array<KeyEvent, 12 * 2> keva_input;
std::array<KeyEvent, 12 * 2> keva_layer;
std::array<KeyEvent, 12 * 2> keva_emacs;
std::array<KeyEvent, 6 * 2> keva_unmod;

KeyEventBuffer kevb_input(keva_input.data(), keva_input.size());
KeyEventBuffer kevb_layer(keva_layer.data(), keva_layer.size());
KeyEventBuffer kevb_emacs(keva_emacs.data(), keva_emacs.size());
KeyEventBuffer kevb_unmod(keva_unmod.data(), keva_unmod.size());

KeyboardReport kbrd_report = {0};

void loop() {
  // return;
  static uint16_t cnt = 0;
  cnt += 1;
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
    proc_led.process(scanner.getSwitchStateData());
  }

  KeyEventBuffer *ptr_kevb_in = nullptr;
  KeyEventBuffer *ptr_kevb_out = &kevb_input;

  // clang-format off
#define _set_kevb(kevb)  ptr_kevb_in = ptr_kevb_out;  ptr_kevb_out = &(kevb)
  _set_kevb(kevb_layer); while (proc_layer.process(*ptr_kevb_in, *ptr_kevb_out));
  _set_kevb(kevb_emacs); while (proc_emacs.process(*ptr_kevb_in, *ptr_kevb_out));
  _set_kevb(kevb_unmod); while (proc_unmod.process(*ptr_kevb_in, *ptr_kevb_out));
#undef _set_kevb
  // clang-format on

  // send one event every 8ms
  if (ptr_kevb_out->can_pop()) {
    const auto kev = ptr_kevb_out->pop_front();
    if (kev.event_ == EKeyEvent::Pressed) {
      LOG_DUMP("%d, %d, %u", kev.code_, kev.event_, kev.tick_ms_);
    }
    kbrd_report = proc_nkro.send_key(kev);

    if (GetKeybStatus().GetStatus(EKeybStatusBit::Ble)) {
      ble_kbrd.sendKeyboardReport(kbrd_report);
    }
  }
  delay(1);
}
