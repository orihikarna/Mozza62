#pragma once

#include <log.h>
#include <qmk/keycode.h>

#define KBRD_NAME "Mozza62 keyb"
#define MANUFACTURER "orihikarna"

struct KeyboardReport {
  uint8_t modifiers;
  uint8_t reserved;
  uint8_t keys[6];
};

#if defined(BOARD_M5ATOM) || defined(BOARD_XIAO_ESP32) || defined(BOARD_XIAO_ESP32_NIMBLE)
#include <BleKeyboard.h>

#if defined(BOARD_XIAO_ESP32)
#include <NimBLEDevice.h>

class MozzaBleKeyboard : public BleKeyboard {
 public:
  MozzaBleKeyboard() : BleKeyboard(KBRD_NAME, MANUFACTURER) {}

#ifdef USE_NIMBLE
  uint32_t onPassKeyRequest() override {
    LOG_INFO("onPassKeyRequest");
    return 6262;
  }
  bool onConfirmPIN(uint32_t pin) override {
    LOG_INFO("onConfirmPIN, pin = %d", pin);
    return true;
  }
  void onAuthenticationComplete(ble_gap_conn_desc* desc) override {
    LOG_INFO("onAuthenticationComplete, addr = %s", desc->peer_id_addr.val[0]);
  }
  void onConnect(NimBLEServer* pServer) override {
    BleKeyboard::onConnect(pServer);
    NimBLEDevice::stopAdvertising();
    LOG_INFO("onConnect");
  }
  void onDisconnect(NimBLEServer* pServer) override {
    BleKeyboard::onDisconnect(pServer);
    NimBLEDevice::startAdvertising();
    LOG_INFO("onDisconnect");
  }
#endif
};

class BleConnectorESP32 {
 private:
  MozzaBleKeyboard ble_kbrd_;

 public:
  void begin() {
    LOG_INFO("BleConnectorESP32::begin");
    ble_kbrd_.begin();
#ifdef USE_NIMBLE
    // NimBLEDevice::setSecurityIOCap(BLE_HS_IO_KEYBOARD_ONLY);
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_ONLY);
#endif
  };
  bool isConnected() { return ble_kbrd_.isConnected(); }

  bool sendKeyboardReport(const KeyboardReport& kbrd_report) {
    KeyReport report = *reinterpret_cast<const KeyReport*>(&kbrd_report);
    ble_kbrd_.sendReport(&report);
    return true;
  }

#ifdef USE_NIMBLE
  void enumBonds() {
    LOG_INFO("passkey = %d", NimBLEDevice::getSecurityPasskey());

    const size_t num_white = NimBLEDevice::getWhiteListCount();
    LOG_INFO("ble num white list = %d", num_white);
    for (int i = 0; i < num_white; ++i) {
      const NimBLEAddress addr = NimBLEDevice::getWhiteListAddress(i);
      LOG_INFO("ble white %d, addr = %s", i, addr.toString().c_str());
    }

    const int num_bonds = NimBLEDevice::getNumBonds();
    LOG_INFO("ble num bonds = %d", num_bonds);
    for (int i = 0; i < num_bonds; ++i) {
      const NimBLEAddress addr = NimBLEDevice::getBondedAddress(i);
      LOG_INFO("ble bond %d, addr = %s", i, addr.toString().c_str());
    }
  }

  void deleteAllBonds() {
    LOG_INFO("ble delete all bonds");
    NimBLEDevice::deleteAllBonds();
  }
#endif
};

#elif defined(BOARD_XIAO_ESP32_NIMBLE)
#include <NimBLEDevice.h>

class MozzaBleKeyboard : public BleKeyboard {
 public:
  MozzaBleKeyboard() : BleKeyboard(KBRD_NAME, MANUFACTURER) {}

  uint32_t onPassKeyDisplay() override {
    LOG_INFO("onPassKeyDisplay");
    return 6262;
  }
  void onConfirmPassKey(NimBLEConnInfo& connInfo, uint32_t pin) override {
    LOG_INFO("onConfirmPassKey, pin = %d", pin);
  }
  void onAuthenticationComplete(NimBLEConnInfo& connInfo) override {
    LOG_INFO("onAuthenticationComplete, addr = %s", connInfo.getAddress().toString().c_str());
  }
  void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override {
    BleKeyboard::onConnect(pServer, connInfo);
    NimBLEDevice::stopAdvertising();
    LOG_INFO("onConnect");
  }
  void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override {
    BleKeyboard::onDisconnect(pServer, connInfo, reason);
    NimBLEDevice::startAdvertising();
    LOG_INFO("onDisconnect, reason = %d, 0x%04x", reason, reason);
  }
};

class BleConnectorESP32 {
 private:
  MozzaBleKeyboard ble_kbrd_;

 public:
  void begin() {
    LOG_INFO("BleConnectorESP32::begin");
    ble_kbrd_.begin();
    // BLEDevice::setSecurityAuth(true, false, false);
    // NimBLEDevice::setSecurityIOCap(BLE_HS_IO_KEYBOARD_ONLY);
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_ONLY);
    // NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_YESNO);
    // NimBLEDevice::setSecurityInitKey(BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID);
    // NimBLEDevice::setSecurityRespKey(BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID);
  };
  bool isConnected() { return ble_kbrd_.isConnected(); }

  bool sendKeyboardReport(const KeyboardReport& kbrd_report) {
    KeyReport report = *reinterpret_cast<const KeyReport*>(&kbrd_report);
    ble_kbrd_.sendReport(&report);
    return true;
  }

  void enumBonds() {
    LOG_INFO("passkey = %d", NimBLEDevice::getSecurityPasskey());

    const size_t num_white = NimBLEDevice::getWhiteListCount();
    LOG_INFO("ble num white list = %d", num_white);
    for (int i = 0; i < num_white; ++i) {
      const NimBLEAddress addr = NimBLEDevice::getWhiteListAddress(i);
      LOG_INFO("ble white %d, addr = %s", i, addr.toString().c_str());
    }

    const int num_bonds = NimBLEDevice::getNumBonds();
    LOG_INFO("ble num bonds = %d", num_bonds);
    for (int i = 0; i < num_bonds; ++i) {
      const NimBLEAddress addr = NimBLEDevice::getBondedAddress(i);
      LOG_INFO("ble bond %d, addr = %s", i, addr.toString().c_str());
    }
  }

  void deleteAllBonds() {
    LOG_INFO("ble delete all bonds");
    NimBLEDevice::deleteAllBonds();
  }
};
#endif
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
    bledis_.setModel("Bluefruit Feather 52");
    bledis_.begin();

    /* Start BLE HID
     * Note: Apple requires BLE device must have min connection interval >= 20m
     * ( The smaller the connection interval the faster we could send data).
     * However for HID and MIDI device, Apple could accept min connection
     * interval up to 11.25 ms. Therefore BLEHidAdafruit::begin() will try to
     * set the min and max connection interval to 11.25  ms and 15 ms
     * respectively for best performance.
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
    // Bluefruit.Advertising.addName();
    {
      const char name[] = "Mozz62 kbrd";
      const uint8_t len = sizeof(name);
      Bluefruit.Advertising.addData(BLE_GAP_AD_TYPE_COMPLETE_LOCAL_NAME, name, len);
    }

    /* Start Advertising
     * - Enable auto advertising if disconnected
     * - Interval:  fast mode = 20 ms, slow mode = 152.5 ms
     * - Timeout for fast mode is 30 seconds
     * - Start(timeout) with timeout = 0 will advertise forever (until
     * connected)
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
