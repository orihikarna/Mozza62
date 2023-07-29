#define FASTLED_ESP32_I2S true
#include <M5Atom.h>
//#include <FastLED.h>
#include <Adafruit_MCP23X17.h>
//#include "key_scanner.hpp"

Adafruit_MCP23X17 mcp;

// pins
#define BTN_pin 39
#define LED_pin 27
#define LED_Left_pin 19
#define ENC_A_pin 21
#define ENC_B_pin 25

// constants
#define NUM_LEDS 25
#define NUM_LEFT_LEDS 31

// static variable
CRGB s_leds[NUM_LEDS];
CRGB s_leds_left[NUM_LEFT_LEDS];

// encoder counts
int s_last_enc_cnt = 0;
int s_enc_cnt = NUM_LEDS / 2;
byte s_enc_val = 0;
byte s_enc_dir = 0;

// functions
void set_led(CRGB clr) {
  for (int8_t i = 0; i < NUM_LEDS; ++i) {
    s_leds[i] = clr;
  }
  //FastLED.show();
}

void set_left_led(CRGB clr) {
  for (int8_t i = 0; i < NUM_LEFT_LEDS; ++i) {
    s_leds_left[i] = clr;
  }
  //FastLED.show();
}

void update_enc_cnt() {
  const byte curr_val = digitalRead(ENC_A_pin) | (digitalRead(ENC_B_pin) << 1);
  const byte prev_val = s_enc_val;
  byte dir = s_enc_dir;

  // positive rotation: 0 -> 1 -> 3 -> 2
  // negative rotation: 0 -> 2 -> 3 -> 1

  if (curr_val != prev_val) {
    if (dir == 0) {                          // no direction
      if (curr_val == 1 || curr_val == 2) {  // positive or negtive begin
        dir = curr_val;
      }
    } else if (curr_val == 0) {
      if (dir == 1 && prev_val == 2) {  // positive end
        s_enc_cnt++;
        if (s_enc_cnt > NUM_LEDS) {
          s_enc_cnt = NUM_LEDS;
        }
      } else if (dir == 2 && prev_val == 1) {  // negative end
        s_enc_cnt--;
        if (s_enc_cnt < -NUM_LEDS) {
          s_enc_cnt = -NUM_LEDS;
        }
      }
      dir = 0;  // reset direction
      if (true) {
        for (int8_t n = 0; n < NUM_LEDS; ++n) {
          s_leds[n] = CRGB((s_enc_cnt > n) ? 20 : 0, (s_enc_cnt < -n) ? 20 : 0, 0);
        }
        FastLED.show();
      }
    }
    s_enc_dir = dir;
    s_enc_val = curr_val;

    //Serial.println( curr_val );
  }
}

void scan_I2C() {
  Serial.println("I2C Scan");
  for (int address = 1; address < 0x80; address++) {
    //Wire.beginTransmission(address);
    //int error = Wire.endTransmission();
    const int error = mcp.begin_I2C(address);
    if (error != 0) {
      Serial.printf("%02X", address);
    } else {
      Serial.print(" .");
    }

    if (address % 16 == 0) {
      Serial.print("\n");
    }
    delay(20);
  }
  Serial.print("end\n\n");
}

void setup() {
  // put your setup code here, to run once:
  M5.begin(true, true, true);  // Init Atom-Matrix( Initialize serial port, I2C enable, LED matrix )

  Serial.begin(115200);
  // Wire.begin( 25, 21 );

  FastLED.addLeds<WS2812B, LED_Left_pin, GRB>(s_leds_left, NUM_LEFT_LEDS);
  FastLED.addLeds<WS2812B, LED_pin, GRB>(s_leds, NUM_LEDS);
  FastLED.setBrightness(20);
  //set_led( CRGB( 0, 20, 0 ) );

  pinMode(BTN_pin, INPUT);
  //pinMode( ENC_A_pin, INPUT_PULLUP );
  //pinMode( ENC_B_pin, INPUT_PULLUP );

  //attachInterrupt( ENC_A_pin, update_enc_cnt, CHANGE );
  //attachInterrupt( ENC_B_pin, update_enc_cnt, CHANGE );

  //scan_I2C();

  mcp.begin_I2C(0x21);
  // in = 0, out = 1
  constexpr uint16_t pin_inout = 0xd802;
  for (uint8_t pin = 0; pin < 16; ++pin) {
    mcp.pinMode(pin, (pin_inout & (1 << pin)) ? OUTPUT : INPUT);
  }
}

void loop() {
  // put your main code here, to run repeatedly:
  if (false) {
    update_enc_cnt();
    delay(3);
  }
  static uint16_t i = 0;
  i = (i+1) & 255;
  //for (uint16_t i = 0; i < 256; ++i) {
  {
    //set_led( CRGB( 0, i, i ) );
    //set_left_led( CRGB( 0, i, i ) );
    //set_led(CHSV(i, 255, 255));
    //set_left_led(CHSV(i, 255, 255));
    for (uint16_t n = 0; n < NUM_LEDS; ++n) {
      s_leds[n] = CHSV((i + 8 * n) & 255, 255, 255);
    }
    for (uint16_t n = 0; n < NUM_LEFT_LEDS; ++n) {
      s_leds_left[n] = CHSV((i + 4 * n) & 255, 255, 255);
    }
    FastLED.show();
    delay(10);
  }
  if (true) {
    // B4, B3, B7, B6, A1
    constexpr uint8_t row_pins[] = {12, 11, 15, 14, 1};
    // B5, B2
    constexpr uint8_t col_pins[] = {13, 10, 9, 8, 7, 6, 5, 4};
    constexpr uint8_t rot_pins[] = {3, 2};
    for (uint8_t row = 0; row < 5; ++row) {
      // printf("row %d:", row);
      mcp.digitalWrite(row_pins[row], HIGH);
      delay(2);
      const uint16_t vals = mcp.readGPIOAB();
      for (uint8_t col = 0; col < 8; ++col) {
        if ((vals & (uint16_t(1) << col_pins[col]))) {
        //if (mcp.digitalRead(col_pins[col]) == LOW) {
          // printf(" col%d, ", col);
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
}
