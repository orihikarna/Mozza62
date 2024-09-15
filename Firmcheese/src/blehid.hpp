#pragma once

#include <qmk/keycode.h>

#define KBRD_NAME "Mozza62 keyb"

struct KeyboardReport {
  uint8_t modifiers;
  uint8_t reserved;
  uint8_t keys[6];
};

#ifdef BOARD_M5ATOM
#include <BleKeyboard.h>

class BleConnectorESP32 {
 private:
  BleKeyboard ble_kbrd_;

 public:
  BleConnectorESP32() : ble_kbrd_(KBRD_NAME) {};

  void begin() { ble_kbrd_.begin(); };
  bool isConnected() const { return ble_kbrd_.isConnected(); }
};
#endif

#ifdef BOARD_XIAO_BLE
#include <bluefruit.h>

class BleConnectorNRF {
 private:
  BLEDis bledis_;
  BLEHidAdafruit blehid_;

 public:
  void begin() {
    Bluefruit.begin();
    Bluefruit.setTxPower(4);  // Check bluefruit.h for supported values

    // Configure and Start Device Information Service
    bledis_.setManufacturer("Adafruit Industries");
    bledis_.setModel(KBRD_NAME);
    bledis_.begin();

    /* Start BLE HID
     * Note: Apple requires BLE device must have min connection interval >= 20m
     * ( The smaller the connection interval the faster we could send data).
     * However for HID and MIDI device, Apple could accept min connection interval
     * up to 11.25 ms. Therefore BLEHidAdafruit::begin() will try to set the min and max
     * connection interval to 11.25  ms and 15 ms respectively for best performance.
     */
    blehid_.begin();

    // Set callback for set LED from central
    // blehid_.setKeyboardLedCallback(set_keyboard_led);

    /* Set connection interval (min, max) to your perferred value.
     * Note: It is already set by BLEHidAdafruit::begin() to 11.25ms - 15ms
     * min = 9*1.25=11.25 ms, max = 12*1.25= 15 ms
     */
    /* Bluefruit.Periph.setConnInterval(9, 12); */

    // Set up and start advertising
    start_adv();
  }

  void start_adv(void) {
    // Advertising packet
    Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
    Bluefruit.Advertising.addTxPower();
    Bluefruit.Advertising.addAppearance(BLE_APPEARANCE_HID_KEYBOARD);

    // Include BLE HID service
    Bluefruit.Advertising.addService(blehid_);

    // There is enough room for the dev name in the advertising packet
    Bluefruit.Advertising.addName();

    /* Start Advertising
     * - Enable auto advertising if disconnected
     * - Interval:  fast mode = 20 ms, slow mode = 152.5 ms
     * - Timeout for fast mode is 30 seconds
     * - Start(timeout) with timeout = 0 will advertise forever (until connected)
     *
     * For recommended advertising interval
     * https://developer.apple.com/library/content/qa/qa1931/_index.html
     */
    Bluefruit.Advertising.restartOnDisconnect(true);
    Bluefruit.Advertising.setInterval(32, 244);  // in unit of 0.625 ms
    Bluefruit.Advertising.setFastTimeout(30);    // number of seconds in fast mode
    Bluefruit.Advertising.start(0);              // 0 = Don't stop advertising after n seconds
  }

  bool isConnected() const { return Bluefruit.connected(Bluefruit.connHandle()); }

  bool sendKeyboardReport(const KeyboardReport& kbrd_report) {
    hid_keyboard_report_t report = *reinterpret_cast<const hid_keyboard_report_t*>(&kbrd_report);
    return blehid_.keyboardReport(&report);
  }
};

#endif
