#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_BME280.h>
#include <Adafruit_MCP3008.h>
#include <AS5600.h>
#include "driver/twai.h"
#include "pinmap.h"

// ---------- Sensors ----------
Adafruit_BME280 bme;         // I2C BME280
Adafruit_MCP3008 mcp;        // SPI MCP3008 (anemometer on CH0)
AS5600 as5600;               // I2C AS5600 (wind vane)

// ---------- CAN (TWAI) ----------
static bool can_ok = false;

static void can_init() {
  twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(
      (gpio_num_t)CAN_TX, (gpio_num_t)CAN_RX, TWAI_MODE_NORMAL);
  twai_timing_config_t  t_config = TWAI_TIMING_CONFIG_500KBITS();
  twai_filter_config_t  f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g_config, &t_config, &f_config) == ESP_OK &&
      twai_start() == ESP_OK) {
    can_ok = true;
  }
}

static inline void put_u16_be(uint8_t* p, uint16_t v) {
  p[0] = (v >> 8) & 0xFF; p[1] = v & 0xFF;
}

static void can_send_0x10(uint16_t t10, uint16_t h10, uint16_t p10) {
  if (!can_ok) return;
  twai_message_t msg = {};
  msg.identifier = 0x10;
  msg.flags = TWAI_MSG_FLAG_NONE;
  msg.data_length_code = 6;
  put_u16_be(&msg.data[0], t10);
  put_u16_be(&msg.data[2], h10);
  put_u16_be(&msg.data[4], p10);
  twai_transmit(&msg, pdMS_TO_TICKS(10));
}

static void can_send_0x11(uint16_t angle10, uint16_t wind_raw) {
  if (!can_ok) return;
  twai_message_t msg = {};
  msg.identifier = 0x11;
  msg.flags = TWAI_MSG_FLAG_NONE;
  msg.data_length_code = 4;
  put_u16_be(&msg.data[0], angle10);
  put_u16_be(&msg.data[2], wind_raw);
  twai_transmit(&msg, pdMS_TO_TICKS(10));
}

void setup() {
  Serial.begin(115200);
  delay(200);

  // I2C
  Wire.begin(I2C_SDA, I2C_SCL);

  // BME280 (try 0x76 then 0x77)
  bool bme_ok = bme.begin(0x76);
  if (!bme_ok) bme_ok = bme.begin(0x77);
  if (!bme_ok) Serial.println(F("BME280 init FAILED"));

  // MCP3008 (SPI)
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  if (!mcp.begin(SPI, MCP_CS)) {
    Serial.println(F("MCP3008 init FAILED"));
  }

  // AS5600
  as5600.begin(Wire);
  if (!as5600.isConnected()) {
    Serial.println(F("AS5600 not detected"));
  }

  // CAN
  can_init();
  if (!can_ok) Serial.println(F("CAN init FAILED"));
}

void loop() {
  static uint32_t t_last = 0, w_last = 0;
  uint32_t now = millis();

  // ---- Atmos block → 0x10 every 500 ms ----
  if (now - t_last >= 500) {
    t_last = now;
    float tC = bme.readTemperature();           // °C
    float h  = bme.readHumidity();              // %
    float pH = bme.readPressure() / 100.0f;     // hPa

    uint16_t t10 = (tC  < 0) ? 0 : (uint16_t)roundf(tC * 10.0f);
    uint16_t h10 = (h   < 0) ? 0 : (uint16_t)roundf(h  * 10.0f);
    uint16_t p10 = (pH  < 0) ? 0 : (uint16_t)roundf(pH * 10.0f);

    can_send_0x10(t10, h10, p10);
  }

  // ---- Wind block → 0x11 every 200 ms ----
  if (now - w_last >= 200) {
    w_last = now;

    // AS5600 raw angle 0..4095 -> degrees
    uint16_t raw = as5600.readAngle();                 // 0..4095
    float deg = (raw * 360.0f) / 4096.0f;              // 0..360
    if (deg >= 360.0f) deg -= 360.0f;
    uint16_t angle10 = (uint16_t)roundf(deg * 10.0f);  // Pi divides by 10.0

    // Anemometer raw via MCP3008 CH0 → 0..1023
    uint16_t wind_raw = (uint16_t)mcp.readADC(ANEMO_CH);

    can_send_0x11(angle10, wind_raw);
  }
}
